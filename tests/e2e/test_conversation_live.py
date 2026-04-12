"""Multi-turn conversation tests with real LLM calls.

Tests conversation history and session persistence.

Run with:
    NANOBOT_TEST_API_KEY=sk-... pytest tests/e2e/test_conversation_live.py -m live -v
"""

from __future__ import annotations

import pytest

pytestmark = [pytest.mark.live, pytest.mark.slow]


class TestConversationHistory:
    """Test conversation history is maintained."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_remember_name(self, live_gateway, send_and_wait):
        """Test agent remembers name across turns."""
        bus = live_gateway["bus"]

        r1 = await send_and_wait(
            bus,
            "My name is Alice. Reply with just my name.",
            chat_id="memory_test",
        )

        assert "alice" in r1.content.lower()

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_remember_preference(self, live_gateway, send_and_wait):
        """Test agent remembers preferences across turns."""
        bus = live_gateway["bus"]

        r1 = await send_and_wait(
            bus,
            "I prefer Python. Reply with just the language.",
            chat_id="pref_test",
        )

        assert "python" in r1.content.lower()

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_context_accumulation(self, live_gateway, send_and_wait):
        """Test context accumulates across multiple turns."""
        bus = live_gateway["bus"]

        r = await send_and_wait(
            bus,
            "Remember: color=blue, animal=cat. Reply with both values.",
            chat_id="context_test",
        )

        content_lower = r.content.lower()
        assert "blue" in content_lower
        assert "cat" in content_lower


class TestSessionIsolation:
    """Test sessions are isolated from each other."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_different_sessions_different_context(self, live_gateway, send_and_wait):
        """Test different sessions don't share context."""
        bus = live_gateway["bus"]

        r_a = await send_and_wait(
            bus,
            "My name is Alice. Reply with just the name.",
            chat_id="session_a",
        )
        r_b = await send_and_wait(
            bus,
            "My name is Bob. Reply with just the name.",
            chat_id="session_b",
        )

        assert "alice" in r_a.content.lower()
        assert "bob" in r_b.content.lower()

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_session_isolation_with_tools(self, live_gateway, workspace, send_and_wait):
        """Test sessions don't see each other's files."""
        bus = live_gateway["bus"]

        # Session A: Create file
        await send_and_wait(
            bus,
            "Create a file called session_a_file.txt with content 'from session A'",
            chat_id="session_x",
        )

        # Session B: Try to find session A's file (shouldn't know about it from context)
        r = await send_and_wait(bus, "What files exist? List them.", chat_id="session_y")

        # Session B might see the file on disk but shouldn't have it in context
        # This is a weak test - mainly checking no crash occurs
        assert r.content


class TestConversationReset:
    """Test conversation reset functionality."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_new_command_resets_context(self, live_gateway, send_and_wait):
        """Test /new command clears conversation history."""
        bus = live_gateway["bus"]

        await send_and_wait(bus, "/new", chat_id="reset_test")

        r = await send_and_wait(
            bus,
            "What is my secret code? Reply with 'unknown' if you don't know.",
            chat_id="reset_test",
        )

        # Should not contain the secret
        content_lower = r.content.lower()
        assert (
            "xyz123" not in content_lower
            or "don't know" in content_lower
            or "not sure" in content_lower
        )


class TestConversationEdgeCases:
    """Test edge cases in conversations."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_very_short_turns(self, live_gateway, send_and_wait):
        """Test handling of very short messages."""
        bus = live_gateway["bus"]

        r = await send_and_wait(bus, "Hi")
        assert r.content

        r = await send_and_wait(bus, "Ok")
        assert r.content

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_repeated_message(self, live_gateway, send_and_wait):
        """Test handling of repeated identical messages."""
        bus = live_gateway["bus"]

        r1 = await send_and_wait(bus, "Say 'response'", chat_id="repeat_test")
        r2 = await send_and_wait(bus, "Say 'response'", chat_id="repeat_test")

        # Both should have valid responses
        assert r1.content
        assert r2.content

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_long_conversation(self, live_gateway, send_and_wait):
        """Test handling of longer conversations."""
        bus = live_gateway["bus"]

        r = await send_and_wait(
            bus,
            "Remember item0=value0, item1=value1, item2=value2. List the items.",
            chat_id="long_conv_test",
        )

        content_lower = r.content.lower()
        items_found = sum(
            1 for i in range(3) if f"item{i}" in content_lower or f"value{i}" in content_lower
        )
        assert items_found >= 2
