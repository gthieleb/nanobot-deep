"""Nanobot-specific agent factory using deepagents + CLI utilities."""

from __future__ import annotations

import asyncio
import time
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from loguru import logger

from nanobot_deep.config.deepagents_cli import apply_deepagents_config_path

if TYPE_CHECKING:
    from nanobot.config.schema import Config
    from nanobot_deep.config.schema import DeepAgentsConfig

try:
    from deepagents import create_deep_agent
    from deepagents.backends import FilesystemBackend
    from deepagents.backends.local_shell import LocalShellBackend
    from deepagents.middleware.subagents import GENERAL_PURPOSE_SUBAGENT

    DEEPAGENTS_AVAILABLE = True
except ImportError:
    DEEPAGENTS_AVAILABLE = False
    create_deep_agent = None

try:
    from deepagents_cli.config import ModelConfigError, create_model
    from deepagents_cli.mcp_tools import resolve_and_load_mcp_tools
    from deepagents_cli.project_utils import ProjectContext

    CLI_AVAILABLE = True
except ImportError:
    CLI_AVAILABLE = False
    ModelConfigError = None
    create_model = None
    resolve_and_load_mcp_tools = None
    ProjectContext = None


def create_nanobot_agent(
    workspace: Path,
    nanobot_config: "Config",
    deepagents_config: "DeepAgentsConfig",
    checkpointer: Any | None = None,
    mcp_config_path: str | None = None,
    no_mcp: bool = False,
    custom_tools: list[Any] | None = None,
    custom_middleware: list[Any] | None = None,
) -> tuple[Any, Any, dict[str, Any]]:
    """Create nanobot agent using deepagents + CLI utilities.

    This is a sync wrapper that runs the async agent creation.
    If an event loop is already running, it creates a new thread to run the async code.

    Uses:
    - deepagents_cli for model resolution and MCP loading
    - deepagents.create_deep_agent() for agent creation

    Args:
        workspace: Workspace directory
        nanobot_config: nanobot configuration
        deepagents_config: DeepAgents configuration
        checkpointer: Session checkpointer
        mcp_config_path: Optional MCP config path
        no_mcp: Disable MCP loading
        custom_tools: Additional tools to add
        custom_middleware: Additional middleware

    Returns:
        Tuple of (agent, backend, mcp_info)
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is not None:
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(
                asyncio.run,
                create_nanobot_agent_async(
                    workspace=workspace,
                    nanobot_config=nanobot_config,
                    deepagents_config=deepagents_config,
                    checkpointer=checkpointer,
                    mcp_config_path=mcp_config_path,
                    no_mcp=no_mcp,
                    custom_tools=custom_tools,
                    custom_middleware=custom_middleware,
                ),
            )
            return future.result()
    else:
        return asyncio.run(
            create_nanobot_agent_async(
                workspace=workspace,
                nanobot_config=nanobot_config,
                deepagents_config=deepagents_config,
                checkpointer=checkpointer,
                mcp_config_path=mcp_config_path,
                no_mcp=no_mcp,
                custom_tools=custom_tools,
                custom_middleware=custom_middleware,
            )
        )


async def create_nanobot_agent_async(
    workspace: Path,
    nanobot_config: "Config",
    deepagents_config: "DeepAgentsConfig",
    checkpointer: Any | None = None,
    mcp_config_path: str | None = None,
    no_mcp: bool = False,
    custom_tools: list[Any] | None = None,
    custom_middleware: list[Any] | None = None,
) -> tuple[Any, Any, dict[str, Any]]:
    """Async version of create_nanobot_agent.

    Uses:
    - deepagents_cli for model resolution and MCP loading
    - deepagents.create_deep_agent() for agent creation

    Args:
        workspace: Workspace directory
        nanobot_config: nanobot configuration
        deepagents_config: DeepAgents configuration
        checkpointer: Session checkpointer
        mcp_config_path: Optional MCP config path
        no_mcp: Disable MCP loading
        custom_tools: Additional tools to add
        custom_middleware: Additional middleware

    Returns:
        Tuple of (agent, backend, mcp_info)
    """
    if not DEEPAGENTS_AVAILABLE:
        raise ImportError("deepagents is required. Install with: pip install deepagents")

    model, model_result = _init_model(deepagents_config)
    project_context = ProjectContext.from_user_cwd(workspace) if CLI_AVAILABLE else None
    tools, session_manager, server_infos = await _load_mcp_tools(
        mcp_config_path, no_mcp, project_context
    )
    system_prompt = _build_system_prompt(workspace)
    backend = _create_backend(workspace, deepagents_config)

    if custom_tools:
        tools = [*custom_tools, *tools]

    if deepagents_config.middleware.enable_flatten_content_blocks:
        from nanobot_deep.langgraph.middleware import FlattenContentBlocksMiddleware

        middleware = custom_middleware or []
        middleware.append(FlattenContentBlocksMiddleware())
        subagents = [
            {
                **GENERAL_PURPOSE_SUBAGENT,
                "middleware": [FlattenContentBlocksMiddleware()],
            }
        ]
    else:
        middleware = custom_middleware or []
        subagents = None

    backend_type = deepagents_config.backend.type
    interrupt_config = deepagents_config.get_interrupt_on_config(backend_type)
    interrupt_on = interrupt_config if any(interrupt_config.values()) else None

    if backend_type == "local_shell" and interrupt_on and interrupt_on.get("execute"):
        logger.info("HITL enabled for execute tool (security best practice for shell execution)")

    agent = create_deep_agent(
        model=model,
        tools=tools,
        system_prompt=system_prompt,
        backend=backend,
        checkpointer=checkpointer,
        skills=deepagents_config.get_skills_paths(workspace),
        memory=deepagents_config.get_memory_paths(workspace),
        middleware=middleware,
        subagents=subagents,
        interrupt_on=interrupt_on,
        debug=deepagents_config.debug,
        name=deepagents_config.name,
    )

    agent = agent.with_config({"recursion_limit": deepagents_config.recursion_limit})

    mcp_info = {
        "session_manager": session_manager,
        "server_infos": server_infos,
        "tools": tools,
    }

    logger.info(
        "Created nanobot agent: model={}, backend={}",
        getattr(model_result, "model_name", "unknown") if model_result else "unknown",
        backend_type,
    )

    return agent, backend, mcp_info


def _init_model(config: "DeepAgentsConfig") -> tuple[Any, Any]:
    """Initialize model via CLI config.

    Args:
        config: DeepAgents configuration

    Returns:
        Tuple of (model, model_result)
    """
    import os

    if not CLI_AVAILABLE:
        raise ImportError("deepagents-cli required for model resolution")

    apply_deepagents_config_path()

    if config.model.name or config.model.api_key or config.model.api_base:
        logger.warning(
            "deepagents.json model.* fields are ignored for model/provider resolution; "
            "configure ~/.deepagents/config.toml instead"
        )

    extra_kwargs: dict[str, Any] = {
        "max_tokens": config.model.max_tokens,
        "temperature": config.model.temperature,
    }
    model_spec = os.environ.get("DEEPAGENTS_TEST_MODEL") or os.environ.get("NANOBOT_TEST_MODEL")

    try:
        result = create_model(model_spec=model_spec, extra_kwargs=extra_kwargs)
    except ModelConfigError as e:
        msg = (
            "DeepAgents model configuration error. Configure provider/model in "
            "~/.deepagents/config.toml, then retry. Original error: " + str(e)
        )
        raise RuntimeError(msg) from e

    logger.info("Initialized model provider={} model={}", result.provider, result.model_name)
    return result.model, result


def _create_backend(workspace: Path, config: "DeepAgentsConfig") -> Any:
    """Create backend based on config.

    Args:
        workspace: Workspace directory
        config: DeepAgents configuration

    Returns:
        Backend instance (FilesystemBackend or LocalShellBackend)
    """
    backend_type = config.backend.type

    if backend_type == "local_shell":
        path_env = (
            f"/usr/local/bin:{config.backend.path_append}"
            if config.backend.path_append
            else "/usr/local/bin:/usr/bin:/bin"
        )
        logger.info(
            "Using LocalShellBackend with timeout={}s, restrict_to_workspace={}",
            config.backend.exec_timeout,
            config.backend.restrict_to_workspace,
        )
        return LocalShellBackend(
            root_dir=workspace,
            timeout=config.backend.exec_timeout,
            env={"PATH": path_env},
            restrict_to_workspace=config.backend.restrict_to_workspace,
        )

    logger.info("Using FilesystemBackend (file operations only)")
    return FilesystemBackend(root_dir=workspace)


async def _load_mcp_tools(
    config_path: str | None,
    no_mcp: bool,
    project_context: Any | None,
) -> tuple[list[Any], Any, list[Any]]:
    """Load MCP tools via CLI utility.

    Args:
        config_path: Optional MCP config path
        no_mcp: Disable MCP loading
        project_context: Project context

    Returns:
        Tuple of (tools, session_manager, server_infos)
    """
    if no_mcp or not CLI_AVAILABLE:
        return [], None, []

    if project_context is None:
        project_context = ProjectContext.from_user_cwd(Path.cwd())

    try:
        tools, session_manager, server_infos = await resolve_and_load_mcp_tools(
            explicit_config_path=config_path,
            no_mcp=no_mcp,
            project_context=project_context,
        )
        if tools:
            logger.info(
                "Loaded {} MCP tools from {} server(s)",
                len(tools),
                len(server_infos),
            )
        return tools, session_manager, server_infos
    except Exception as e:
        logger.error(f"Failed to connect MCP servers: {e}")
        return [], None, []


def _build_system_prompt(workspace: Path) -> str:
    """Build nanobot-specific system prompt.

    Args:
        workspace: Workspace directory

    Returns:
        System prompt string
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M (%A)")
    tz = time.strftime("%Z") or "UTC"

    return f"""# nanobot Agent

## Current Time
{now} ({tz})

## Workspace
Your workspace is at: {workspace}

## Skills
Skills are available at: {workspace}/skills/ (read SKILL.md files as needed)

## Behavior
- Be concise and direct. Don't over-explain unless asked.
- NEVER add unnecessary preamble ("Sure!", "Great question!", "I'll now...").
- When doing tasks: understand first, act, then verify.
- Keep working until the task is fully complete.
- Use the task tool to delegate complex, multi-step tasks to subagents.
"""
