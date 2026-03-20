"""Telegram gateway E2E tests - Error Handling.

Tests error handling and edge cases through Telegram channel.

Run with:
    export TELEGRAM_API_ID=12345
    export TELEGRAM_API_HASH=abc123...
    export TEST_USER_PHONE=+49...
    export TELEGRAM_BOT_USERNAME=@your_bot
    pytest tests/e2e/test_telegram_errors.py -m live -v
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.live


class TestTelegramEmptyMessages:
    """Test handling of empty or whitespace messages."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_empty_message(self, telegram_send_and_wait):
        """Test completely empty message."""
        response = await telegram_send_and_wait("")

        assert response is not None
        assert response.message is not None

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_whitespace_only(self, telegram_send_and_wait):
        """Test message with only whitespace."""
        response = await telegram_send_and_wait("   ")

        assert response is not None
        assert response.message is not None

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_newlines_only(self, telegram_send_and_wait):
        """Test message with only newlines."""
        response = await telegram_send_and_wait("\n\n\n")

        assert response is not None
        assert response.message is not None


class TestTelegramInvalidInput:
    """Test handling of invalid or malformed input."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_special_characters(self, telegram_send_and_wait):
        """Test message with many special characters."""
        response = await telegram_send_and_wait("!@#$%^&*()_+-=[]{}|;':\",./<>?")

        assert response is not None
        assert response.message is not None

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_unicode_characters(self, telegram_send_and_wait):
        """Test message with unicode characters."""
        response = await telegram_send_and_wait("こんにちは 世界 مرحبا")

        assert response is not None
        assert response.message is not None

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_repeated_command(self, telegram_send_and_wait):
        """Test repeated command spam."""
        response1 = await telegram_send_and_wait("/ping")
        assert response1 is not None

        response2 = await telegram_send_and_wait("/ping")
        assert response2 is not None

        response3 = await telegram_send_and_wait("/ping")
        assert response3 is not None


class TestTelegramTimeoutHandling:
    """Test timeout and slow response handling."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(90)
    async def test_slow_query(self, telegram_send_and_wait):
        """Test bot handles slow queries."""
        response = await telegram_send_and_wait("Think carefully and count to 10 in your response")

        assert response is not None
        assert response.message is not None

    @pytest.mark.asyncio
    @pytest.mark.timeout(90)
    async def test_complex_calculation(self, telegram_send_and_wait):
        """Test bot handles complex requests."""
        response = await telegram_send_and_wait(
            "Calculate the factorial of 5 and explain each step"
        )

        assert response is not None
        assert response.message is not None


class TestTelegramLargeMessages:
    """Test handling of large messages."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(90)
    async def test_very_long_message(self, telegram_send_and_wait):
        """Test very long input message."""
        long_message = "Test: " + "word " * 500
        response = await telegram_send_and_wait(long_message)

        assert response is not None
        assert response.message is not None

    @pytest.mark.asyncio
    @pytest.mark.timeout(90)
    async def test_long_response(self, telegram_send_and_wait):
        """Test bot can send long responses."""
        response = await telegram_send_and_wait(
            "Write a detailed paragraph about artificial intelligence"
        )

        assert response is not None
        assert response.message is not None
        assert len(response.message) > 100


class TestTelegramEdgeCases:
    """Test various edge cases."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_single_word(self, telegram_send_and_wait):
        """Test single word message."""
        response = await telegram_send_and_wait("hello")

        assert response is not None
        assert response.message is not None

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_question_only(self, telegram_send_and_wait):
        """Test question mark only."""
        response = await telegram_send_and_wait("?")

        assert response is not None
        assert response.message is not None

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_numbers_only(self, telegram_send_and_wait):
        """Test numbers only."""
        response = await telegram_send_and_wait("12345")

        assert response is not None
        assert response.message is not None

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_url_only(self, telegram_send_and_wait):
        """Test URL only."""
        response = await telegram_send_and_wait("https://example.com")

        assert response is not None
        assert response.message is not None


class TestTelegramErrorMessages:
    """Test that errors are handled gracefully."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_invalid_tool_request(self, telegram_send_and_wait):
        """Test request for non-existent tool."""
        response = await telegram_send_and_wait(
            "Just say 'I cannot do that' - do not try to use any tools"
        )

        assert response is not None
        assert response.message is not None
        content_lower = response.message.lower()
        assert "error" not in content_lower or "cannot" in content_lower

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_malformed_json(self, telegram_send_and_wait):
        """Test malformed JSON in message."""
        response = await telegram_send_and_wait('{"invalid": json}')

        assert response is not None
        assert response.message is not None

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_code_block_only(self, telegram_send_and_wait):
        """Test message with only code block."""
        response = await telegram_send_and_wait("```python\n```")

        assert response is not None
        assert response.message is not None
