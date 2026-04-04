"""DeepAgent e2e tests with real LLM calls.

Tests the full message flow: inbound -> DeepAgent -> outbound

Run with:
    NANOBOT_TEST_API_KEY=sk-... pytest tests/e2e/test_deepagent_live.py -m live -v
"""

from __future__ import annotations

import asyncio

import pytest
from nanobot.bus.events import InboundMessage

pytestmark = pytest.mark.live


class TestDeepAgentBasic:
    """Basic DeepAgent functionality tests."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_simple_message(self, live_deep_gateway, send_and_wait):
        """Test basic message processing through DeepAgent."""
        bus = live_deep_gateway["bus"]

        response = await send_and_wait(bus, "Reply with exactly the word 'pong' and nothing else")

        assert response.channel == "test"
        assert response.chat_id == "chat1"
        assert "pong" in response.content.lower()

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_message_routing(self, live_deep_gateway):
        """Test message is routed to correct channel/chat."""
        bus = live_deep_gateway["bus"]

        await bus.publish_inbound(
            InboundMessage(
                channel="test_channel",
                sender_id="test_sender",
                chat_id="test_chat_123",
                content="Say 'hello'",
            )
        )

        response = await asyncio.wait_for(bus.consume_outbound(), timeout=30)

        assert response.channel == "test_channel"
        assert response.chat_id == "test_chat_123"
        assert "hello" in response.content.lower()


class TestDeepAgentSlashCommands:
    """Test slash commands through DeepAgent."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_help_command(self, live_deep_gateway, send_and_wait):
        """Test /help command."""
        bus = live_deep_gateway["bus"]

        response = await send_and_wait(bus, "/help")

        assert response.channel == "test"
        content_lower = response.content.lower()
        assert any(word in content_lower for word in ["help", "commands", "usage"])

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_new_command(self, live_deep_gateway, send_and_wait):
        """Test /new command clears session."""
        bus = live_deep_gateway["bus"]

        response = await send_and_wait(bus, "/new")

        assert response.channel == "test"
        content_lower = response.content.lower()
        assert any(word in content_lower for word in ["new", "session", "cleared", "started"])


class TestDeepAgentConversation:
    """Test conversation history and session persistence."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_remember_name(self, live_deep_gateway, send_and_wait):
        """Test agent remembers name across turns."""
        bus = live_deep_gateway["bus"]

        r1 = await send_and_wait(
            bus, "My name is Alice. Just acknowledge briefly.", chat_id="memory_test"
        )
        assert r1.content

        r2 = await send_and_wait(bus, "What is my name?", chat_id="memory_test")

        assert "alice" in r2.content.lower()

    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_session_isolation(self, live_deep_gateway, send_and_wait):
        """Test different sessions don't share context."""
        bus = live_deep_gateway["bus"]

        await send_and_wait(bus, "My name is Alice.", chat_id="session_a")
        await send_and_wait(bus, "My name is Bob.", chat_id="session_b")

        r_a = await send_and_wait(bus, "What is my name?", chat_id="session_a")
        r_b = await send_and_wait(bus, "What is my name?", chat_id="session_b")

        assert "alice" in r_a.content.lower()
        assert "bob" in r_b.content.lower()


class TestDeepAgentFileOperations:
    """Test file operations through DeepAgent."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(90)
    async def test_write_file(self, live_deep_gateway, workspace, send_and_wait):
        """Test writing a file through DeepAgent."""
        bus = live_deep_gateway["bus"]

        await send_and_wait(
            bus, "Create a file called test_write.txt with the content 'Written by DeepAgent'"
        )

        written_file = workspace / "test_write.txt"
        assert written_file.exists(), f"File not created in {workspace}"
        assert "Written by DeepAgent" in written_file.read_text()

    @pytest.mark.asyncio
    @pytest.mark.timeout(90)
    async def test_read_file(self, live_deep_gateway, workspace, send_and_wait):
        """Test reading a file through DeepAgent."""
        bus = live_deep_gateway["bus"]

        test_file = workspace / "test_read.txt"
        test_file.write_text("Hello from DeepAgent!")

        response = await send_and_wait(bus, "Read the file test_read.txt and tell me what it says")

        assert "Hello from DeepAgent" in response.content

    @pytest.mark.asyncio
    @pytest.mark.timeout(90)
    async def test_edit_file(self, live_deep_gateway, workspace, send_and_wait):
        """Test editing a file through DeepAgent."""
        bus = live_deep_gateway["bus"]

        test_file = workspace / "test_edit.txt"
        test_file.write_text("Original content here")

        await send_and_wait(
            bus, "Edit the file test_edit.txt and replace 'Original' with 'Modified'"
        )

        content = test_file.read_text()
        assert "Modified" in content
        assert "Original" not in content


class TestDeepAgentErrorHandling:
    """Test error handling in DeepAgent."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_handles_nonexistent_file(self, live_deep_gateway, send_and_wait):
        """Test DeepAgent handles non-existent file gracefully."""
        bus = live_deep_gateway["bus"]

        response = await send_and_wait(
            bus, "Try to read a file called nonexistent_file_12345.txt and report what happens"
        )

        content_lower = response.content.lower()
        assert any(
            word in content_lower
            for word in ["not found", "does not exist", "error", "cannot", "unable"]
        )


class TestDeepAgentDebugging:
    """Tests for debugging agent behavior."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_response_not_empty(self, live_deep_gateway, send_and_wait):
        """Test that response is not empty."""
        bus = live_deep_gateway["bus"]

        response = await send_and_wait(bus, "Say hello")

        assert response.content, "Response content should not be empty"
        assert len(response.content) > 0, "Response content should have length > 0"

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_response_channel_matches(self, live_deep_gateway, send_and_wait):
        """Test that response channel matches request channel."""
        bus = live_deep_gateway["bus"]

        response = await send_and_wait(
            bus, "Reply with OK", channel="debug_channel", chat_id="debug_chat"
        )

        assert response.channel == "debug_channel"
        assert response.chat_id == "debug_chat"

    @pytest.mark.asyncio
    @pytest.mark.timeout(90)
    async def test_agent_processes_tool_calls(self, live_deep_gateway, workspace, send_and_wait):
        """Test that agent can use tools successfully."""
        bus = live_deep_gateway["bus"]

        response = await send_and_wait(
            bus, "Create a file called debug_test.txt with content 'test passed'"
        )

        assert response.content, "Response should not be empty after tool use"

        debug_file = workspace / "debug_test.txt"
        assert debug_file.exists(), f"File should be created in {workspace}"
        assert "test passed" in debug_file.read_text()

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_agent_returns_proper_structure(self, live_deep_gateway, send_and_wait):
        """Test that response has proper OutboundMessage structure."""
        from nanobot.bus.events import OutboundMessage

        bus = live_deep_gateway["bus"]

        response = await send_and_wait(bus, "Reply with the word 'structure'")

        assert isinstance(response, OutboundMessage)
        assert hasattr(response, "channel")
        assert hasattr(response, "chat_id")
        assert hasattr(response, "content")
        assert hasattr(response, "metadata")
        assert response.channel is not None
        assert response.chat_id is not None
        assert response.content is not None

    @pytest.mark.asyncio
    @pytest.mark.timeout(90)
    async def test_agent_handles_multiline_response(self, live_deep_gateway, send_and_wait):
        """Test that agent can return multiline responses."""
        bus = live_deep_gateway["bus"]

        response = await send_and_wait(
            bus, "Write a short 3-line poem about robots. Each line on a new line."
        )

        assert "\n" in response.content or len(response.content) > 20, (
            "Response should be multiline or substantial"
        )

    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_agent_maintains_context_in_session(self, live_deep_gateway, send_and_wait):
        """Test that agent maintains context within a session."""
        bus = live_deep_gateway["bus"]

        await send_and_wait(bus, "Remember the secret code is ALPHA-123", chat_id="context_test")

        response = await send_and_wait(
            bus, "What is the secret code I just told you?", chat_id="context_test"
        )

        assert "alpha" in response.content.lower() or "123" in response.content

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_error_message_is_informative(self, live_deep_gateway, send_and_wait):
        """Test that error messages are informative when things fail."""
        bus = live_deep_gateway["bus"]

        response = await send_and_wait(
            bus, "Try to read a file that definitely does not exist: /nonexistent/path/xyz123.txt"
        )

        assert response.content, "Should have some response even on error"
        assert len(response.content) > 5, "Error message should be informative"
