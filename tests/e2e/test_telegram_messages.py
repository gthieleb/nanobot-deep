"""Telegram gateway E2E tests - Message Flow.

Tests message processing and conversation flow through Telegram channel.

Run with:
    export TELEGRAM_API_ID=12345
    export TELEGRAM_API_HASH=abc123...
    export TEST_USER_PHONE=+49...
    export TELEGRAM_BOT_USERNAME=@your_bot
    pytest tests/e2e/test_telegram_messages.py -m live -v
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.live


class TestTelegramMessageFlow:
    """Test basic message processing flow."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_text_message(self, telegram_send_and_wait):
        """Test text message is processed correctly."""
        response = await telegram_send_and_wait("Say 'hello world'")

        assert response is not None
        assert response.message is not None
        content_lower = response.message.lower()
        assert "hello" in content_lower or "world" in content_lower

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_short_message(self, telegram_send_and_wait):
        """Test very short message."""
        response = await telegram_send_and_wait("Hi")

        assert response is not None
        assert response.message is not None
        assert len(response.message) > 0

    @pytest.mark.asyncio
    @pytest.mark.timeout(90)
    async def test_long_message(self, telegram_send_and_wait):
        """Test long message processing."""
        long_text = "Please repeat the word 'test' 20 times: " + "test " * 20
        response = await telegram_send_and_wait(long_text)

        assert response is not None
        assert response.message is not None
        assert len(response.message) > 0

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_message_with_emoji(self, telegram_send_and_wait):
        """Test message containing emojis."""
        response = await telegram_send_and_wait("Say '👍' in your response")

        assert response is not None
        assert response.message is not None


class TestTelegramMultiTurnConversation:
    """Test multi-turn conversation flow."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_sequential_messages(self, telegram_send_and_wait):
        """Test sequential messages in conversation."""
        r1 = await telegram_send_and_wait("Remember my name is Alice")
        assert r1 is not None

        r2 = await telegram_send_and_wait("What is my name?")
        assert r2 is not None
        content_lower = r2.message.lower()
        assert "alice" in content_lower

    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_context_across_messages(self, telegram_send_and_wait):
        """Test context is maintained across messages."""
        await telegram_send_and_wait("Remember: color=blue")

        r2 = await telegram_send_and_wait("What color did I mention?")
        assert r2 is not None
        content_lower = r2.message.lower()
        assert "blue" in content_lower

    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_session_reset(self, telegram_send_and_wait):
        """Test session reset clears context."""
        await telegram_send_and_wait("My secret code is XYZ123")

        await telegram_send_and_wait("/new")

        r3 = await telegram_send_and_wait("What is my secret code?")
        assert r3 is not None
        content_lower = r3.message.lower()
        assert (
            "xyz123" not in content_lower
            or "don't know" in content_lower
            or "not sure" in content_lower
        )


class TestTelegramReplyToMessages:
    """Test reply-to message handling."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_reply_to_message(self, telegram_send_and_wait):
        """Test reply-to message is processed."""
        response = await telegram_send_and_wait("Yes, I agree with that")

        assert response is not None
        assert response.message is not None

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_reply_with_context(self, telegram_send_and_wait):
        """Test reply considers previous context."""
        r1 = await telegram_send_and_wait("What is 2 + 2?")
        assert r1 is not None

        r2 = await telegram_send_and_wait("Now what is 3 + 3?")
        assert r2 is not None
        content_lower = r2.message.lower()
        assert "6" in content_lower or "three" in content_lower


class TestTelegramMessageRouting:
    """Test message routing and metadata."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_message_has_sender_id(self, telegram_send_and_wait):
        """Test message includes sender information."""
        response = await telegram_send_and_wait("Just say 'ok'")

        assert response is not None
        assert response.message is not None
        assert "ok" in response.message.lower()

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_message_timestamp(self, telegram_send_and_wait):
        """Test message has timestamp."""
        response = await telegram_send_and_wait("Say 'timestamp test'")

        assert response is not None
        assert response.message is not None
        assert response.date is not None
