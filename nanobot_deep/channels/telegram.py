"""Custom Telegram channel with /ping support for E2E tests."""

from telegram import Update
from telegram.request import HTTPXRequest
from telegram.ext import Application, MessageHandler, filters
from telegram.ext import CommandHandler, ContextTypes

from nanobot.channels.telegram import TelegramChannel


class CustomTelegramChannel(TelegramChannel):
    """Telegram channel with extended command support.

    Adds /ping command handling for E2E testing.
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
        self._app.add_handler(CommandHandler("stop", self._forward_command))
        self._app.add_handler(CommandHandler("help", self._on_help))

        # Add /ping handler (CUSTOM - must be added before polling starts!)
        self._app.add_handler(CommandHandler("ping", self._on_ping))

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

        if self._app is None:
            return

        # Get bot info and register command menu (from parent)
        bot_info = await self._app.bot.get_me()
        logger.info("Telegram bot @{} connected", bot_info.username)

        try:
            await self._app.bot.set_my_commands(self.BOT_COMMANDS)
            logger.debug("Telegram bot commands registered")
        except Exception as e:
            logger.warning("Failed to register bot commands: {}", e)

        updater = self._app.updater
        if updater is None:
            return

        # Start polling (this runs until stopped) (from parent)
        await updater.start_polling(
            allowed_updates=["message"],
            drop_pending_updates=True,  # Ignore old messages on startup
        )

        # Keep running until stopped (from parent)
        while self._running:
            import asyncio

            await asyncio.sleep(1)

    async def _on_ping(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /ping command."""
        if not update.message:
            return
        await update.message.reply_text("pong")

    @staticmethod
    def _is_ping_text(content: str | None) -> bool:
        if not content:
            return False
        command = content.strip().split(" ", 1)[0]
        if not command.startswith("/"):
            return False
        command_name = command[1:].split("@", 1)[0]
        return command_name.lower() == "ping"

    async def _on_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.message and self._is_ping_text(update.message.text):
            await update.message.reply_text("pong")
            return
        await super()._on_message(update, context)
