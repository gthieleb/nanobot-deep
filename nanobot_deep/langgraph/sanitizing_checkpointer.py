"""Checkpoint sanitization utilities to fix Pydantic serialization issues."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from loguru import logger

if TYPE_CHECKING:
    from langgraph.checkpoint.base import BaseCheckpointSaver


def _sanitize_value(value: Any) -> Any:
    """Recursively sanitize a value, removing problematic fields."""
    if isinstance(value, dict):
        return {k: _sanitize_value(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [_sanitize_value(item) for item in value]
    elif hasattr(value, "additional_kwargs") and isinstance(value.additional_kwargs, dict):
        sanitized = value.model_copy(deep=True)
        if hasattr(sanitized, "additional_kwargs") and "reasoning" in sanitized.additional_kwargs:
            del sanitized.additional_kwargs["reasoning"]
        if hasattr(sanitized, "usage_metadata") and sanitized.usage_metadata:
            sanitized_usage = sanitized.usage_metadata.copy()
            if "prompt_tokens_details" in sanitized_usage:
                details = sanitized_usage["prompt_tokens_details"]
                if hasattr(details, "additional_kwargs"):
                    sanitized_details = details.model_copy(deep=True)
                    if hasattr(sanitized_details, "additional_kwargs") and hasattr(
                        sanitized_details.additional_kwargs, "__delitem__"
                    ):
                        sanitized_details.additional_kwargs.pop("reasoning", None)
                    sanitized_usage["prompt_tokens_details"] = sanitized_details
            sanitized.usage_metadata = sanitized_usage
        return sanitized
    return value


def _sanitize_checkpoint(checkpoint: dict[str, Any]) -> dict[str, Any]:
    """Sanitize a checkpoint dict, removing reasoning from messages."""
    sanitized = checkpoint.copy()
    if "channel_values" in sanitized:
        channel_values = sanitized["channel_values"].copy()
        if "messages" in channel_values:
            channel_values["messages"] = [
                _sanitize_value(msg) for msg in channel_values["messages"]
            ]
        sanitized["channel_values"] = channel_values
    return sanitized


def _sanitize_writes(writes: list[tuple[str, Any]]) -> list[tuple[str, Any]]:
    """Sanitize writes before checkpointing."""
    sanitized_writes = []
    for channel, value in writes:
        if channel == "messages" or (isinstance(channel, str) and "message" in channel.lower()):
            sanitized_writes.append((channel, _sanitize_value(value)))
        else:
            sanitized_writes.append((channel, value))
    return sanitized_writes


def _make_sanitizing_method(method_name: str):
    """Create a sanitizing wrapper for an async method."""
    original_method = None

    async def sanitizing_method(self, *args, **kwargs):
        nonlocal original_method
        if original_method is None:
            original_method = getattr(type(self).__bases__[0], method_name)

        if method_name in ("aput", "put"):
            checkpoint = args[1] if len(args) > 1 else kwargs.get("checkpoint")
            if checkpoint:
                sanitized = _sanitize_checkpoint(checkpoint)
                args = (args[0], sanitized, *args[2:])
        elif method_name in ("aput_writes", "put_writes"):
            writes = args[1] if len(args) > 1 else kwargs.get("writes")
            if writes:
                sanitized = _sanitize_writes(writes)
                args = (args[0], sanitized, *args[2:])

        return await original_method(self, *args, **kwargs)

    return sanitizing_method


class SanitizingCheckpointerWrapper:
    """Wrapper that sanitizes messages before checkpointing.

    This wrapper strips problematic fields like `reasoning` from `additional_kwargs`
    in AIMessage objects to prevent Pydantic serialization errors during checkpointing.

    The issue occurs when AI providers (like z.ai/GPT) add `reasoning` to
    `additional_kwargs`, which causes Pydantic validation to fail during
    checkpoint serialization.

    This implementation delegates all attribute access to the wrapped checkpointer
    to ensure full compatibility, including attributes like `lock` that langgraph
    may access directly.
    """

    def __init__(self, checkpointer: "BaseCheckpointSaver"):
        self._checkpointer = checkpointer

    def __getattribute__(self, name: str) -> Any:
        """Delegate all attribute access to wrapped checkpointer."""
        if name == "_checkpointer":
            return object.__getattribute__(self, name)
        # Check if attribute exists on the wrapper itself first
        try:
            attr = object.__getattribute__(self, name)
            return attr
        except AttributeError:
            # If not found on wrapper, delegate to checkpointer
            return getattr(self._checkpointer, name)

    def __getattr__(self, name: str) -> Any:
        """Delegate to wrapped checkpointer for any missing attributes."""
        return getattr(self._checkpointer, name)

    async def aput(
        self,
        config: dict[str, Any],
        checkpoint: dict[str, Any],
        metadata: dict[str, Any],
        new_versions: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Async put with sanitization."""
        sanitized_checkpoint = _sanitize_checkpoint(checkpoint)
        return await self._checkpointer.aput(config, sanitized_checkpoint, metadata, new_versions)

    def put(
        self,
        config: dict[str, Any],
        checkpoint: dict[str, Any],
        metadata: dict[str, Any],
        new_versions: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Sync put with sanitization."""
        sanitized_checkpoint = _sanitize_checkpoint(checkpoint)
        return self._checkpointer.put(config, sanitized_checkpoint, metadata, new_versions)

    async def aput_writes(
        self,
        config: dict[str, Any],
        writes: list[tuple[str, Any]],
        task_id: str | None = None,
    ) -> None:
        """Async put writes with sanitization."""
        sanitized_writes = _sanitize_writes(writes)
        await self._checkpointer.aput_writes(config, sanitized_writes, task_id)

    def put_writes(
        self,
        config: dict[str, Any],
        writes: list[tuple[str, Any]],
        task_id: str | None = None,
    ) -> None:
        """Sync put writes with sanitization."""
        sanitized_writes = _sanitize_writes(writes)
        self._checkpointer.put_writes(config, sanitized_writes, task_id)


def wrap_checkpointer_with_sanitizer(
    checkpointer: "BaseCheckpointSaver",
) -> SanitizingCheckpointerWrapper:
    """Wrap a checkpointer with message sanitization.

    This prevents Pydantic serialization errors during checkpointing by stripping
    problematic fields like `reasoning` from AIMessage.additional_kwargs.

    Args:
        checkpointer: The checkpointer to wrap

    Returns:
        A wrapped checkpointer that sanitizes messages before checkpointing

    Example:
        >>> from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
        >>> async with aiosqlite.connect(":memory:") as conn:
        ...     base_checkpointer = AsyncSqliteSaver(conn)
        ...     checkpointer = wrap_checkpointer_with_sanitizer(base_checkpointer)
    """
    if isinstance(checkpointer, SanitizingCheckpointerWrapper):
        logger.debug("Checkpointer already wrapped with sanitizer")
        return checkpointer

    logger.debug("Wrapping checkpointer with message sanitizer")
    return SanitizingCheckpointerWrapper(checkpointer)
