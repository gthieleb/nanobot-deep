"""Unit tests for bridge.py message translation functions."""

from __future__ import annotations

import pytest

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage


class TestTranslateInboundToState:
    """Tests for translate_inbound_to_state function."""

    def test_simple_text_message(self):
        """Test basic text message conversion."""
        from nanobot.bus.events import InboundMessage
        from nanobot_deep.langgraph.bridge import translate_inbound_to_state

        msg = InboundMessage(
            channel="telegram",
            sender_id="user123",
            chat_id="chat456",
            content="Hello, world!",
        )

        state = translate_inbound_to_state(msg)

        assert "messages" in state
        assert len(state["messages"]) == 1
        assert isinstance(state["messages"][0], HumanMessage)
        assert state["messages"][0].content == "Hello, world!"

    def test_message_with_system_prompt(self):
        """Test message with system prompt prepended."""
        from nanobot.bus.events import InboundMessage
        from nanobot_deep.langgraph.bridge import translate_inbound_to_state

        msg = InboundMessage(
            channel="cli",
            sender_id="user",
            chat_id="test",
            content="Test message",
        )

        state = translate_inbound_to_state(msg, system_prompt="You are a helpful assistant.")

        assert len(state["messages"]) == 2
        assert isinstance(state["messages"][0], SystemMessage)
        assert state["messages"][0].content == "You are a helpful assistant."
        assert isinstance(state["messages"][1], HumanMessage)

    def test_message_with_history(self):
        """Test message with conversation history."""
        from nanobot.bus.events import InboundMessage
        from nanobot_deep.langgraph.bridge import translate_inbound_to_state

        msg = InboundMessage(
            channel="test",
            sender_id="user",
            chat_id="chat",
            content="What about now?",
        )

        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]

        state = translate_inbound_to_state(msg, history=history)

        assert len(state["messages"]) == 3
        assert isinstance(state["messages"][0], HumanMessage)
        assert state["messages"][0].content == "Hello"
        assert isinstance(state["messages"][1], AIMessage)
        assert state["messages"][1].content == "Hi there!"
        assert isinstance(state["messages"][2], HumanMessage)

    def test_message_with_reply_context(self):
        """Test message with reply-to context."""
        from nanobot.bus.events import InboundMessage
        from nanobot_deep.langgraph.bridge import translate_inbound_to_state

        msg = InboundMessage(
            channel="telegram",
            sender_id="user123",
            chat_id="chat456",
            content="Yes, I agree",
        )

        reply_context = {
            "text": "Do you agree with this proposal?",
            "from_username": "manager",
        }

        state = translate_inbound_to_state(msg, reply_context=reply_context)

        assert len(state["messages"]) == 2
        assert isinstance(state["messages"][0], SystemMessage)
        assert "manager" in state["messages"][0].content
        assert "Do you agree with this proposal?" in state["messages"][0].content


class TestTranslateResultToOutbound:
    """Tests for translate_result_to_outbound function."""

    def test_simple_ai_response(self):
        """Test converting simple AI response."""
        from nanobot.bus.events import InboundMessage
        from nanobot_deep.langgraph.bridge import translate_result_to_outbound

        msg = InboundMessage(
            channel="telegram",
            sender_id="user123",
            chat_id="chat456",
            content="Hello",
        )

        result = {
            "messages": [
                HumanMessage(content="Hello"),
                AIMessage(content="Hi there! How can I help you?"),
            ]
        }

        outbound = translate_result_to_outbound(result, msg)

        assert outbound.channel == "telegram"
        assert outbound.chat_id == "chat456"
        assert outbound.content == "Hi there! How can I help you?"

    def test_result_with_tool_messages(self):
        """Test result with tool messages finds AI response."""
        from nanobot.bus.events import InboundMessage
        from langchain_core.messages import ToolCall
        from nanobot_deep.langgraph.bridge import translate_result_to_outbound

        msg = InboundMessage(
            channel="test",
            sender_id="user",
            chat_id="chat",
            content="Read the file",
        )

        result = {
            "messages": [
                HumanMessage(content="Read the file"),
                AIMessage(
                    content="",
                    tool_calls=[
                        ToolCall(name="read_file", args={"path": "test.txt"}, id="call_123")
                    ],
                ),
                ToolMessage(content="File contents here", tool_call_id="call_123"),
                AIMessage(content="The file contains: File contents here"),
            ]
        }

        outbound = translate_result_to_outbound(result, msg)

        assert outbound.content == "The file contains: File contents here"

    def test_empty_result(self):
        """Test handling of empty result."""
        from nanobot.bus.events import InboundMessage
        from nanobot_deep.langgraph.bridge import translate_result_to_outbound

        msg = InboundMessage(
            channel="test",
            sender_id="user",
            chat_id="chat",
            content="Test",
        )

        result = {"messages": []}

        outbound = translate_result_to_outbound(result, msg)

        assert outbound.content == ""

    def test_preserves_metadata(self):
        """Test that metadata is preserved in outbound."""
        from nanobot.bus.events import InboundMessage
        from nanobot_deep.langgraph.bridge import translate_result_to_outbound

        msg = InboundMessage(
            channel="test",
            sender_id="user",
            chat_id="chat",
            content="Test",
            metadata={"original_message_id": "msg123"},
        )

        result = {"messages": [AIMessage(content="Response")]}

        outbound = translate_result_to_outbound(result, msg)

        assert outbound.metadata.get("original_message_id") == "msg123"


class TestExtractReplyContext:
    """Tests for extract_reply_context function."""

    def test_no_metadata(self):
        """Test message without metadata."""
        from nanobot.bus.events import InboundMessage
        from nanobot_deep.langgraph.bridge import extract_reply_context

        msg = InboundMessage(
            channel="test",
            sender_id="user",
            chat_id="chat",
            content="Hello",
        )

        assert extract_reply_context(msg) is None

    def test_with_reply_context(self):
        """Test message with reply context."""
        from nanobot.bus.events import InboundMessage
        from nanobot_deep.langgraph.bridge import extract_reply_context

        msg = InboundMessage(
            channel="telegram",
            sender_id="user123",
            chat_id="chat456",
            content="Yes",
            metadata={
                "reply_to_message": {
                    "message_id": "orig_123",
                    "text": "Question?",
                    "from_username": "other_user",
                }
            },
        )

        context = extract_reply_context(msg)

        assert context is not None
        assert context["text"] == "Question?"
        assert context["from_username"] == "other_user"


class TestShouldDelegateTask:
    """Tests for should_delegate_task function."""

    def test_control_command_not_delegated(self):
        """Test control commands are not delegated."""
        from nanobot.bus.events import InboundMessage
        from nanobot_deep.langgraph.bridge import should_delegate_task

        msg = InboundMessage(
            channel="test",
            sender_id="user",
            chat_id="chat",
            content="/help",
        )

        should, delegate_type = should_delegate_task(
            msg, control_commands=["/help", "/new", "/stop"]
        )

        assert should is False
        assert delegate_type == "control"

    def test_reply_message_delegated(self):
        """Test reply messages are delegated when enabled."""
        from nanobot.bus.events import InboundMessage
        from nanobot_deep.langgraph.bridge import should_delegate_task

        msg = InboundMessage(
            channel="telegram",
            sender_id="user",
            chat_id="chat",
            content="Yes, I agree",
            metadata={
                "reply_to_message": {
                    "text": "Do you agree?",
                }
            },
        )

        should, delegate_type = should_delegate_task(
            msg, control_commands=["/help"], auto_delegate_reply=True
        )

        assert should is True
        assert delegate_type == "reply"

    def test_reply_delegation_disabled(self):
        """Test reply messages not delegated when disabled."""
        from nanobot.bus.events import InboundMessage
        from nanobot_deep.langgraph.bridge import should_delegate_task

        msg = InboundMessage(
            channel="test",
            sender_id="user",
            chat_id="chat",
            content="Yes",
            metadata={"reply_to_message": {"text": "Question?"}},
        )

        should, delegate_type = should_delegate_task(
            msg, control_commands=[], auto_delegate_reply=False
        )

        assert should is False
        assert delegate_type == "main"

    def test_regular_message_not_delegated(self):
        """Test regular messages are not delegated."""
        from nanobot.bus.events import InboundMessage
        from nanobot_deep.langgraph.bridge import should_delegate_task

        msg = InboundMessage(
            channel="test",
            sender_id="user",
            chat_id="chat",
            content="Tell me a joke",
        )

        should, delegate_type = should_delegate_task(msg, control_commands=["/help", "/new"])

        assert should is False
        assert delegate_type == "main"


class TestFullMessageFlow:
    """Tests for complete message flow through bridge functions."""

    def test_inbound_to_outbound_roundtrip(self):
        """Test complete roundtrip: InboundMessage -> State -> Result -> OutboundMessage."""
        from nanobot.bus.events import InboundMessage
        from nanobot_deep.langgraph.bridge import (
            translate_inbound_to_state,
            translate_result_to_outbound,
        )

        msg = InboundMessage(
            channel="telegram",
            sender_id="tg_user_123",
            chat_id="tg_chat_456",
            content="What is the weather?",
            metadata={"user_name": "Alice"},
        )

        state = translate_inbound_to_state(msg)

        result = {
            "messages": [
                state["messages"][0],
                AIMessage(content="I don't have access to weather data."),
            ]
        }

        outbound = translate_result_to_outbound(result, msg)

        assert outbound.channel == "telegram"
        assert outbound.chat_id == "tg_chat_456"
        assert "weather" in outbound.content.lower()
        assert outbound.metadata.get("user_name") == "Alice"


class TestEdgeCases:
    """Tests for edge cases in message translation."""

    def test_empty_content(self):
        """Test handling of empty message content."""
        from nanobot.bus.events import InboundMessage
        from nanobot_deep.langgraph.bridge import translate_inbound_to_state

        msg = InboundMessage(
            channel="test",
            sender_id="user",
            chat_id="chat",
            content="",
        )

        state = translate_inbound_to_state(msg)

        assert len(state["messages"]) == 1
        assert state["messages"][0].content == ""

    def test_very_long_content(self):
        """Test handling of very long message content."""
        from nanobot.bus.events import InboundMessage
        from nanobot_deep.langgraph.bridge import translate_inbound_to_state

        long_content = "x" * 10000
        msg = InboundMessage(
            channel="test",
            sender_id="user",
            chat_id="chat",
            content=long_content,
        )

        state = translate_inbound_to_state(msg)

        assert len(state["messages"]) == 1
        assert state["messages"][0].content == long_content

    def test_special_characters_in_content(self):
        """Test handling of special characters in content."""
        from nanobot.bus.events import InboundMessage
        from nanobot_deep.langgraph.bridge import translate_inbound_to_state

        special_content = "Hello\n\tWorld! @#$%^&*() 你好"
        msg = InboundMessage(
            channel="test",
            sender_id="user",
            chat_id="chat",
            content=special_content,
        )

        state = translate_inbound_to_state(msg)

        assert state["messages"][0].content == special_content

    def test_tool_message_in_history(self):
        """Test handling of tool messages in history."""
        from nanobot.bus.events import InboundMessage
        from nanobot_deep.langgraph.bridge import translate_inbound_to_state

        msg = InboundMessage(
            channel="test",
            sender_id="user",
            chat_id="chat",
            content="What happened?",
        )

        history = [
            {"role": "user", "content": "Read file"},
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [{"id": "call_1", "name": "read_file", "args": {"path": "test.txt"}}],
            },
            {"role": "tool", "content": "File contents", "tool_call_id": "call_1"},
        ]

        state = translate_inbound_to_state(msg, history=history)

        assert len(state["messages"]) == 4
        assert isinstance(state["messages"][2], ToolMessage)

    def test_result_with_only_tool_message(self):
        """Test result that only has tool messages, no AI response."""
        from nanobot.bus.events import InboundMessage
        from nanobot_deep.langgraph.bridge import translate_result_to_outbound

        msg = InboundMessage(
            channel="test",
            sender_id="user",
            chat_id="chat",
            content="Test",
        )

        result = {
            "messages": [
                HumanMessage(content="Test"),
                ToolMessage(content="Tool output", tool_call_id="call_1"),
            ]
        }

        outbound = translate_result_to_outbound(result, msg)

        assert outbound.channel == "test"
        assert outbound.chat_id == "chat"

    def test_result_with_non_message_objects(self):
        """Test result with objects that have content attribute."""
        from nanobot.bus.events import InboundMessage
        from nanobot_deep.langgraph.bridge import translate_result_to_outbound

        msg = InboundMessage(
            channel="test",
            sender_id="user",
            chat_id="chat",
            content="Test",
        )

        class FakeMessage:
            content = "Fake response"

        result = {"messages": [FakeMessage()]}

        outbound = translate_result_to_outbound(result, msg)

        assert outbound.content == "Fake response"
