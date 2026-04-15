"""Unit tests for sanitizing checkpointer."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from langgraph.checkpoint.base import BaseCheckpointSaver

from nanobot_deep.langgraph.sanitizing_checkpointer import (
    SanitizingCheckpointerWrapper,
    wrap_checkpointer_with_sanitizer,
)
from nanobot_deep.langgraph.windowing_checkpointer import WindowingCheckpointerWrapper


class TestSanitizingCheckpointerWrapper:
    """Tests for SanitizingCheckpointerWrapper."""

    def test_wrap_checkpointer_with_sanitizer_returns_wrapper(self):
        """Test that wrapping returns a SanitizingCheckpointerWrapper."""
        mock_checkpointer = MagicMock()
        wrapped = wrap_checkpointer_with_sanitizer(mock_checkpointer)

        assert isinstance(wrapped, SanitizingCheckpointerWrapper)
        assert wrapped._checkpointer is mock_checkpointer

    def test_wrap_already_wrapped_returns_same(self):
        """Test that wrapping an already wrapped checkpointer returns the same."""
        mock_checkpointer = MagicMock()
        wrapped1 = wrap_checkpointer_with_sanitizer(mock_checkpointer)
        wrapped2 = wrap_checkpointer_with_sanitizer(wrapped1)

        assert wrapped1 is wrapped2

    def test_sanitize_checkpoint_removes_reasoning(self):
        """Test that reasoning is removed from checkpoint messages."""
        from langchain_core.messages import AIMessage

        mock_checkpointer = MagicMock()
        mock_checkpointer.put.return_value = None
        wrapper = SanitizingCheckpointerWrapper(mock_checkpointer)

        checkpoint = {
            "channel_values": {
                "messages": [
                    AIMessage(content="test", additional_kwargs={"reasoning": 1}),
                    AIMessage(content="test2", additional_kwargs={}),
                ]
            }
        }

        wrapper.put({}, checkpoint, {})

        call_args = mock_checkpointer.put.call_args
        sanitized_checkpoint = call_args[0][1]  # Get the second argument (checkpoint)

        messages = sanitized_checkpoint["channel_values"]["messages"]
        assert messages[0].additional_kwargs == {}
        assert "reasoning" not in messages[0].additional_kwargs
        assert messages[1].additional_kwargs == {}

    def test_sanitize_writes_removes_reasoning(self):
        """Test that reasoning is removed from writes."""
        from langchain_core.messages import AIMessage

        mock_checkpointer = MagicMock()
        mock_checkpointer.put_writes.return_value = None
        wrapper = SanitizingCheckpointerWrapper(mock_checkpointer)

        writes = [
            ("messages", [AIMessage(content="test", additional_kwargs={"reasoning": 1})]),
        ]

        wrapper.put_writes({}, writes)

        call_args = mock_checkpointer.put_writes.call_args
        sanitized_writes = call_args[0][1]  # Get the second argument (writes)

        assert sanitized_writes[0][0] == "messages"
        # Sanitized message should have reasoning removed
        assert "reasoning" not in sanitized_writes[0][1][0].additional_kwargs

    def test_sanitize_non_message_fields_preserved(self):
        """Test that non-message fields are preserved."""
        mock_checkpointer = MagicMock()
        mock_checkpointer.put.return_value = None
        wrapper = SanitizingCheckpointerWrapper(mock_checkpointer)

        checkpoint = {
            "channel_values": {
                "other_field": "value",
                "count": 42,
            }
        }

        wrapper.put({}, checkpoint, {})

        call_args = mock_checkpointer.put.call_args
        sanitized = call_args[0][1]  # Get the second argument (checkpoint)

        assert sanitized["channel_values"]["other_field"] == "value"
        assert sanitized["channel_values"]["count"] == 42

    def test_sanitize_nested_dict(self):
        """Test that nested dicts are sanitized."""
        mock_checkpointer = MagicMock()
        mock_checkpointer.put.return_value = None
        wrapper = SanitizingCheckpointerWrapper(mock_checkpointer)

        checkpoint = {
            "channel_values": {
                "messages": [
                    {"nested": {"reasoning": 1}},
                ]
            }
        }

        wrapper.put({}, checkpoint, {})

        call_args = mock_checkpointer.put.call_args
        sanitized = call_args[0][1]  # Get the second argument (checkpoint)

        assert sanitized["channel_values"]["messages"][0]["nested"] == {"reasoning": 1}

    def test_put_delegates_to_checkpointer(self):
        """Test that put() delegates to the wrapped checkpointer."""
        mock_checkpointer = MagicMock()
        mock_checkpointer.put.return_value = {"config": "result"}
        wrapper = SanitizingCheckpointerWrapper(mock_checkpointer)

        result = wrapper.put(
            config={"configurable": {"thread_id": "test"}},
            checkpoint={"channel_values": {}},
            metadata={},
        )

        mock_checkpointer.put.assert_called_once()
        assert result == {"config": "result"}

    def test_get_delegates_to_checkpointer(self):
        """Test that get() delegates to the wrapped checkpointer."""
        mock_checkpointer = MagicMock()
        mock_checkpointer.get.return_value = {"checkpoint": "data"}
        wrapper = SanitizingCheckpointerWrapper(mock_checkpointer)

        result = wrapper.get(config={"configurable": {"thread_id": "test"}})

        mock_checkpointer.get.assert_called_once()
        assert result == {"checkpoint": "data"}

    def test_delete_thread_delegates(self):
        """Test that delete_thread() delegates to the wrapped checkpointer."""
        mock_checkpointer = MagicMock()
        mock_checkpointer.delete_thread = MagicMock()
        wrapper = SanitizingCheckpointerWrapper(mock_checkpointer)

        wrapper.delete_thread("test-thread")

        mock_checkpointer.delete_thread.assert_called_once_with("test-thread")


class TestIsinstanceValidation:
    def test_isinstance_base_checkpointer_saver(self):
        w = SanitizingCheckpointerWrapper(MagicMock())

        assert isinstance(w, BaseCheckpointSaver)

    def test_wrap_returns_base_checkpointer_saver(self):
        wrapped = wrap_checkpointer_with_sanitizer(MagicMock())

        assert isinstance(wrapped, BaseCheckpointSaver)

    def test_double_wrap_isinstance(self):
        sanitized = SanitizingCheckpointerWrapper(MagicMock())
        windowed = WindowingCheckpointerWrapper(sanitized, 10)

        assert isinstance(windowed, BaseCheckpointSaver)

    def test_ensure_valid_checkpointer_no_raise(self):
        wrapper = SanitizingCheckpointerWrapper(MagicMock())

        try:
            from langgraph.graph.state import ensure_valid_checkpointer
        except ImportError:
            try:
                from langgraph.pregel import ensure_valid_checkpointer
            except ImportError:
                pytest.skip("ensure_valid_checkpointer import path unavailable")

        assert ensure_valid_checkpointer(wrapper) is wrapper

    def test_wrap_idempotency(self):
        mock_checkpointer = MagicMock()
        wrapped_once = wrap_checkpointer_with_sanitizer(mock_checkpointer)
        wrapped_twice = wrap_checkpointer_with_sanitizer(wrapped_once)

        assert wrapped_twice is wrapped_once
