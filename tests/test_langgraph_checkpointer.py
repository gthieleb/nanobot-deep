from __future__ import annotations

from types import SimpleNamespace

import pytest

from nanobot_deep.langgraph.checkpointer import get_session_history


class FakeCheckpointer:
    def __init__(self, checkpoint_tuple):
        self._checkpoint_tuple = checkpoint_tuple

    def get_tuple(self, _config):
        return self._checkpoint_tuple


def test_get_session_history_empty():
    checkpointer = FakeCheckpointer(None)
    history = get_session_history(checkpointer, "thread")
    assert history == []


def test_get_session_history_roles():
    human = SimpleNamespace(type="human", content="hi")
    ai = SimpleNamespace(
        type="ai",
        content="hello",
        tool_calls=[{"id": "1", "name": "tool", "args": {"q": "x"}}],
    )
    tool = SimpleNamespace(type="tool", content="ok", tool_call_id="1")
    system = SimpleNamespace(type="system", content="sys")

    checkpoint = {"channel_values": {"messages": [human, ai, tool, system]}}
    checkpointer = FakeCheckpointer(SimpleNamespace(checkpoint=checkpoint))

    history = get_session_history(checkpointer, "thread")
    assert history[0]["role"] == "user"
    assert history[1]["role"] == "assistant"
    assert history[1]["tool_calls"][0]["function"]["name"] == "tool"
    assert history[2]["role"] == "tool"
    assert history[2]["tool_call_id"] == "1"
    assert history[3]["role"] == "system"


@pytest.mark.asyncio
async def test_get_session_history_in_running_loop():
    ai = SimpleNamespace(type="ai", content="hello", tool_calls=[])
    checkpoint = {"channel_values": {"messages": [ai]}}
    checkpointer = FakeCheckpointer(SimpleNamespace(checkpoint=checkpoint))

    history = get_session_history(checkpointer, "thread")
    assert history[0]["role"] == "assistant"
