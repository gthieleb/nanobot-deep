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
import os
import signal
from pathlib import Path
from typing import TYPE_CHECKING, Any

from loguru import logger

if TYPE_CHECKING:
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
        mcp_config_path: str | None = None,
        no_mcp: bool = False,
    ):
        from nanobot.bus.queue import MessageBus
        from nanobot.channels.manager import ChannelManager

        self.config = config
        self.workspace = workspace or config.workspace_path
        self.verbose = verbose

        self.bus: "MessageBus" = MessageBus()
        self.channels: "ChannelManager" = ChannelManager(config, self.bus)
        self._ensure_custom_telegram_channel()
        self.agent: "DeepAgent | None" = None
        self.checkpointer: Any | None = None
        self.mcp_config_path = mcp_config_path
        self.no_mcp = no_mcp

        self._running = False
        self._shutdown_event = asyncio.Event()

    def _ensure_custom_telegram_channel(self) -> None:
        """Replace Telegram channel instance with CustomTelegramChannel."""
        from nanobot_deep.channels.telegram import CustomTelegramChannel
        from nanobot_deep.langgraph.interrupt_registry import REGISTRY

        channels = getattr(self.channels, "channels", None)
        if not isinstance(channels, dict):
            return

        telegram_channel = channels.get("telegram")
        if telegram_channel is None or isinstance(telegram_channel, CustomTelegramChannel):
            telegram_channel = channels.get("telegram")
            if isinstance(telegram_channel, CustomTelegramChannel):
                self._register_interrupt_callback(telegram_channel, REGISTRY)
            return

        providers = getattr(self.config, "providers", None)
        groq = getattr(providers, "groq", None)
        groq_api_key = getattr(groq, "api_key", "")

        custom_channel = CustomTelegramChannel(
            self.config.channels.telegram,
            self.bus,
        )
        custom_channel.transcription_api_key = groq_api_key
        channels["telegram"] = custom_channel
        self._register_interrupt_callback(custom_channel, REGISTRY)
        logger.info("Using CustomTelegramChannel for Telegram")

    def _register_interrupt_callback(self, channel: Any, registry: Any) -> None:
        """Register interrupt callback to send Telegram messages when interrupts are registered."""

        async def on_interrupt(interrupt: Any) -> None:
            try:
                await channel.send_interrupt(interrupt.chat_id, interrupt)
            except Exception as e:
                logger.error("Failed to send interrupt message: {}", e)

        registry.on_register(on_interrupt)

    async def _setup_checkpointer(self, deepagents_config) -> Any | None:
        """Create and setup the session checkpointer."""
        ctype = deepagents_config.checkpointer.type

        if ctype == "none":
            return None
        if ctype == "memory":
            from langgraph.checkpoint.memory import InMemorySaver

            return InMemorySaver()

        if ctype == "sqlite":
            import aiosqlite
            from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

            db_path = deepagents_config.get_checkpointer_path()
            db_path.parent.mkdir(parents=True, exist_ok=True)
            conn = await aiosqlite.connect(str(db_path))
            checkpointer = AsyncSqliteSaver(conn)
            await checkpointer.setup()
            return checkpointer

        raise ValueError(f"Unknown checkpointer type: {ctype}")

    async def _setup_agent(self) -> "DeepAgent":
        """Create the DeepAgent instance."""
        from nanobot_deep.agent.deep_agent import DeepAgent
        from nanobot_deep.config.loader import load_deepagents_config

        deepagents_config = load_deepagents_config()
        self.checkpointer = await self._setup_checkpointer(deepagents_config)

        agent = DeepAgent(
            workspace=self.workspace,
            config=self.config,
            checkpointer=self.checkpointer,
            deepagents_config=deepagents_config,
            mcp_config_path=self.mcp_config_path,
            no_mcp=self.no_mcp,
        )

        validate_on_start = os.environ.get("NANOBOT_VALIDATE_MODEL_ON_START", "1").lower()
        if validate_on_start not in {"0", "false", "no"}:
            await agent.validate_model()

        return agent

    async def _process_inbound(self, msg: "InboundMessage") -> None:
        """Process an inbound message through DeepAgent."""
        if self.agent is None:
            logger.error("Agent not initialized - cannot process message")
            from nanobot.bus.events import OutboundMessage

            error_response = OutboundMessage(
                channel=msg.channel,
                chat_id=msg.chat_id,
                content="Sorry, the agent is not initialized. Please check the logs.",
                metadata=msg.metadata or {},
            )
            await self.bus.publish_outbound(error_response)
            return

        preview = msg.content[:80] + "..." if len(msg.content) > 80 else msg.content
        logger.info(f"Processing message from {msg.channel}:{msg.sender_id}: {preview}")

        try:
            response = await self.agent.process(msg)
            logger.debug(
                f"Agent processed message, publishing response to {msg.channel}:{msg.chat_id}"
            )
            await self.bus.publish_outbound(response)
            logger.debug("Response published successfully")
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
        logger.info("Inbound message consumer started")
        while self._running:
            try:
                msg = await asyncio.wait_for(
                    self.bus.consume_inbound(),
                    timeout=1.0,
                )
                logger.debug(f"Received message from {msg.channel}:{msg.sender_id}")
                asyncio.create_task(self._process_inbound(msg))
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                logger.info("Inbound consumer cancelled")
                break
            except Exception as e:
                logger.exception(f"Error in inbound loop: {e}")
        logger.info("Inbound message consumer stopped")

    async def run(self) -> None:
        """Start the gateway."""
        from nanobot.utils.helpers import sync_workspace_templates

        logger.info(f"Starting DeepGateway on workspace: {self.workspace}")

        sync_workspace_templates(self.workspace)

        try:
            self.agent = await self._setup_agent()
            logger.info("DeepAgent initialized successfully")
        except Exception as e:
            logger.exception(f"Failed to initialize DeepAgent: {e}")
            self._shutdown_event.set()
            return

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

        inbound_task: asyncio.Task | None = None
        channels_task: asyncio.Task | None = None

        try:
            inbound_task = asyncio.create_task(self._consume_inbound_loop())
            channels_task = asyncio.create_task(self.channels.start_all())

            await self._shutdown_event.wait()

        finally:
            self._running = False

            if inbound_task:
                inbound_task.cancel()
            if channels_task:
                channels_task.cancel()

            await asyncio.gather(
                inbound_task or asyncio.sleep(0),
                channels_task or asyncio.sleep(0),
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
    mcp_config_path: str | None = None,
    no_mcp: bool = False,
) -> None:
    """Run the DeepGateway.

    Args:
        config: nanobot configuration
        workspace: Optional workspace override
        verbose: Enable verbose logging
    """
    gateway = DeepGateway(
        config,
        workspace,
        verbose,
        mcp_config_path=mcp_config_path,
        no_mcp=no_mcp,
    )
    await gateway.run()
