"""Custom Telegram channel with /ping support and HITL interrupt handling."""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger
from nanobot.channels.telegram import TelegramChannel
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters
from telegram.request import HTTPXRequest

if TYPE_CHECKING:
    from telegram.ext import Application

from nanobot_deep.langgraph.interrupt_registry import (
    REGISTRY,
    PendingInterrupt,
    format_interrupt_message,
)


class CustomTelegramChannel(TelegramChannel):
    """Telegram channel with extended command support and HITL interrupts.

    Features:
    - /ping command for E2E testing
    - Inline approve/reject buttons for HITL interrupts
    - Automatic interrupt message sending when agent is interrupted
    """

    async def start(self) -> None:
        """Start the Telegram bot and add custom command handlers."""
        if not self.config.token:
            logger.error("Telegram bot token not configured")
            return

        self._running = True

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

        self._app.add_handler(CommandHandler("start", self._on_start))
        self._app.add_handler(CommandHandler("new", self._forward_command))
        self._app.add_handler(CommandHandler("stop", self._forward_command))
        self._app.add_handler(CommandHandler("status", self._forward_command))
        self._app.add_handler(CommandHandler("help", self._on_help))
        self._app.add_handler(CommandHandler("ping", self._on_ping))

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

        self._app.add_handler(CallbackQueryHandler(self._on_callback_query))

        logger.info("Starting Telegram bot (polling mode)...")

        await self._app.initialize()
        await self._app.start()

        if self._app is None:
            return

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

        await updater.start_polling(
            allowed_updates=["message", "callback_query"],
            drop_pending_updates=True,
        )

        while self._running:
            import asyncio

            await asyncio.sleep(1)

    async def _on_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle callback queries from inline buttons."""
        query = update.callback_query
        if not query:
            return

        data = query.data or ""
        if not data.startswith("hitl:"):
            return

        parts = data.split(":", 2)
        if len(parts) < 3:
            await query.answer("Invalid callback data")
            return

        _, tool_call_id, action = parts

        interrupt_obj = await REGISTRY.get(tool_call_id)
        if not interrupt_obj:
            await query.answer("Interrupt expired or not found")
            return

        if action == "approve":
            await REGISTRY.resolve(tool_call_id, "approve")
            await query.answer("Approved!")
            await query.edit_message_reply_markup(reply_markup=None)
            try:
                if query.message:
                    await query.message.edit_text(
                        text=query.message.text + "\n\n✅ <b>Approved</b>",
                        parse_mode="HTML",
                    )
            except Exception as e:
                logger.debug(f"Failed to edit message: {e}")

        elif action == "reject":
            await REGISTRY.resolve(tool_call_id, "reject", message="User rejected the action")
            await query.answer("Rejected")
            await query.edit_message_reply_markup(reply_markup=None)
            try:
                if query.message:
                    await query.message.edit_text(
                        text=query.message.text + "\n\n❌ <b>Rejected</b>",
                        parse_mode="HTML",
                    )
            except Exception as e:
                logger.debug(f"Failed to edit message: {e}")

        elif action == "edit":
            await query.answer("Edit not implemented yet - treating as reject")
            await REGISTRY.resolve(
                tool_call_id, "reject", message="Edit feature not yet implemented"
            )
            await query.edit_message_reply_markup(reply_markup=None)
        else:
            await query.answer(f"Unknown action: {action}")

    def _build_interrupt_keyboard(
        self, tool_call_id: str, allowed_decisions: list[str]
    ) -> InlineKeyboardMarkup:
        """Build inline keyboard for HITL interrupt."""
        keyboard: list[list[InlineKeyboardButton]] = []

        buttons = []
        if "approve" in allowed_decisions:
            buttons.append(
                InlineKeyboardButton("✅ Approve", callback_data=f"hitl:{tool_call_id}:approve")
            )
        if "edit" in allowed_decisions:
            buttons.append(
                InlineKeyboardButton("✏️ Edit", callback_data=f"hitl:{tool_call_id}:edit")
            )
        if "reject" in allowed_decisions:
            buttons.append(
                InlineKeyboardButton("❌ Reject", callback_data=f"hitl:{tool_call_id}:reject")
            )

        if buttons:
            keyboard.append(buttons)

        return InlineKeyboardMarkup(keyboard)

    async def send_interrupt(
        self,
        chat_id: str,
        interrupt: PendingInterrupt,
    ) -> int | None:
        """Send an interrupt message with inline buttons.

        Args:
            chat_id: Telegram chat ID
            interrupt: The pending interrupt

        Returns:
            Message ID if sent successfully, None otherwise
        """
        if not self._app:
            logger.warning("Telegram bot not running - cannot send interrupt")
            return None

        try:
            chat_id_int = int(chat_id)
        except ValueError:
            logger.error("Invalid chat_id: {}", chat_id)
            return None

        message_text = await format_interrupt_message(interrupt)
        keyboard = self._build_interrupt_keyboard(
            interrupt.tool_call_id, interrupt.allowed_decisions
        )

        try:
            message = await self._app.bot.send_message(
                chat_id=chat_id_int,
                text=message_text,
                parse_mode="HTML",
                reply_markup=keyboard,
            )
            REGISTRY.set_message_id(interrupt.tool_call_id, message.message_id)
            logger.info(
                "Sent HITL interrupt for tool {} to chat {}",
                interrupt.tool_name,
                chat_id,
            )
            return message.message_id
        except Exception as e:
            logger.error("Failed to send interrupt message: {}", e)
            return None

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
