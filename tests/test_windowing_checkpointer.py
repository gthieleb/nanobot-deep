from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from langgraph.checkpoint.base import BaseCheckpointSaver, CheckpointTuple

from nanobot_deep.langgraph.sanitizing_checkpointer import SanitizingCheckpointerWrapper
from nanobot_deep.langgraph.windowing_checkpointer import (
    WindowingCheckpointerWrapper,
    wrap_checkpointer_with_window,
)


def _make_tuple(messages):
    return CheckpointTuple(
        config={"configurable": {"thread_id": "t"}},
        checkpoint={"channel_values": {"messages": messages}},
        metadata={},
    )


class TestWindowingCheckpointerWrapper:
    def test_wrap_none_returns_same(self):
        checkpointer = MagicMock()
        wrapped = wrap_checkpointer_with_window(checkpointer, None)

        assert wrapped is checkpointer

    def test_get_tuple_windows_messages(self):
        checkpointer = MagicMock()
        checkpointer.get_tuple.return_value = _make_tuple(["a", "b", "c", "d"])
        wrapper = WindowingCheckpointerWrapper(checkpointer, 2)

        result = wrapper.get_tuple({"configurable": {"thread_id": "t"}})

        assert result.checkpoint["channel_values"]["messages"] == ["c", "d"]

    def test_get_tuple_handles_empty(self):
        checkpointer = MagicMock()
        checkpointer.get_tuple.return_value = None
        wrapper = WindowingCheckpointerWrapper(checkpointer, 2)

        result = wrapper.get_tuple({"configurable": {"thread_id": "t"}})

        assert result is None

    @pytest.mark.asyncio
    async def test_aget_tuple_windows_messages(self):
        checkpointer = MagicMock()
        checkpointer.aget_tuple = AsyncMock(return_value=_make_tuple([1, 2, 3]))
        wrapper = WindowingCheckpointerWrapper(checkpointer, 1)

        result = await wrapper.aget_tuple({"configurable": {"thread_id": "t"}})

        assert result.checkpoint["channel_values"]["messages"] == [3]


class TestIsinstanceValidation:
    def test_isinstance_base_checkpointer_saver(self):
        w = WindowingCheckpointerWrapper(MagicMock(), 10)

        assert isinstance(w, BaseCheckpointSaver)

    def test_wrap_returns_base_checkpointer_saver(self):
        wrapped = wrap_checkpointer_with_window(MagicMock(), 10)

        assert isinstance(wrapped, BaseCheckpointSaver)

    def test_double_wrap_isinstance(self):
        sanitized = SanitizingCheckpointerWrapper(MagicMock())
        windowed = WindowingCheckpointerWrapper(sanitized, 10)

        assert isinstance(windowed, BaseCheckpointSaver)

    def test_ensure_valid_checkpointer_no_raise(self):
        wrapper = WindowingCheckpointerWrapper(MagicMock(), 10)

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
        wrapped_once = wrap_checkpointer_with_window(mock_checkpointer, 10)
        wrapped_twice = wrap_checkpointer_with_window(wrapped_once, 10)

        assert wrapped_twice is wrapped_once
