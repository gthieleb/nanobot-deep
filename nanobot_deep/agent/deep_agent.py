"""Deep Agent wrapper for nanobot.

This module provides the main integration between nanobot and deepagents,
creating a LangGraph-based agent with nanobot-specific tools and features.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from contextlib import AsyncExitStack
from pathlib import Path
from typing import TYPE_CHECKING, Any

from loguru import logger

from nanobot_deep.config.deepagents_cli import apply_deepagents_config_path
from nanobot_deep.config.loader import merge_with_nanobot_config
from nanobot_deep.config.schema import DeepAgentsConfig
from nanobot_deep.langgraph.bridge import (
    extract_reply_context,
    should_delegate_task,
)
from nanobot_deep.langgraph.middleware import FlattenContentBlocksMiddleware

if TYPE_CHECKING:
    from nanobot.bus.events import InboundMessage, OutboundMessage
    from nanobot.config.schema import Config

try:
    from deepagents import create_deep_agent
    from deepagents.backends import FilesystemBackend, StateBackend
    from deepagents.backends.protocol import BackendProtocol
    from deepagents.middleware.subagents import GENERAL_PURPOSE_SUBAGENT

    DEEPAGENTS_AVAILABLE = True
except ImportError:
    DEEPAGENTS_AVAILABLE = False
    create_deep_agent = None

try:
    from langfuse.langchain import CallbackHandler as LangfuseCallbackHandler

    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    LangfuseCallbackHandler = None


class DeepAgent:
    """LangGraph-based agent using deepagents framework.

    This class wraps deepagents' create_deep_agent() to provide:
    - File operations via FilesystemBackend
    - Subagent spawning via task tool
    - Session checkpointing
    - Multi-channel message routing
    - Config from nanobot + deepagents.json

    Args:
        workspace: Workspace directory for file operations
        config: nanobot configuration
        checkpointer: Session checkpointer instance
        deepagents_config: Optional DeepAgentsConfig (loaded if None)

    Example:
        >>> from nanobot.langgraph import SessionCheckpointer
        >>> checkpointer = SessionCheckpointer()
        >>> agent = DeepAgent(workspace, config, checkpointer)
        >>> response = await agent.process(msg)
    """

    def __init__(
        self,
        workspace: Path,
        config: "Config",
        checkpointer: Any | None = None,
        deepagents_config: DeepAgentsConfig | None = None,
    ):
        if not DEEPAGENTS_AVAILABLE:
            raise ImportError("deepagents is not installed. Install with: pip install deepagents")

        self.workspace = workspace
        self.config = config
        self.checkpointer = checkpointer

        self.dg_config = merge_with_nanobot_config(config, deepagents_config)

        self._agent = None
        self._backend: BackendProtocol | None = None
        self._tools: list[Any] = []
        self._mcp_stack: AsyncExitStack | None = None
        self._mcp_connected = False
        self._mcp_servers = config.tools.mcp_servers if hasattr(config, "tools") else {}

    def _init_model(self) -> Any:
        """Initialize model from DeepAgents CLI configuration.

        Model/provider resolution is delegated to `deepagents_cli.config.create_model`
        using `~/.deepagents/config.toml` or `DEEPAGENTS_CONFIG_PATH`.
        """
        try:
            from deepagents_cli.config import ModelConfigError, create_model
        except ImportError as e:
            raise ImportError(
                "deepagents-cli is required for model resolution. Install with: pip install deepagents-cli"
            ) from e
        import os

        apply_deepagents_config_path()

        if (
            self.dg_config.model.name
            or self.dg_config.model.api_key
            or self.dg_config.model.api_base
        ):
            logger.warning(
                "deepagents.json model.* fields are ignored for model/provider resolution; "
                "configure ~/.deepagents/config.toml (or set DEEPAGENTS_CONFIG_PATH) instead"
            )

        extra_kwargs: dict[str, Any] = {
            "max_tokens": self.dg_config.model.max_tokens,
            "temperature": self.dg_config.model.temperature,
        }
        model_spec = (
            os.environ.get("DEEPAGENTS_TEST_MODEL") or os.environ.get("NANOBOT_TEST_MODEL") or None
        )

        try:
            result = create_model(model_spec=model_spec, extra_kwargs=extra_kwargs)
        except ModelConfigError as e:
            msg = (
                "DeepAgents model configuration error. Configure provider/model in "
                "~/.deepagents/config.toml (or set DEEPAGENTS_CONFIG_PATH, or set provider "
                "credentials env vars), "
                f"then retry. Original error: {e}"
            )
            raise RuntimeError(msg) from e

        logger.info(
            "Initialized DeepAgents model provider={} model={}",
            result.provider,
            result.model_name,
        )
        return result.model

    async def validate_model(self, timeout_seconds: float = 20.0) -> None:
        """Validate model reachability and existence with a lightweight call."""
        model = self._init_model()
        model_name = self.dg_config.model.name or self.config.agents.defaults.model

        try:
            await asyncio.wait_for(
                model.ainvoke([HumanMessage(content="Reply with OK.")]),
                timeout=timeout_seconds,
            )
            logger.info(f"Model validation passed: {model_name}")
        except Exception as e:
            logger.error(f"Model validation failed for {model_name}: {e}")
            raise RuntimeError(f"Model validation failed for {model_name}: {e}") from e

    def _init_backend(self) -> BackendProtocol:
        """Get or create the backend for file operations."""
        if self._backend is None:
            self._backend = FilesystemBackend(root_dir=self.workspace)
        return self._backend

    def _build_custom_tools(self) -> list[Any]:
        """Build nanobot-specific custom tools."""
        tools = []

        return tools

    def _create_agent(self) -> Any:
        """Create the deep agent with configured middleware."""
        model = self._init_model()
        backend = self._init_backend()
        custom_tools = self._build_custom_tools()

        system_prompt = self._build_system_prompt()

        custom_middleware: list[Any] = []
        subagents = None
        if self.dg_config.middleware.enable_flatten_content_blocks:
            custom_middleware.append(FlattenContentBlocksMiddleware())
            subagents = [
                {
                    **GENERAL_PURPOSE_SUBAGENT,
                    "middleware": [FlattenContentBlocksMiddleware()],
                }
            ]

        agent = create_deep_agent(
            model=model,
            tools=custom_tools,
            system_prompt=system_prompt,
            backend=backend,
            checkpointer=self.checkpointer,
            skills=self.dg_config.get_skills_paths(self.workspace),
            memory=self.dg_config.get_memory_paths(self.workspace),
            middleware=custom_middleware,
            subagents=subagents,
            interrupt_on=self.dg_config.get_interrupt_on_config()
            if any(self.dg_config.get_interrupt_on_config().values())
            else None,
            debug=self.dg_config.debug,
            name=self.dg_config.name,
        )

        return agent.with_config({"recursion_limit": self.dg_config.recursion_limit})

    def _build_system_prompt(self) -> str:
        """Build system prompt with nanobot context."""
        from datetime import datetime
        import time

        now = datetime.now().strftime("%Y-%m-%d %H:%M (%A)")
        tz = time.strftime("%Z") or "UTC"

        return f"""# nanobot Agent

## Current Time
{now} ({tz})

## Workspace
Your workspace is at: {self.workspace}

## Skills
Skills are available at: {self.workspace}/skills/ (read SKILL.md files as needed)

## Behavior
- Be concise and direct. Don't over-explain unless asked.
- NEVER add unnecessary preamble ("Sure!", "Great question!", "I'll now...").
- When doing tasks: understand first, act, then verify.
- Keep working until the task is fully complete.
- Use the task tool to delegate complex, multi-step tasks to subagents.
"""

    @property
    def agent(self) -> Any:
        """Get or create the compiled agent."""
        if self._agent is None:
            self._agent = self._create_agent()
        return self._agent

    async def _connect_mcp(self) -> None:
        """Connect to configured MCP servers."""
        if self._mcp_connected or not self._mcp_servers:
            return

        try:
            from langchain_mcp_adapters import load_mcp_tools

            self._mcp_stack = AsyncExitStack()
            await self._mcp_stack.__aenter__()

            for name, server_config in self._mcp_servers.items():
                try:
                    tools = await load_mcp_tools(server_config, self._mcp_stack)
                    self._tools.extend(tools)
                    logger.info(f"Loaded {len(tools)} tools from MCP server: {name}")
                except Exception as e:
                    logger.error(f"Failed to load MCP tools from {name}: {e}")

            self._mcp_connected = True
            if self._tools:
                self._agent = None

        except ImportError:
            logger.warning("langchain-mcp-adapters not installed, skipping MCP")
        except Exception as e:
            logger.error(f"Failed to connect MCP servers: {e}")

    def _should_delegate(self, msg: "InboundMessage") -> tuple[bool, str]:
        """Determine if message should be delegated to a subagent.

        Args:
            msg: The inbound message

        Returns:
            Tuple of (should_delegate, delegate_type)
        """
        return should_delegate_task(
            msg,
            self.dg_config.task_routing.control_commands,
            self.dg_config.task_routing.auto_delegate_reply_to,
        )

    def _get_reply_context(self, msg: "InboundMessage") -> dict[str, Any] | None:
        """Extract reply-to context from message.

        Args:
            msg: The inbound message

        Returns:
            Reply context dict or None
        """
        return extract_reply_context(msg)

    def _get_reply_handler_subagent(self) -> dict[str, Any] | None:
        """Get the reply-handler subagent config if available.

        Returns:
            Subagent config dict or None
        """
        for subagent in self.dg_config.subagents:
            if subagent.name == "reply-handler":
                return {
                    "name": subagent.name,
                    "description": subagent.description,
                    "system_prompt": subagent.system_prompt,
                    "model": subagent.model,
                }
        return None

    def _get_langfuse_handler(self) -> Any | None:
        """Get Langfuse callback handler if configured and available.

        Environment variables take precedence over config file values.

        Returns:
            Langfuse CallbackHandler or None if not configured/available
        """
        import os

        if not LANGFUSE_AVAILABLE:
            return None

        langfuse_config = self.dg_config.langfuse
        if not langfuse_config.enabled:
            return None

        public_key = os.environ.get("LANGFUSE_PUBLIC_KEY") or langfuse_config.public_key
        secret_key = os.environ.get("LANGFUSE_SECRET_KEY") or langfuse_config.secret_key
        host = os.environ.get("LANGFUSE_HOST") or langfuse_config.host

        if not public_key or not secret_key:
            logger.warning("Langfuse enabled but missing credentials (public_key/secret_key)")
            return None

        try:
            handler = LangfuseCallbackHandler(
                public_key=public_key,
                secret_key=secret_key,
                host=host,
                environment=langfuse_config.environment,
                session_id=langfuse_config.session_id,
                user_id=langfuse_config.user_id,
                tags=langfuse_config.tags or None,
                metadata=langfuse_config.metadata or None,
            )
            logger.debug(f"Langfuse handler initialized for {host}")
            return handler
        except Exception as e:
            logger.warning(f"Failed to initialize Langfuse handler: {e}")
            return None

    async def process(
        self,
        msg: "InboundMessage",
        on_progress: Callable[[str, bool], Awaitable[None]] | None = None,
        history: list[dict] | None = None,
    ) -> "OutboundMessage":
        """Process an inbound message.

        Args:
            msg: The inbound message
            on_progress: Optional callback for progress updates
            history: Optional conversation history

        Returns:
            OutboundMessage with the response
        """
        from nanobot.bus.events import OutboundMessage
        from nanobot_deep.langgraph.bridge import (
            translate_inbound_to_state,
            translate_result_to_outbound,
        )

        await self._connect_mcp()

        content = msg.content.strip()
        if content.startswith("/new"):
            await self._clear_session_async(msg.session_key)
            return OutboundMessage(
                channel=msg.channel,
                chat_id=msg.chat_id,
                content="New session started.",
                metadata=msg.metadata or {},
            )

        should_delegate, delegate_type = self._should_delegate(msg)
        reply_context = self._get_reply_context(msg)

        if delegate_type == "reply" and should_delegate:
            logger.debug("Processing reply-to message with context delegation")

        state = translate_inbound_to_state(msg, history, reply_context=reply_context)
        config: dict[str, Any] = {
            "configurable": {
                "thread_id": msg.session_key,
            },
        }

        langfuse_handler = self._get_langfuse_handler()
        if langfuse_handler:
            config["callbacks"] = [langfuse_handler]

        try:
            if on_progress:
                result = await self._invoke_with_progress(state, config, on_progress)
            else:
                result = await self.agent.ainvoke(state, config)

            return translate_result_to_outbound(result, msg)

        except Exception as e:
            logger.exception("Error in deep agent")
            return OutboundMessage(
                channel=msg.channel,
                chat_id=msg.chat_id,
                content=self._format_user_facing_error(e),
                metadata=msg.metadata or {},
            )

    @staticmethod
    def _exception_chain(exc: Exception, max_depth: int = 6) -> list[BaseException]:
        """Collect exception and nested causes/contexts."""
        chain: list[BaseException] = []
        current: BaseException | None = exc
        seen: set[int] = set()

        while current and len(chain) < max_depth:
            if id(current) in seen:
                break
            seen.add(id(current))
            chain.append(current)
            current = current.__cause__ or current.__context__

        return chain

    @classmethod
    def _format_user_facing_error(cls, exc: Exception) -> str:
        """Map provider/runtime exceptions to clear user-facing error messages."""
        chain = cls._exception_chain(exc)
        names = {type(err).__name__.lower() for err in chain}
        text = " ".join(str(err) for err in chain if str(err)).lower()

        def has_name(*candidates: str) -> bool:
            return any(candidate.lower() in names for candidate in candidates)

        def has_text(*needles: str) -> bool:
            return any(needle in text for needle in needles)

        if has_name("RateLimitError", "RouterRateLimitError") or has_text(
            "rate limit",
            "too many requests",
            "429",
        ):
            return "Provider rate limit reached (429). Please retry in a moment."

        if has_name("BudgetExceededError") or has_text(
            "insufficient_quota",
            "quota exceeded",
            "billing",
            "credits",
            "budget exceeded",
        ):
            return "Provider quota exceeded. Please check billing/quota and try again."

        if has_name("AuthenticationError", "PermissionDeniedError") or has_text(
            "invalid api key",
            "authentication",
            "unauthorized",
            "forbidden",
            "permission denied",
            "401",
            "403",
        ):
            return "Provider authentication/permission failed. Please verify API key and provider config."

        if has_name(
            "Timeout", "APIConnectionError", "ServiceUnavailableError", "BadGatewayError"
        ) or has_text(
            "timeout",
            "timed out",
            "connection",
            "service unavailable",
            "bad gateway",
            "502",
            "503",
            "504",
        ):
            return "Provider timeout or connectivity issue. Please retry shortly."

        if has_name(
            "ContextWindowExceededError",
            "BadRequestError",
            "InvalidRequestError",
            "UnprocessableEntityError",
        ) or has_text(
            "context window",
            "too long",
            "max token",
            "maximum context length",
            "invalid request",
            "400",
            "422",
        ):
            return "Provider rejected the request (invalid input or context too large)."

        detail = str(chain[0]).strip() if chain else str(exc).strip()
        if detail:
            return f"Sorry, I encountered an error: {detail}"
        return "Sorry, I encountered an unexpected error while calling the AI provider."

    async def _invoke_with_progress(
        self,
        state: dict[str, Any],
        config: dict[str, Any],
        on_progress: Callable[[str, bool], Awaitable[None]],
    ) -> dict[str, Any]:
        """Invoke agent with streaming."""
        final_result: dict[str, Any] = {}

        async for event in self.agent.astream_events(state, config, version="v2"):
            kind = event.get("event")

            if kind == "on_chat_model_stream":
                content = event.get("data", {}).get("chunk")
                if content and hasattr(content, "content") and content.content:
                    await on_progress(str(content.content), False)

            elif kind == "on_tool_start":
                tool_name = event.get("name", "unknown")
                tool_input = event.get("data", {}).get("input", {})
                hint = self._format_tool_hint(tool_name, tool_input)
                if hint:
                    await on_progress(hint, True)

            elif kind == "on_chain_end":
                if event.get("name") == "LangGraph":
                    final_result = event.get("data", {}).get("output", {})

        return final_result or {"messages": []}

    @staticmethod
    def _format_tool_hint(name: str, args: dict) -> str:
        """Format tool call as concise hint."""
        if not args:
            return f"{name}()"

        first_val = next(iter(args.values()), None)
        if isinstance(first_val, str):
            if len(first_val) > 40:
                return f'{name}("{first_val[:40]}…")'
            return f'{name}("{first_val}")'
        return f"{name}()"

    async def process_direct(
        self,
        content: str,
        session_key: str = "cli:direct",
        channel: str = "cli",
        chat_id: str = "direct",
        on_progress: Callable[[str], Awaitable[None]] | None = None,
    ) -> str:
        """Process a message directly (for CLI usage).

        Args:
            content: Message content
            session_key: Session identifier
            channel: Channel name
            chat_id: Chat identifier
            on_progress: Progress callback

        Returns:
            Response content
        """
        from nanobot.bus.events import InboundMessage

        msg = InboundMessage(
            channel=channel,
            sender_id="user",
            chat_id=chat_id,
            content=content,
        )

        async def _progress(text: str, is_tool_hint: bool = False) -> None:
            if on_progress:
                await on_progress(text)

        response = await self.process(msg, on_progress=_progress)
        return response.content

    async def _clear_session_async(self, session_key: str) -> bool:
        checkpointer = self.checkpointer
        if checkpointer is None:
            return False
        if hasattr(checkpointer, "adelete_thread"):
            await checkpointer.adelete_thread(session_key)
            return True
        if hasattr(checkpointer, "delete_thread"):
            checkpointer.delete_thread(session_key)
            return True
        if hasattr(checkpointer, "delete_session"):
            result = checkpointer.delete_session(session_key)
            if asyncio.iscoroutine(result):
                await result
            return True
        return False

    def clear_session(self, session_key: str) -> bool:
        """Clear a session's history."""
        checkpointer = self.checkpointer
        if checkpointer is None:
            return False
        if hasattr(checkpointer, "delete_thread"):
            checkpointer.delete_thread(session_key)
            return True
        if hasattr(checkpointer, "delete_session"):
            checkpointer.delete_session(session_key)
            return True
        return False

    def get_history(self, session_key: str, limit: int = 100) -> list[dict]:
        """Get message history for a session."""
        if self.checkpointer:
            return self.checkpointer.get_session_history(session_key, limit)
        return []

    async def close(self) -> None:
        """Close connections and cleanup."""
        if self._mcp_stack:
            try:
                await self._mcp_stack.aclose()
            except Exception:
                pass
            self._mcp_stack = None
        self._mcp_connected = False


def is_deepagents_available() -> bool:
    """Check if deepagents is available."""
    return DEEPAGENTS_AVAILABLE
