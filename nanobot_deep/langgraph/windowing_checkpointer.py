from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from langgraph.checkpoint.base import Checkpoint, CheckpointTuple


def _window_messages(messages: list[Any], memory_window: int) -> list[Any]:
    if memory_window <= 0:
        return []
    if len(messages) <= memory_window:
        return messages
    return messages[-memory_window:]


def _window_checkpoint(checkpoint: "Checkpoint", memory_window: int) -> "Checkpoint":
    if not isinstance(checkpoint, dict):
        return checkpoint
    channel_values = checkpoint.get("channel_values")
    if not isinstance(channel_values, dict):
        return checkpoint
    messages = channel_values.get("messages")
    if not isinstance(messages, list):
        return checkpoint

    windowed = _window_messages(messages, memory_window)
    if windowed is messages:
        return checkpoint

    new_checkpoint = checkpoint.copy()
    new_channel_values = channel_values.copy()
    new_channel_values["messages"] = windowed
    new_checkpoint["channel_values"] = new_channel_values
    return new_checkpoint


def _window_checkpoint_tuple(
    checkpoint_tuple: "CheckpointTuple", memory_window: int
) -> "CheckpointTuple":
    from langgraph.checkpoint.base import CheckpointTuple

    checkpoint = _window_checkpoint(checkpoint_tuple.checkpoint, memory_window)
    if checkpoint is checkpoint_tuple.checkpoint:
        return checkpoint_tuple

    return CheckpointTuple(
        checkpoint_tuple.config,
        checkpoint,
        checkpoint_tuple.metadata,
        checkpoint_tuple.parent_config,
        checkpoint_tuple.pending_writes,
    )


class WindowingCheckpointerWrapper:
    def __init__(self, checkpointer: Any, memory_window: int):
        self._checkpointer = checkpointer
        self._memory_window = memory_window

    def __getattr__(self, name: str) -> Any:
        return getattr(self._checkpointer, name)

    def get_tuple(self, config: dict[str, Any]):
        result = self._checkpointer.get_tuple(config)
        if result is None:
            return None
        return _window_checkpoint_tuple(result, self._memory_window)

    async def aget_tuple(self, config: dict[str, Any]):
        result = await self._checkpointer.aget_tuple(config)
        if result is None:
            return None
        return _window_checkpoint_tuple(result, self._memory_window)

    def get(self, config: dict[str, Any]):
        result = self._checkpointer.get(config)
        if result is None:
            return None
        return _window_checkpoint(result, self._memory_window)

    async def aget(self, config: dict[str, Any]):
        result = await self._checkpointer.aget(config)
        if result is None:
            return None
        return _window_checkpoint(result, self._memory_window)


def wrap_checkpointer_with_window(checkpointer: Any, memory_window: int | None) -> Any:
    if memory_window is None:
        return checkpointer
    if isinstance(checkpointer, WindowingCheckpointerWrapper):
        if checkpointer._memory_window == memory_window:
            return checkpointer
    return WindowingCheckpointerWrapper(checkpointer, memory_window)
