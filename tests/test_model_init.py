"""Unit tests for model initialization with ChatLiteLLM."""

from __future__ import annotations

from unittest.mock import MagicMock, patch


class TestModelInit:
    """Tests for model initialization with litellm-style model names."""

    def test_anthropic_model_name(self):
        """Test anthropic model name is passed correctly."""
        from langchain_litellm import ChatLiteLLM

        model = ChatLiteLLM(
            model="anthropic/claude-sonnet-4-5",
            api_key="test-key",
            max_tokens=1000,
            temperature=0.7,
        )

        assert model.model == "anthropic/claude-sonnet-4-5"

    def test_openai_model_name(self):
        """Test openai model name is passed correctly."""
        from langchain_litellm import ChatLiteLLM

        model = ChatLiteLLM(
            model="openai/gpt-4",
            api_key="test-key",
            max_tokens=1000,
            temperature=0.7,
        )

        assert model.model == "openai/gpt-4"

    def test_custom_provider_model_name(self):
        """Test custom provider model name is passed correctly."""
        from langchain_litellm import ChatLiteLLM

        model = ChatLiteLLM(
            model="zai/glm-4.7",
            api_key="test-key",
            api_base="https://api.zai.com/v1",
            max_tokens=1000,
            temperature=0.7,
        )

        assert model.model == "zai/glm-4.7"

    def test_model_without_provider_prefix(self):
        """Test model name without provider prefix."""
        from langchain_litellm import ChatLiteLLM

        model = ChatLiteLLM(
            model="gpt-4",
            api_key="test-key",
            max_tokens=1000,
            temperature=0.7,
        )

        assert model.model == "gpt-4"


class TestDeepAgentModelInit:
    """Tests for factory model initialization."""

    def _create_mock_config(self, model: str = "anthropic/claude-sonnet-4-5"):
        """Create a mock nanobot config."""
        config = MagicMock()
        config.agents.defaults.model = model
        config.agents.defaults.max_tool_iterations = 10
        config.tools.mcp_servers = {}

        provider = MagicMock()
        provider.api_key = "test-api-key"
        provider.api_base = None
        config.get_provider = MagicMock(return_value=provider)

        return config

    def _create_mock_merged_config(self, model_name: str | None = None, api_key: str | None = None):
        """Create a mock merged DeepAgentsConfig."""
        from nanobot_deep.config.schema import (
            DeepAgentsConfig,
            DeepAgentsModelConfig,
        )

        config = DeepAgentsConfig()
        config.model = DeepAgentsModelConfig(
            name=model_name,
            api_key=api_key,
            max_tokens=2000,
            temperature=0.1,
        )
        return config

    def test_uses_litellm_model_names(self):
        """Test that model names are passed to ChatLiteLLM without parsing."""
        from nanobot_deep.agent.factory import _init_model

        merged_config = self._create_mock_merged_config()

        mock_result = MagicMock()
        mock_result.model = MagicMock()
        mock_result.model.model = "anthropic/claude-sonnet-4-5"
        mock_result.provider = "anthropic"
        mock_result.model_name = "claude-sonnet-4-5"

        with patch("nanobot_deep.agent.factory.create_model", return_value=mock_result):
            model, result = _init_model(merged_config)
            assert model.model == "anthropic/claude-sonnet-4-5"

    def test_custom_provider_model(self):
        """Test custom provider model name is preserved."""
        from nanobot_deep.agent.factory import _init_model

        merged_config = self._create_mock_merged_config()

        mock_result = MagicMock()
        mock_result.model = MagicMock()
        mock_result.model.model = "zai/glm-4.7"
        mock_result.provider = "zai"
        mock_result.model_name = "glm-4.7"

        with patch("nanobot_deep.agent.factory.create_model", return_value=mock_result):
            model, result = _init_model(merged_config)
            assert model.model == "zai/glm-4.7"

    def test_model_config_override(self):
        """Test that deepagents config model overrides nanobot config."""
        from nanobot_deep.agent.factory import _init_model

        merged_config = self._create_mock_merged_config(model_name="openai/gpt-4o")

        mock_result = MagicMock()
        mock_result.model = MagicMock()
        mock_result.model.model = "openai/gpt-4o"
        mock_result.provider = "openai"
        mock_result.model_name = "gpt-4o"

        with patch("nanobot_deep.agent.factory.create_model", return_value=mock_result):
            model, result = _init_model(merged_config)
            assert model.model == "openai/gpt-4o"

    def test_default_model_when_none(self):
        """Test default model is used when none specified."""
        from nanobot_deep.agent.factory import _init_model

        merged_config = self._create_mock_merged_config(model_name=None)

        mock_result = MagicMock()
        mock_result.model = MagicMock()
        mock_result.model.model = "anthropic/claude-sonnet-4-5"
        mock_result.provider = "anthropic"
        mock_result.model_name = "claude-sonnet-4-5"

        with patch("nanobot_deep.agent.factory.create_model", return_value=mock_result):
            model, result = _init_model(merged_config)
            assert model.model == "anthropic/claude-sonnet-4-5"
