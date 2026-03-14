"""CLI entry point for nanobot-deep.

This module provides a CLI that extends nanobot with LangGraph/DeepAgents support.
"""

from __future__ import annotations

import asyncio
import signal
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.text import Text

app = typer.Typer(
    name="nanobot-deep",
    help="Nanobot with LangGraph/DeepAgents integration",
    no_args_is_help=True,
)

console = Console()
EXIT_COMMANDS = {"exit", "quit", "/exit", "/quit", ":q"}

_NANOBOT_LOGO = "🤖"


def _load_config(
    config_path: str | None = None,
    workspace: str | None = None,
):
    """Load nanobot config with optional overrides."""
    from nanobot.config.loader import load_config, set_config_path

    cfg_path = None
    if config_path:
        cfg_path = Path(config_path).expanduser().resolve()
        if not cfg_path.exists():
            console.print(f"[red]Error: Config file not found: {cfg_path}[/red]")
            raise typer.Exit(1)
        set_config_path(cfg_path)
        console.print(f"[dim]Using config: {cfg_path}[/dim]")

    loaded = load_config(cfg_path)
    if workspace:
        loaded.agents.defaults.workspace = workspace
    return loaded


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Nanobot with LangGraph/DeepAgents integration.

    This CLI wraps nanobot and adds deep-specific commands.
    All nanobot commands are available.
    """
    if ctx.invoked_subcommand is None:
        typer.echo("Use 'nanobot-deep --help' for available commands")


@app.command()
def deep():
    """Run with DeepAgents backend (LangGraph-based agent)."""
    from nanobot_deep import is_deepagents_available

    if not is_deepagents_available():
        typer.secho(
            "Error: deepagents is not installed. Install with: pip install deepagents",
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)

    typer.secho(
        "DeepAgents backend is available. Use 'nanobot-deep gateway' or 'nanobot-deep agent' to start.",
        fg=typer.colors.GREEN,
    )


@app.command()
def config():
    """Show or create default deepagents.json configuration."""
    from pathlib import Path

    from nanobot_deep import DeepAgentsConfig, save_deepagents_config

    config_path = Path.home() / ".nanobot" / "deepagents.json"

    if config_path.exists():
        typer.secho(f"Config exists at {config_path}", fg=typer.colors.GREEN)
        with open(config_path) as f:
            typer.echo(f.read())
    else:
        typer.secho(f"Creating default config at {config_path}", fg=typer.colors.YELLOW)
        default_config = DeepAgentsConfig()
        save_deepagents_config(default_config, config_path)
        typer.secho("Done!", fg=typer.colors.GREEN)


@app.command()
def gateway(
    port: int = typer.Option(18790, "--port", "-p", help="Gateway port (reserved for future use)"),
    workspace: str | None = typer.Option(None, "--workspace", "-w", help="Workspace directory"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    config: str | None = typer.Option(None, "--config", "-c", help="Path to config file"),
):
    """Start the nanobot-deep gateway with DeepAgent backend.

    This uses LangGraph-based DeepAgent instead of the LiteLLM-based AgentLoop.
    """
    from nanobot.utils.helpers import sync_workspace_templates

    if verbose:
        import logging

        logging.basicConfig(level=logging.DEBUG)

    nanobot_config = _load_config(config, workspace)

    console.print(f"{_NANOBOT_LOGO} Starting nanobot-deep gateway (DeepAgent backend)...")
    sync_workspace_templates(nanobot_config.workspace_path)

    from nanobot_deep.gateway import run_gateway

    asyncio.run(
        run_gateway(
            config=nanobot_config,
            workspace=nanobot_config.workspace_path,
            verbose=verbose,
        )
    )


@app.command()
def agent(
    message: str = typer.Option(None, "--message", "-m", help="Message to send to the agent"),
    session_id: str = typer.Option("cli:direct", "--session", "-s", help="Session ID"),
    workspace: str | None = typer.Option(None, "--workspace", "-w", help="Workspace directory"),
    config: str | None = typer.Option(None, "--config", "-c", help="Config file path"),
    markdown: bool = typer.Option(
        True, "--markdown/--no-markdown", help="Render assistant output as Markdown"
    ),
    logs: bool = typer.Option(
        False, "--logs/--no-logs", help="Show nanobot runtime logs during chat"
    ),
):
    """Interact with the DeepAgent directly.

    This uses LangGraph-based DeepAgent instead of the LiteLLM-based AgentLoop.
    """
    from loguru import logger
    from nanobot.utils.helpers import sync_workspace_templates
    from prompt_toolkit import PromptSession
    from prompt_toolkit.formatted_text import HTML
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.patch_stdout import patch_stdout

    nanobot_config = _load_config(config, workspace)
    sync_workspace_templates(nanobot_config.workspace_path)

    if logs:
        logger.enable("nanobot")
        logger.enable("nanobot_deep")
    else:
        logger.disable("nanobot")
        logger.disable("nanobot_deep")

    from nanobot_deep.agent.deep_agent import DeepAgent
    from nanobot_deep.config.loader import load_deepagents_config
    from nanobot_deep.langgraph.checkpointer import SessionCheckpointer

    db_path = nanobot_config.workspace_path.parent / "sessions.db"
    checkpointer = SessionCheckpointer(db_path, migrate_from_json=True)
    checkpointer.setup()

    deepagents_config = load_deepagents_config()

    agent_instance = DeepAgent(
        workspace=nanobot_config.workspace_path,
        config=nanobot_config,
        checkpointer=checkpointer,
        deepagents_config=deepagents_config,
    )

    def _print_response(response: str) -> None:
        content = response or ""
        body = Markdown(content) if markdown else Text(content)
        console.print()
        console.print(f"[cyan]{_NANOBOT_LOGO} nanobot-deep[/cyan]")
        console.print(body)
        console.print()

    def _thinking_ctx():
        if logs:
            from contextlib import nullcontext

            return nullcontext()
        return console.status("[dim]nanobot-deep is thinking...[/dim]", spinner="dots")

    async def _progress(text: str) -> None:
        console.print(f"  [dim]↳ {text}[/dim]")

    if message:

        async def run_once():
            with _thinking_ctx():
                response = await agent_instance.process_direct(
                    message,
                    session_key=session_id,
                    on_progress=_progress if not logs else None,
                )
            _print_response(response)
            await agent_instance.close()

        asyncio.run(run_once())
    else:
        history_file = Path.home() / ".nanobot" / "cli_history"
        history_file.parent.mkdir(parents=True, exist_ok=True)

        prompt_session = PromptSession(
            history=FileHistory(str(history_file)),
            enable_open_in_editor=False,
            multiline=False,
        )

        console.print(
            f"{_NANOBOT_LOGO} Interactive mode (type [bold]exit[/bold] or [bold]Ctrl+C[/bold] to quit)\n"
        )

        if ":" in session_id:
            cli_channel, cli_chat_id = session_id.split(":", 1)
        else:
            cli_channel, cli_chat_id = "cli", session_id

        def _handle_signal(signum, frame):
            sig_name = signal.Signals(signum).name
            console.print(f"\nReceived {sig_name}, goodbye!")
            sys.exit(0)

        signal.signal(signal.SIGINT, _handle_signal)
        signal.signal(signal.SIGTERM, _handle_signal)
        if hasattr(signal, "SIGHUP"):
            signal.signal(signal.SIGHUP, _handle_signal)
        if hasattr(signal, "SIGPIPE"):
            signal.signal(signal.SIGPIPE, signal.SIG_IGN)

        async def run_interactive():
            try:
                while True:
                    try:
                        with patch_stdout():
                            user_input = await prompt_session.prompt_async(
                                HTML("<b fg='ansiblue'>You:</b> "),
                            )
                        command = user_input.strip()
                        if not command:
                            continue

                        if command.lower() in EXIT_COMMANDS:
                            console.print("\nGoodbye!")
                            break

                        with _thinking_ctx():
                            response = await agent_instance.process_direct(
                                command,
                                session_key=session_id,
                                channel=cli_channel,
                                chat_id=cli_chat_id,
                                on_progress=_progress if not logs else None,
                            )
                        _print_response(response)
                    except KeyboardInterrupt:
                        console.print("\nGoodbye!")
                        break
                    except EOFError:
                        console.print("\nGoodbye!")
                        break
            finally:
                await agent_instance.close()

        asyncio.run(run_interactive())


def run_nanobot():
    """Entry point that handles deep commands locally, delegates others to nanobot."""
    import sys

    try:
        from nanobot.cli.commands import app as nanobot_app
    except ImportError:
        typer.secho(
            "Error: nanobot-ai is not installed. Install with: pip install nanobot-ai",
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)

    if len(sys.argv) > 1:
        first_arg = sys.argv[1]
        if first_arg in ["deep", "config", "gateway", "agent"]:
            app()
            return

    nanobot_app()


if __name__ == "__main__":
    run_nanobot()
