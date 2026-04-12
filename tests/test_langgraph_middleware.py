from __future__ import annotations

from types import SimpleNamespace

from langchain.agents.middleware.types import ModelRequest
from langchain_core.messages import SystemMessage

from nanobot_deep.langgraph.middleware import (
    FlattenContentBlocksMiddleware,
    _flatten_content,
    _flatten_message,
)


def test_flatten_content_with_blocks():
    content = ["Hello", {"text": "World"}, {"text": ""}, {"other": 1}]
    assert _flatten_content(content) == "Hello\nWorld"


def test_flatten_message_no_change():
    message = SystemMessage(content="Keep")
    assert _flatten_message(message) is message


def test_middleware_flattens_system_and_messages():
    system_message = SystemMessage(content=["System", {"text": "Prompt"}])
    message = SystemMessage(content=["Hello", {"text": "User"}])
    request = ModelRequest(
        model=SimpleNamespace(), messages=[message], system_message=system_message
    )

    def handler(updated):
        return updated

    middleware = FlattenContentBlocksMiddleware()
    result = middleware.wrap_model_call(request, handler)

    assert result.system_message is not None
    assert result.system_message.content == "System\nPrompt"
    assert result.messages[0].content == "Hello\nUser"
