from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from nanobot_deep.channels.telegram import CustomTelegramChannel


class TestCustomTelegramChannel:
    def test_is_ping_text(self):
        assert CustomTelegramChannel._is_ping_text("/ping")
        assert CustomTelegramChannel._is_ping_text("/ping@my_bot")
        assert CustomTelegramChannel._is_ping_text("/PING@my_bot test")
        assert not CustomTelegramChannel._is_ping_text("ping")
        assert not CustomTelegramChannel._is_ping_text("/pings")

    @pytest.mark.asyncio
    async def test_on_message_handles_ping_text(self):
        channel = object.__new__(CustomTelegramChannel)
        message = SimpleNamespace(text="/ping@my_bot", reply_text=AsyncMock())
        update = SimpleNamespace(message=message)

        with patch("nanobot.channels.telegram.TelegramChannel._on_message", new=AsyncMock()):
            await channel._on_message(update, None)

        message.reply_text.assert_awaited_once_with("pong")

    @pytest.mark.asyncio
    async def test_on_message_forwards_non_ping(self):
        channel = object.__new__(CustomTelegramChannel)
        message = SimpleNamespace(text="hello", reply_text=AsyncMock())
        update = SimpleNamespace(message=message)
        super_on_message = AsyncMock()

        with patch("nanobot.channels.telegram.TelegramChannel._on_message", new=super_on_message):
            await channel._on_message(update, None)

        super_on_message.assert_awaited_once_with(update, None)
        message.reply_text.assert_not_called()
