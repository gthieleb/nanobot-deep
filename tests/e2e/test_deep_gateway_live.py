"""E2E tests for DeepAgent gateway with real LLM calls.

Tests the full message flow: inbound -> DeepAgent -> outbound

Run with:
    NANOBOT_TEST_API_KEY=sk-... NANOBOT_TEST_MODEL=gpt-5-mini pytest tests/e2e/test_deep_gateway_live.py -m live -v
"""

from __future__ import annotations

import asyncio

import pytest
from nanobot.bus.events import InboundMessage

pytestmark = pytest.mark.live


class TestDeepAgentDirect:
    """Tests for DeepAgent direct processing."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_direct_process_simple(self, live_deep_agent):
        """Test basic message processing with DeepAgent."""
        agent = live_deep_agent

        from nanobot.bus.events import InboundMessage

        msg = InboundMessage(
            channel="test",
            sender_id="user1",
            chat_id="chat1",
            content="Reply with exactly the word 'pong' and nothing else",
        )

        response = await agent.process(msg)

        assert response.channel == "test"
        assert response.chat_id == "chat1"
        assert "pong" in response.content.lower()

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_direct_process_with_session(self, live_deep_agent):
        """Test session persistence across messages."""
        agent = live_deep_agent

        from nanobot.bus.events import InboundMessage

        msg1 = InboundMessage(
            channel="test",
            sender_id="user1",
            chat_id="session_test",
            content="My name is Alice. Remember this.",
        )
        response1 = await agent.process(msg1)
        assert response1.content

        msg2 = InboundMessage(
            channel="test",
            sender_id="user1",
            chat_id="session_test",
            content="What is my name?",
        )
        response2 = await agent.process(msg2)

        assert "alice" in response2.content.lower()


class TestDeepGatewayBus:
    """Tests for DeepGateway message bus integration."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_bus_message_flow(self, live_deep_gateway, deep_send_and_wait):
        """Test message flows through bus correctly."""
        bus = live_deep_gateway["bus"]

        response = await deep_send_and_wait(
            bus,
            "Reply with exactly the word 'hello' and nothing else",
        )

        assert response.channel == "test"
        assert response.chat_id == "chat1"
        assert "hello" in response.content.lower()

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_bus_routing_preserved(self, live_deep_gateway):
        """Test channel and chat_id are preserved in response."""
        bus = live_deep_gateway["bus"]

        await bus.publish_inbound(
            InboundMessage(
                channel="custom_channel",
                sender_id="test_sender",
                chat_id="custom_chat_123",
                content="Say 'response'",
            )
        )

        response = await asyncio.wait_for(bus.consume_outbound(), timeout=30)

        assert response.channel == "custom_channel"
        assert response.chat_id == "custom_chat_123"

    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_multiple_sessions(self, live_deep_gateway, deep_send_and_wait):
        """Test multiple sessions are isolated."""
        bus = live_deep_gateway["bus"]

        r1 = await deep_send_and_wait(bus, "My secret is alpha123", chat_id="session_a")
        assert r1.content

        r2 = await deep_send_and_wait(bus, "My secret is beta456", chat_id="session_b")
        assert r2.content

        r1_check = await deep_send_and_wait(bus, "What is my secret?", chat_id="session_a")
        assert "alpha123" in r1_check.content.lower()
        assert "beta456" not in r1_check.content.lower()

        r2_check = await deep_send_and_wait(bus, "What is my secret?", chat_id="session_b")
        assert "beta456" in r2_check.content.lower()
        assert "alpha123" not in r2_check.content.lower()


class TestDeepAgentTools:
    """Tests for DeepAgent tool usage."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_file_operations(self, live_deep_agent, workspace):
        """Test DeepAgent can perform file operations."""
        from nanobot.bus.events import InboundMessage

        msg = InboundMessage(
            channel="test",
            sender_id="user1",
            chat_id="tool_test",
            content=f"Create a file called 'test_file.txt' in {workspace} with content 'Hello from DeepAgent'",
        )

        response = await live_deep_agent.process(msg)

        assert response.content

        file_path = workspace / "test_file.txt"
        assert (
            file_path.exists()
            or "created" in response.content.lower()
            or "wrote" in response.content.lower()
        )


class TestDeepAgentEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_empty_message(self, live_deep_agent):
        """Test handling of empty/whitespace messages."""
        from nanobot.bus.events import InboundMessage

        msg = InboundMessage(
            channel="test",
            sender_id="user1",
            chat_id="edge_test",
            content="   Say 'ok'   ",
        )

        response = await live_deep_agent.process(msg)

        assert response.content
        assert len(response.content) > 0

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_very_long_message(self, live_deep_agent):
        """Test handling of very long messages."""
        from nanobot.bus.events import InboundMessage

        long_content = "Repeat after me: " + "hello " * 50

        msg = InboundMessage(
            channel="test",
            sender_id="user1",
            chat_id="long_test",
            content=long_content,
        )

        response = await live_deep_agent.process(msg)

        assert response.content

        import os

        file_path = workspace / "test_file.txt"
        assert (
            file_path.exists()
            or "created" in response.content.lower()
            or "wrote" in response.content.lower()
        )


class TestDeepAgentEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_empty_message(self, live_deep_agent):
        """Test handling of empty/whitespace messages."""
        from nanobot.bus.events import InboundMessage

        msg = InboundMessage(
            channel="test",
            sender_id="user1",
            chat_id="edge_test",
            content="   Say 'ok'   ",
        )

        response = await agent.process(msg) if False else await live_deep_agent.process(msg)

        assert response.content
        assert len(response.content) > 0

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_very_long_message(self, live_deep_agent):
        """Test handling of very long messages."""
        from nanobot.bus.events import InboundMessage

        long_content = "Repeat after me: " + "hello " * 50

        msg = InboundMessage(
            channel="test",
            sender_id="user1",
            chat_id="long_test",
            content=long_content,
        )

        response = await agent.process(msg) if False else await live_deep_agent.process(msg)

        assert response.content
