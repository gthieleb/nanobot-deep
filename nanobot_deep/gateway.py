"""Gateway module for nanobot-deep using DeepAgent.

This module provides the gateway functionality that:
- Loads nanobot config
- Creates MessageBus
- Creates DeepAgent instance (LangGraph-based)
- Creates ChannelManager (from nanobot-ai)
- Subscribes to inbound messages
- Processes with DeepAgent.process()
- Publishes to outbound
"""

from __future__ import annotations

import asyncio
import signal
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
    from nanobot.bus.events import InboundMessage
    from nanobot.bus.queue import MessageBus
    from nanobot.channels.manager import ChannelManager
    from nanobot.config.schema import Config

    from nanobot_deep.agent.deep_agent import DeepAgent


class DeepGateway:
    """Gateway using DeepAgent (LangGraph-based) backend.

    This is the main entry point for running nanobot-deep in gateway mode,
    processing messages from multiple channels through a LangGraph agent.

    Args:
        config: nanobot configuration
        workspace: Workspace directory
        verbose: Enable verbose logging

    Example:
        >>> from nanobot.config.loader import load_config
        >>> config = load_config()
        >>> gateway = DeepGateway(config)
        >>> await gateway.run()
    """

    def __init__(
        self,
        config: "Config",
        workspace: Path | None = None,
        verbose: bool = False,
    ):
        from nanobot.bus.queue import MessageBus
        from nanobot.channels.manager import ChannelManager

        self.config = config
        self.workspace = workspace or config.workspace_path
        self.verbose = verbose

        self.bus: "MessageBus" = MessageBus()
        self.channels: "ChannelManager" = ChannelManager(config, self.bus)
        self.agent: "DeepAgent | None" = None
        self.checkpointer: "AsyncSqliteSaver | None" = None

        self._running = False
        self._shutdown_event = asyncio.Event()

    async def _setup_checkpointer(self) -> "AsyncSqliteSaver":
        """Create and setup the session checkpointer."""
        import aiosqlite

        from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

        db_path = self.workspace.parent / "sessions.db"
        conn = await aiosqlite.connect(str(db_path))
        checkpointer = AsyncSqliteSaver(conn)
        await checkpointer.setup()
        return checkpointer

    async def _setup_agent(self) -> "DeepAgent":
        from nanobot_deep.agent.deep_agent import DeepAgent
        from nanobot_deep.config.loader import load_deepagents_config

        logger.debug("Setting up checkpointer...")
        self.checkpointer = await self._setup_checkpointer()
        logger.debug(f"Checkpointer ready: {type(self.checkpointer).__name__}")

        deepagents_config = load_deepagents_config()
        logger.debug(
            f"Loaded deepagents config: model={deepagents_config.model.name or 'from nanobot config'}"
        )

        if self.verbose:
            deepagents_config.debug = True

        logger.debug("Creating DeepAgent instance...")
        agent = DeepAgent(
            workspace=self.workspace,
            config=self.config,
            checkpointer=self.checkpointer,
            deepagents_config=deepagents_config,
        )
        logger.debug("DeepAgent instance created")
        return agent

    async def _process_inbound(self, msg: "InboundMessage") -> None:
        if self.agent is None:
            logger.error("Agent not initialized")
            return

        logger.debug(
            f"Processing inbound: channel={msg.channel}, chat_id={msg.chat_id}, content={msg.content[:100]}..."
        )

        try:
            response = await self.agent.process(msg)
            logger.debug(f"Agent response: {response.content[:100]}...")
            await self.bus.publish_outbound(response)
        except Exception as e:
            logger.exception(f"Error processing message: {e}")
            from nanobot.bus.events import OutboundMessage

            error_response = OutboundMessage(
                channel=msg.channel,
                chat_id=msg.chat_id,
                content=f"Sorry, I encountered an error: {str(e)}",
                metadata=msg.metadata or {},
            )
            await self.bus.publish_outbound(error_response)

    async def _consume_inbound_loop(self) -> None:
        """Background task that consumes inbound messages."""
        while self._running:
            try:
                msg = await asyncio.wait_for(
                    self.bus.consume_inbound(),
                    timeout=1.0,
                )
                asyncio.create_task(self._process_inbound(msg))
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"Error in inbound loop: {e}")

    async def run(self) -> None:
        """Start the gateway."""
        from nanobot.utils.helpers import sync_workspace_templates

        logger.info(f"Starting DeepGateway on workspace: {self.workspace}")

        sync_workspace_templates(self.workspace)

        self.agent = await self._setup_agent()

        if self.channels.enabled_channels:
            logger.info(f"Channels enabled: {', '.join(self.channels.enabled_channels)}")
        else:
            logger.warning("No channels enabled")

        self._running = True

        loop = asyncio.get_running_loop()

        def handle_signal():
            logger.info("Received shutdown signal")
            self._running = False
            self._shutdown_event.set()

        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, handle_signal)
        if hasattr(signal, "SIGHUP"):
            loop.add_signal_handler(signal.SIGHUP, handle_signal)

        try:
            inbound_task = asyncio.create_task(self._consume_inbound_loop())
            channels_task = asyncio.create_task(self.channels.start_all())

            await self._shutdown_event.wait()

        finally:
            self._running = False

            inbound_task.cancel()
            channels_task.cancel()

            await asyncio.gather(
                inbound_task,
                channels_task,
                return_exceptions=True,
            )

            await self.channels.stop_all()

            if self.agent:
                await self.agent.close()

            logger.info("DeepGateway stopped")

    def stop(self) -> None:
        """Signal the gateway to stop."""
        self._running = False
        self._shutdown_event.set()


async def run_gateway(
    config: "Config",
    workspace: Path | None = None,
    verbose: bool = False,
) -> None:
    """Run the DeepGateway.

    Args:
        config: nanobot configuration
        workspace: Optional workspace override
        verbose: Enable verbose logging
    """
    gateway = DeepGateway(config, workspace, verbose)
    await gateway.run()
