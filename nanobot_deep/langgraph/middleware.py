"""LangGraph middleware helpers for nanobot-deep."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from langchain.agents.middleware.types import AgentMiddleware, ModelRequest, ModelResponse
from langchain_core.messages import BaseMessage, SystemMessage

ResponseT = TypeVar("ResponseT")
ContextT = TypeVar("ContextT")


def _flatten_content(content: str | list[str | dict[str, Any]]) -> str:
    if isinstance(content, str):
        return content

    parts: list[str] = []
    for item in content:
        if isinstance(item, str):
            parts.append(item)
        elif isinstance(item, dict):
            text = item.get("text")
            if text:
                parts.append(str(text))
    return "\n".join(part for part in parts if part)


def _flatten_system_message(request: ModelRequest[ContextT]) -> ModelRequest[ContextT]:
    system_message = request.system_message
    if system_message is None:
        return request

    content = system_message.content
    if not isinstance(content, list):
        return request

    flattened = _flatten_content(content)
    new_system_message = SystemMessage(content=flattened)
    return request.override(system_message=new_system_message)


def _flatten_message(message: BaseMessage) -> BaseMessage:
    content = message.content
    if not isinstance(content, list):
        return message

    flattened = _flatten_content(content)
    return message.model_copy(update={"content": flattened})


def _flatten_messages(request: ModelRequest[ContextT]) -> ModelRequest[ContextT]:
    if not request.messages:
        return request

    flattened_messages = [_flatten_message(message) for message in request.messages]
    if flattened_messages == request.messages:
        return request
    return request.override(messages=flattened_messages)


class FlattenContentBlocksMiddleware(AgentMiddleware[Any, Any]):
    def wrap_model_call(
        self,
        request: ModelRequest[ContextT],
        handler: Callable[[ModelRequest[ContextT]], ModelResponse[ResponseT]],
    ) -> ModelResponse[ResponseT]:
        flattened_request = _flatten_system_message(request)
        flattened_request = _flatten_messages(flattened_request)
        return handler(flattened_request)

    async def awrap_model_call(
        self,
        request: ModelRequest[ContextT],
        handler: Callable[[ModelRequest[ContextT]], Awaitable[ModelResponse[ResponseT]]],
    ) -> ModelResponse[ResponseT]:
        flattened_request = _flatten_system_message(request)
        flattened_request = _flatten_messages(flattened_request)
        return await handler(flattened_request)
