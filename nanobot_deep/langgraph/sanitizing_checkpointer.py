"""Checkpoint sanitization utilities to fix Pydantic serialization issues."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from loguru import logger

if TYPE_CHECKING:
    from langgraph.checkpoint.base import BaseCheckpointSaver


class SanitizingCheckpointerWrapper:
    """Wrapper that sanitizes messages before checkpointing.

    This wrapper strips problematic fields like `reasoning` from `additional_kwargs`
    in AIMessage objects to prevent Pydantic serialization errors during checkpointing.

    The issue occurs when AI providers (like z.ai/GPT) add `reasoning` to
    `additional_kwargs`, which causes Pydantic validation to fail during
    checkpoint serialization.
    """

    def __init__(self, checkpointer: "BaseCheckpointSaver"):
        self._checkpointer = checkpointer

    def _sanitize_value(self, value: Any) -> Any:
        """Recursively sanitize a value, removing problematic fields."""
        if isinstance(value, dict):
            return {k: self._sanitize_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._sanitize_value(item) for item in value]
        elif hasattr(value, "additional_kwargs") and isinstance(value.additional_kwargs, dict):
            sanitized = value.model_copy(deep=True)
            if (
                hasattr(sanitized, "additional_kwargs")
                and "reasoning" in sanitized.additional_kwargs
            ):
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

    def _sanitize_checkpoint(self, checkpoint: dict[str, Any]) -> dict[str, Any]:
        """Sanitize a checkpoint dict, removing reasoning from messages."""
        sanitized = checkpoint.copy()
        if "channel_values" in sanitized:
            channel_values = sanitized["channel_values"].copy()
            if "messages" in channel_values:
                channel_values["messages"] = [
                    self._sanitize_value(msg) for msg in channel_values["messages"]
                ]
            sanitized["channel_values"] = channel_values
        return sanitized

    def _sanitize_writes(self, writes: list[tuple[str, Any]]) -> list[tuple[str, Any]]:
        """Sanitize writes before checkpointing."""
        sanitized_writes = []
        for channel, value in writes:
            if channel == "messages" or (isinstance(channel, str) and "message" in channel.lower()):
                sanitized_writes.append((channel, self._sanitize_value(value)))
            else:
                sanitized_writes.append((channel, value))
        return sanitized_writes

    async def aput(
        self,
        config: dict[str, Any],
        checkpoint: dict[str, Any],
        metadata: dict[str, Any],
        new_versions: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Async put with sanitization."""
        sanitized_checkpoint = self._sanitize_checkpoint(checkpoint)
        return await self._checkpointer.aput(config, sanitized_checkpoint, metadata, new_versions)

    def put(
        self,
        config: dict[str, Any],
        checkpoint: dict[str, Any],
        metadata: dict[str, Any],
        new_versions: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Sync put with sanitization."""
        sanitized_checkpoint = self._sanitize_checkpoint(checkpoint)
        return self._checkpointer.put(config, sanitized_checkpoint, metadata, new_versions)

    async def aput_writes(
        self,
        config: dict[str, Any],
        writes: list[tuple[str, Any]],
        task_id: str | None = None,
    ) -> None:
        """Async put writes with sanitization."""
        sanitized_writes = self._sanitize_writes(writes)
        await self._checkpointer.aput_writes(config, sanitized_writes, task_id)

    def put_writes(
        self,
        config: dict[str, Any],
        writes: list[tuple[str, Any]],
        task_id: str | None = None,
    ) -> None:
        """Sync put writes with sanitization."""
        sanitized_writes = self._sanitize_writes(writes)
        self._checkpointer.put_writes(config, sanitized_writes, task_id)

    async def aget(
        self,
        config: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Async get checkpoint."""
        return await self._checkpointer.aget(config)

    def get(
        self,
        config: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Sync get checkpoint."""
        return self._checkpointer.get(config)

    async def aget_next_version(
        self,
        current_version: str | None,
        channel: str,
    ) -> int:
        """Get next version number."""
        return await self._checkpointer.aget_next_version(current_version, channel)

    def get_next_version(
        self,
        current_version: str | None,
        channel: str,
    ) -> int:
        """Get next version number."""
        return self._checkpointer.get_next_version(current_version, channel)

    async def alist(
        self,
        config: dict[str, Any] | None = None,
        *,
        filter: dict[str, Any] | None = None,
        before: dict[str, Any] | None = None,
        limit: int | None = None,
    ):
        """List checkpoints."""
        return await self._checkpointer.alist(config, filter=filter, before=before, limit=limit)

    def list(
        self,
        config: dict[str, Any] | None = None,
        *,
        filter: dict[str, Any] | None = None,
        before: dict[str, Any] | None = None,
        limit: int | None = None,
    ):
        """List checkpoints."""
        return self._checkpointer.list(config, filter=filter, before=before, limit=limit)

    async def adelete_thread(self, thread_id: str) -> None:
        """Delete a thread."""
        if hasattr(self._checkpointer, "adelete_thread"):
            await self._checkpointer.adelete_thread(thread_id)
        elif hasattr(self._checkpointer, "delete_thread"):
            self._checkpointer.delete_thread(thread_id)

    def delete_thread(self, thread_id: str) -> None:
        """Delete a thread."""
        if hasattr(self._checkpointer, "delete_thread"):
            self._checkpointer.delete_thread(thread_id)
        elif hasattr(self._checkpointer, "adelete_thread"):
            import asyncio

            asyncio.run(self._checkpointer.adelete_thread(thread_id))

    def get_tuple(self, config: dict[str, Any]) -> Any:
        """Get checkpoint tuple."""
        return self._checkpointer.get_tuple(config)

    async def aget_tuple(self, config: dict[str, Any]) -> Any:
        """Async get checkpoint tuple."""
        return await self._checkpointer.aget_tuple(config)


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
        >>> from langgraph.checkpoint.sqlite import AsyncSqliteSaver
        >>> base_checkpointer = AsyncSqliteSaver.from_conn_string("...")
        >>> checkpointer = wrap_checkpointer_with_sanitizer(base_checkpointer)
    """
    if isinstance(checkpointer, SanitizingCheckpointerWrapper):
        logger.debug("Checkpointer already wrapped with sanitizer")
        return checkpointer

    logger.debug("Wrapping checkpointer with message sanitizer")
    return SanitizingCheckpointerWrapper(checkpointer)
