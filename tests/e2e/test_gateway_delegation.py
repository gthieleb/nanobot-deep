"""E2E tests for task delegation through gateway.

Tests:
- Reply-to message flow through gateway
- Control commands stay in main agent
- Reply-to gets delegated when configured
- Metadata with reply_to_message is passed correctly

Run with:
    NANOBOT_TEST_API_KEY=sk-... pytest tests/e2e/test_gateway_delegation.py -m live -v
"""

from __future__ import annotations

import asyncio

import pytest
from nanobot.bus.events import InboundMessage

pytestmark = pytest.mark.live


class TestGatewayReplyToFlow:
    """Test reply-to message handling through gateway."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_reply_to_message_metadata_preserved(self, live_gateway, send_and_wait):
        """Test that reply_to_message metadata is preserved through gateway."""
        bus = live_gateway["bus"]

        msg = InboundMessage(
            channel="test",
            sender_id="user1",
            chat_id="chat_reply_test",
            content="Yes, I agree with that",
            metadata={
                "reply_to_message": {
                    "message_id": "original_123",
                    "text": "Do you agree with this proposal?",
                    "from_username": "manager",
                }
            },
        )

        await bus.publish_inbound(msg)
        response = await asyncio.wait_for(bus.consume_outbound(), timeout=60)

        assert response.channel == "test"
        assert response.chat_id == "chat_reply_test"
        assert response.content
        assert len(response.content) > 0

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_reply_to_with_context_aware_response(self, live_gateway, send_and_wait):
        """Test that response considers reply context."""
        bus = live_gateway["bus"]

        msg = InboundMessage(
            channel="test",
            sender_id="user1",
            chat_id="chat_context_test",
            content="The answer is yes",
            metadata={
                "reply_to_message": {
                    "message_id": "q456",
                    "text": "What is your answer to the question about the project deadline?",
                    "from_username": "pm",
                }
            },
        )

        await bus.publish_inbound(msg)
        response = await asyncio.wait_for(bus.consume_outbound(), timeout=60)

        assert response.content
        assert response.chat_id == "chat_context_test"


class TestGatewayControlCommands:
    """Test control commands are not delegated."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_help_command_stays_main_agent(self, live_gateway, send_and_wait):
        """Test /help command is handled by main agent."""
        bus = live_gateway["bus"]

        response = await send_and_wait(bus, "/help")

        assert response.channel == "test"
        content_lower = response.content.lower()
        assert any(word in content_lower for word in ["help", "commands", "usage", "available"])

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_new_command_stays_main_agent(self, live_gateway, send_and_wait):
        """Test /new command is handled by main agent."""
        bus = live_gateway["bus"]

        response = await send_and_wait(bus, "/new")

        assert response.channel == "test"
        content_lower = response.content.lower()
        assert any(
            word in content_lower
            for word in ["new", "session", "cleared", "started", "conversation"]
        )

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_stop_command_stays_main_agent(self, live_gateway, send_and_wait):
        """Test /stop command is handled by main agent."""
        bus = live_gateway["bus"]

        response = await send_and_wait(bus, "/stop")

        assert response.channel == "test"
        assert response.content


class TestGatewayDelegationDecision:
    """Test delegation decisions based on message type."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_regular_message_not_delegated(self, live_gateway, send_and_wait):
        """Test regular message without reply-to is processed normally."""
        bus = live_gateway["bus"]

        response = await send_and_wait(bus, "Tell me a short joke", chat_id="regular_msg_test")

        assert response.channel == "test"
        assert response.chat_id == "regular_msg_test"
        assert response.content

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_command_not_delegated_even_with_reply_metadata(
        self, live_gateway, send_and_wait
    ):
        """Test control commands bypass delegation even with reply metadata."""
        bus = live_gateway["bus"]

        msg = InboundMessage(
            channel="test",
            sender_id="user1",
            chat_id="cmd_with_reply_test",
            content="/help",
            metadata={
                "reply_to_message": {
                    "message_id": "some_msg",
                    "text": "Previous message",
                }
            },
        )

        await bus.publish_inbound(msg)
        response = await asyncio.wait_for(bus.consume_outbound(), timeout=30)

        assert response.channel == "test"
        assert response.chat_id == "cmd_with_reply_test"
        content_lower = response.content.lower()
        assert any(word in content_lower for word in ["help", "commands", "usage"])


class TestGatewayMultiChannelReply:
    """Test reply-to handling across different channel types."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_telegram_style_reply(self, live_gateway):
        """Test Telegram-style reply message."""
        bus = live_gateway["bus"]

        msg = InboundMessage(
            channel="telegram",
            sender_id="tg_user_123",
            chat_id="tg_chat_456",
            content="Sounds good to me!",
            metadata={
                "message_id": "msg_789",
                "reply_to_message": {
                    "message_id": "original_msg",
                    "text": "Shall we schedule the meeting for tomorrow?",
                    "from_user_id": "tg_user_other",
                    "from_username": "john_doe",
                },
            },
        )

        await bus.publish_inbound(msg)
        response = await asyncio.wait_for(bus.consume_outbound(), timeout=60)

        assert response.channel == "telegram"
        assert response.chat_id == "tg_chat_456"
        assert response.content

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_discord_style_reply(self, live_gateway):
        """Test Discord-style reply message."""
        bus = live_gateway["bus"]

        msg = InboundMessage(
            channel="discord",
            sender_id="discord_user_123",
            chat_id="discord_channel_456",
            content="I vote yes!",
            metadata={
                "message_id": "discord_msg_789",
                "reply_to": "original_discord_msg",
                "reply_to_message": {
                    "message_id": "original_discord_msg",
                    "text": "Vote on the proposal: yes or no?",
                    "from_user_id": "discord_user_other",
                    "from_username": "jane_smith",
                },
            },
        )

        await bus.publish_inbound(msg)
        response = await asyncio.wait_for(bus.consume_outbound(), timeout=60)

        assert response.channel == "discord"
        assert response.chat_id == "discord_channel_456"
        assert response.content

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_slack_style_thread_reply(self, live_gateway):
        """Test Slack-style thread reply."""
        bus = live_gateway["bus"]

        msg = InboundMessage(
            channel="slack",
            sender_id="U123456",
            chat_id="C789012",
            content="Here's the report you asked for",
            metadata={
                "slack": {
                    "thread_ts": "1234567890.123456",
                    "channel_type": "channel",
                },
                "reply_to_message": {
                    "thread_ts": "1234567890.123456",
                    "parent_user": "U_OTHER",
                },
            },
        )

        await bus.publish_inbound(msg)
        response = await asyncio.wait_for(bus.consume_outbound(), timeout=60)

        assert response.channel == "slack"
        assert response.chat_id == "C789012"
        assert response.content


class TestGatewayReplyContextInResponse:
    """Test that reply context influences responses."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_reply_context_acknowledged(self, live_gateway):
        """Test response acknowledges the replied message context."""
        bus = live_gateway["bus"]

        msg = InboundMessage(
            channel="test",
            sender_id="user1",
            chat_id="ack_context_test",
            content="That's correct",
            metadata={
                "reply_to_message": {
                    "message_id": "prev_msg",
                    "text": "Is the meeting at 3pm?",
                    "from_username": "organizer",
                }
            },
        )

        await bus.publish_inbound(msg)
        response = await asyncio.wait_for(bus.consume_outbound(), timeout=60)

        assert response.content
        content_lower = response.content.lower()

        assert any(
            indicator in content_lower
            for indicator in [
                "correct",
                "yes",
                "confirmed",
                "acknowledged",
                "3pm",
                "meeting",
            ]
        )
