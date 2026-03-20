"""Telegram gateway E2E tests - Basic Commands.

Tests basic slash commands through Telegram channel.

Run with:
    export TELEGRAM_API_ID=12345
    export TELEGRAM_API_HASH=abc123...
    export TEST_USER_PHONE=+49...
    export TELEGRAM_BOT_USERNAME=@your_bot
    pytest tests/e2e/test_telegram_basic.py -m live -v
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.live


class TestTelegramBasicCommands:
    """Test basic Telegram bot commands."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_ping_command(self, telegram_send_and_wait):
        """Test /ping command returns pong."""
        response = await telegram_send_and_wait("/ping")

        assert response is not None
        assert response.message is not None
        assert "pong" in response.message.lower()

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_help_command(self, telegram_send_and_wait):
        """Test /help command shows help text."""
        response = await telegram_send_and_wait("/help")

        assert response is not None
        assert response.message is not None
        content_lower = response.message.lower()
        assert any(word in content_lower for word in ["help", "commands", "usage", "available"])

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_new_command(self, telegram_send_and_wait):
        """Test /new command clears session."""
        response = await telegram_send_and_wait("/new")

        assert response is not None
        assert response.message is not None
        content_lower = response.message.lower()
        assert any(
            word in content_lower
            for word in ["new", "session", "cleared", "started", "conversation"]
        )

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_stop_command(self, telegram_send_and_wait):
        """Test /stop command stops session."""
        response = await telegram_send_and_wait("/stop")

        assert response is not None
        assert response.message is not None


class TestTelegramUnknownCommand:
    """Test handling of unknown/invalid commands."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_unknown_command(self, telegram_send_and_wait):
        """Test unknown command returns appropriate message."""
        response = await telegram_send_and_wait("/unknown_command_xyz")

        assert response is not None
        assert response.message is not None

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_invalid_slash_command(self, telegram_send_and_wait):
        """Test invalid slash command format."""
        response = await telegram_send_and_wait("/")

        assert response is not None
        assert response.message is not None


class TestTelegramSpecialCharacters:
    """Test handling of special characters in commands."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_command_with_args(self, telegram_send_and_wait):
        """Test command with arguments."""
        response = await telegram_send_and_wait("/help test")

        assert response is not None
        assert response.message is not None
        content_lower = response.message.lower()
        assert any(word in content_lower for word in ["help", "commands"])

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_command_case_sensitive(self, telegram_send_and_wait):
        """Test command case sensitivity."""
        response = await telegram_send_and_wait("/PING")

        assert response is not None
        assert response.message is not None
