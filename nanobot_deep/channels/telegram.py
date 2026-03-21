"""Custom Telegram channel with /ping support.

Extends nanobot-ai's TelegramChannel to add /ping command handler
for E2E testing compatibility.
"""

from telegram.ext import CommandHandler, ContextTypes
from telegram import Update
from telegram.request import HTTPXRequest
from telegram.ext import Application, MessageHandler, filters

from nanobot.channels.telegram import TelegramChannel


class CustomTelegramChannel(TelegramChannel):
    """Telegram channel with extended command support.

    Adds /ping command forwarding to the bus for E2E testing.
    """

    async def start(self) -> None:
        """Start the Telegram bot and add custom command handlers."""
        # We need to override start() to add the /ping handler before super().start() blocks
        if not self.config.token:
            from loguru import logger

            logger.error("Telegram bot token not configured")
            return

        from loguru import logger

        self._running = True

        # Build the application (copied from parent)
        from telegram.request import HTTPXRequest
        from telegram.ext import Application, CommandHandler, MessageHandler, filters

        req = HTTPXRequest(
            connection_pool_size=16, pool_timeout=5.0, connect_timeout=30.0, read_timeout=30.0
        )
        builder = (
            Application.builder().token(self.config.token).request(req).get_updates_request(req)
        )
        if self.config.proxy:
            builder = builder.proxy(self.config.proxy).get_updates_proxy(self.config.proxy)
        self._app = builder.build()
        self._app.add_error_handler(self._on_error)

        # Add command handlers (from parent)
        self._app.add_handler(CommandHandler("start", self._on_start))
        self._app.add_handler(CommandHandler("new", self._forward_command))
        self._app.add_handler(CommandHandler("help", self._on_help))

        # Add /ping handler to forward to bus (CUSTOM - must be added before polling starts!)
        self._app.add_handler(CommandHandler("ping", self._on_ping))
        # Also add handler for PING (case-insensitive test)
        self._app.add_handler(CommandHandler("PING", self._on_ping))

        # Add message handler for text, photos, voice, documents (from parent)
        self._app.add_handler(
            MessageHandler(
                (
                    filters.TEXT
                    | filters.PHOTO
                    | filters.VOICE
                    | filters.AUDIO
                    | filters.Document.ALL
                )
                & ~filters.COMMAND,
                self._on_message,
            )
        )

        logger.info("Starting Telegram bot (polling mode)...")

        # Initialize and start polling (from parent)
        await self._app.initialize()
        await self._app.start()

        # Get bot info and register command menu (from parent)
        bot_info = await self._app.bot.get_me()
        logger.info("Telegram bot @{} connected", bot_info.username)

        try:
            await self._app.bot.set_my_commands(self.BOT_COMMANDS)
            logger.debug("Telegram bot commands registered")
        except Exception as e:
            logger.warning("Failed to register bot commands: {}", e)

        # Start polling (this runs until stopped) (from parent)
        await self._app.updater.start_polling(
            allowed_updates=["message"],
            drop_pending_updates=True,  # Ignore old messages on startup
        )

        # Keep running until stopped (from parent)
        while self._running:
            import asyncio

            await asyncio.sleep(1)

    async def _on_ping(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /ping command by forwarding to bus."""
        if not update.message or not update.effective_user:
            return

        message = update.message
        user = update.effective_user

        # Remember thread context for message threading
        self._remember_thread_context(message)

        # Forward to message bus for agent processing
        await self._handle_message(
            sender_id=self._sender_id(user),
            chat_id=str(message.chat_id),
            content=message.text,
            metadata=self._build_message_metadata(message, user),
            session_key=self._derive_topic_session_key(message),
        )
