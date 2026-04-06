"""Unit tests for sanitizing checkpointer."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from nanobot_deep.langgraph.sanitizing_checkpointer import (
    SanitizingCheckpointerWrapper,
    wrap_checkpointer_with_sanitizer,
)


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
        wrapper = SanitizingCheckpointerWrapper(mock_checkpointer)

        checkpoint = {
            "channel_values": {
                "messages": [
                    AIMessage(content="test", additional_kwargs={"reasoning": 1}),
                    AIMessage(content="test2", additional_kwargs={}),
                ]
            }
        }

        sanitized = wrapper._sanitize_checkpoint(checkpoint)

        messages = sanitized["channel_values"]["messages"]
        assert messages[0].additional_kwargs == {}
        assert "reasoning" not in messages[0].additional_kwargs
        assert messages[1].additional_kwargs == {}

    def test_sanitize_writes_removes_reasoning(self):
        """Test that reasoning is removed from writes."""
        from langchain_core.messages import AIMessage

        mock_checkpointer = MagicMock()
        wrapper = SanitizingCheckpointerWrapper(mock_checkpointer)

        writes = [
            ("messages", [AIMessage(content="test", additional_kwargs={"reasoning": 1})]),
        ]

        sanitized = wrapper._sanitize_writes(writes)

        assert sanitized[0][0] == "messages"
        assert sanitized[0][1][0].additional_kwargs == {}

    def test_sanitize_non_message_fields_preserved(self):
        """Test that non-message fields are preserved."""
        mock_checkpointer = MagicMock()
        wrapper = SanitizingCheckpointerWrapper(mock_checkpointer)

        checkpoint = {
            "channel_values": {
                "other_field": "value",
                "count": 42,
            }
        }

        sanitized = wrapper._sanitize_checkpoint(checkpoint)

        assert sanitized["channel_values"]["other_field"] == "value"
        assert sanitized["channel_values"]["count"] == 42

    def test_sanitize_nested_dict(self):
        """Test that nested dicts are sanitized."""
        mock_checkpointer = MagicMock()
        wrapper = SanitizingCheckpointerWrapper(mock_checkpointer)

        checkpoint = {
            "channel_values": {
                "messages": [
                    {"nested": {"reasoning": 1}},
                ]
            }
        }

        sanitized = wrapper._sanitize_checkpoint(checkpoint)

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
