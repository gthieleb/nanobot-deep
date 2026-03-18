"""Session history utilities for LangGraph checkpointer."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from langchain_core.runnables import RunnableConfig

if TYPE_CHECKING:
    from langgraph.checkpoint.base import BaseCheckpointSaver


def get_session_history(
    checkpointer: "BaseCheckpointSaver", thread_id: str, limit: int = 100
) -> list[dict]:
    """Get message history for a session.

    Args:
        checkpointer: The checkpointer instance (AsyncSqliteSaver, SqliteSaver, etc.)
        thread_id: The session/thread identifier
        limit: Maximum messages to return

    Returns:
        List of message dicts in nanobot format
    """
    import asyncio

    config: RunnableConfig = {"configurable": {"thread_id": thread_id}}

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(_get_history_sync, checkpointer, config, limit)
            checkpoint_tuple = future.result()
    else:
        checkpoint_tuple = _get_history_sync(checkpointer, config, limit)

    if not checkpoint_tuple:
        return []

    checkpoint = checkpoint_tuple.checkpoint
    messages = checkpoint.get("channel_values", {}).get("messages", [])

    history = []
    for msg in messages[-limit:]:
        msg_dict: dict[str, Any] = {}

        if hasattr(msg, "content"):
            if hasattr(msg, "type"):
                if msg.type == "human":
                    msg_dict["role"] = "user"
                elif msg.type == "ai":
                    msg_dict["role"] = "assistant"
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        msg_dict["tool_calls"] = [
                            {
                                "id": tc.get("id", ""),
                                "type": "function",
                                "function": {
                                    "name": tc.get("name", ""),
                                    "arguments": json.dumps(tc.get("args", {})),
                                },
                            }
                            for tc in msg.tool_calls
                        ]
                elif msg.type == "tool":
                    msg_dict["role"] = "tool"
                    msg_dict["tool_call_id"] = getattr(msg, "tool_call_id", "")
                elif msg.type == "system":
                    msg_dict["role"] = "system"

            msg_dict["content"] = msg.content if isinstance(msg.content, str) else str(msg.content)

        if msg_dict.get("role"):
            history.append(msg_dict)

    return history


def _get_history_sync(checkpointer: "BaseCheckpointSaver", config: RunnableConfig, limit: int):
    """Synchronously get checkpoint tuple."""
    return checkpointer.get_tuple(config)
