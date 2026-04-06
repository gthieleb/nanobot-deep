"""Unit tests for DeepAgent provider error mapping."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch
import pytest

from nanobot_deep.agent.deep_agent import DeepAgent


def test_rate_limit_error_message_is_precise() -> None:
    class RateLimitError(Exception):
        pass

    msg = DeepAgent._format_user_facing_error(RateLimitError("429 Too Many Requests"))
    assert "rate limit" in msg.lower()
    assert "429" in msg


def test_quota_error_message_is_precise() -> None:
    err = Exception("insufficient_quota: monthly credits exceeded")
    msg = DeepAgent._format_user_facing_error(err)
    assert "quota" in msg.lower()
    assert "billing" in msg.lower()


def test_auth_error_message_is_precise() -> None:
    class AuthenticationError(Exception):
        pass

    msg = DeepAgent._format_user_facing_error(AuthenticationError("invalid api key"))
    assert "authentication" in msg.lower()
    assert "api key" in msg.lower()


def test_timeout_error_message_is_precise() -> None:
    class Timeout(Exception):
        pass

    msg = DeepAgent._format_user_facing_error(Timeout("request timed out"))
    assert "timeout" in msg.lower() or "connectivity" in msg.lower()


def test_bad_request_error_message_is_precise() -> None:
    class ContextWindowExceededError(Exception):
        pass

    msg = DeepAgent._format_user_facing_error(
        ContextWindowExceededError("maximum context length exceeded")
    )
    assert "context" in msg.lower() or "invalid input" in msg.lower()


def test_unknown_error_keeps_detail() -> None:
    msg = DeepAgent._format_user_facing_error(Exception("unexpected boom"))
    assert "unexpected boom" in msg


@pytest.mark.asyncio
async def test_validate_model_raises_for_invalid_provider_model() -> None:
    from unittest.mock import AsyncMock

    agent = object.__new__(DeepAgent)
    agent.dg_config = SimpleNamespace(
        model=SimpleNamespace(name="openai/not-a-real-model", max_tokens=2000, temperature=0.1)
    )
    agent.config = SimpleNamespace(
        agents=SimpleNamespace(defaults=SimpleNamespace(model="gpt-5-mini"))
    )

    fake_model = MagicMock()
    fake_model.ainvoke = AsyncMock(side_effect=Exception("Model not found"))

    with patch("nanobot_deep.agent.factory._init_model", return_value=(fake_model, MagicMock())):
        with pytest.raises(RuntimeError, match="Model validation failed"):
            await agent.validate_model(timeout_seconds=0.1)
