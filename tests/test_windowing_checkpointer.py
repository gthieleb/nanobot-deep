from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from langgraph.checkpoint.base import CheckpointTuple

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
