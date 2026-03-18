"""Unit tests for Langfuse configuration."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from nanobot_deep.config.schema import DeepAgentsConfig, DeepAgentsLangfuseConfig


class TestDeepAgentsLangfuseConfig:
    """Tests for DeepAgentsLangfuseConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = DeepAgentsLangfuseConfig()

        assert config.enabled is False
        assert config.public_key is None
        assert config.secret_key is None
        assert config.host == "http://localhost:3000"
        assert config.environment == "development"
        assert config.session_id is None
        assert config.user_id is None
        assert config.tags == []
        assert config.metadata == {}

    def test_custom_config(self):
        """Test custom configuration values."""
        config = DeepAgentsLangfuseConfig(
            enabled=True,
            public_key="pk-lf-test",
            secret_key="sk-lf-test",
            host="https://cloud.langfuse.com",
            environment="production",
            session_id="session-123",
            user_id="user-456",
            tags=["tag1", "tag2"],
            metadata={"key": "value"},
        )

        assert config.enabled is True
        assert config.public_key == "pk-lf-test"
        assert config.secret_key == "sk-lf-test"
        assert config.host == "https://cloud.langfuse.com"
        assert config.environment == "production"
        assert config.session_id == "session-123"
        assert config.user_id == "user-456"
        assert config.tags == ["tag1", "tag2"]
        assert config.metadata == {"key": "value"}

    def test_config_in_deep_agents_config(self):
        """Test Langfuse config is included in DeepAgentsConfig."""
        config = DeepAgentsConfig(
            langfuse=DeepAgentsLangfuseConfig(
                enabled=True,
                public_key="pk-test",
                secret_key="sk-test",
            )
        )

        assert config.langfuse.enabled is True
        assert config.langfuse.public_key == "pk-test"
        assert config.langfuse.secret_key == "sk-test"

    def test_config_from_dict(self):
        """Test loading config from dictionary."""
        config = DeepAgentsConfig.model_validate(
            {
                "langfuse": {
                    "enabled": True,
                    "public_key": "pk-dict",
                    "secret_key": "sk-dict",
                    "host": "http://custom:3000",
                }
            }
        )

        assert config.langfuse.enabled is True
        assert config.langfuse.public_key == "pk-dict"
        assert config.langfuse.secret_key == "sk-dict"
        assert config.langfuse.host == "http://custom:3000"


class TestLangfuseHandlerCreation:
    """Tests for Langfuse handler creation."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock nanobot config."""
        config = MagicMock()
        config.agents.defaults.model = "test-model"
        config.tools.mcp_servers = {}
        config.get_provider.return_value = None
        return config

    @pytest.fixture
    def mock_deepagents_config(self):
        """Create a mock DeepAgentsConfig with Langfuse enabled."""
        return DeepAgentsConfig(
            langfuse=DeepAgentsLangfuseConfig(
                enabled=True,
                public_key="pk-test",
                secret_key="sk-test",
                host="http://localhost:3000",
            )
        )

    def test_handler_not_created_when_disabled(self, mock_config):
        """Test handler is not created when Langfuse is disabled."""
        with patch.dict(os.environ, {}, clear=True):
            from nanobot_deep.agent.deep_agent import DeepAgent

            config = DeepAgentsConfig(langfuse=DeepAgentsLangfuseConfig(enabled=False))

            with patch.object(DeepAgent, "_create_agent"):
                with patch.object(DeepAgent, "_init_model"):
                    with patch.object(DeepAgent, "_init_backend"):
                        agent = DeepAgent(
                            workspace=Path("/tmp/test"),
                            config=mock_config,
                            deepagents_config=config,
                        )
                        handler = agent._get_langfuse_handler()
                        assert handler is None

    def test_handler_not_created_without_credentials(self, mock_config):
        """Test handler is not created when credentials are missing."""
        with patch.dict(os.environ, {}, clear=True):
            from nanobot_deep.agent.deep_agent import DeepAgent

            config = DeepAgentsConfig(langfuse=DeepAgentsLangfuseConfig(enabled=True))

            with patch.object(DeepAgent, "_create_agent"):
                with patch.object(DeepAgent, "_init_model"):
                    with patch.object(DeepAgent, "_init_backend"):
                        agent = DeepAgent(
                            workspace=Path("/tmp/test"),
                            config=mock_config,
                            deepagents_config=config,
                        )
                        handler = agent._get_langfuse_handler()
                        assert handler is None

    def test_handler_uses_env_vars(self, mock_config):
        """Test handler uses environment variables when config is missing."""
        with patch.dict(
            os.environ,
            {
                "LANGFUSE_PUBLIC_KEY": "pk-env",
                "LANGFUSE_SECRET_KEY": "sk-env",
                "LANGFUSE_HOST": "http://env-host:3000",
            },
            clear=True,
        ):
            from nanobot_deep.agent.deep_agent import DeepAgent

            config = DeepAgentsConfig(langfuse=DeepAgentsLangfuseConfig(enabled=True))

            with patch.object(DeepAgent, "_create_agent"):
                with patch.object(DeepAgent, "_init_model"):
                    with patch.object(DeepAgent, "_init_backend"):
                        with patch("nanobot_deep.agent.deep_agent.LANGFUSE_AVAILABLE", True):
                            with patch(
                                "nanobot_deep.agent.deep_agent.LangfuseCallbackHandler"
                            ) as mock_handler:
                                mock_handler.return_value = MagicMock()
                                agent = DeepAgent(
                                    workspace=Path("/tmp/test"),
                                    config=mock_config,
                                    deepagents_config=config,
                                )
                                agent._get_langfuse_handler()
                                mock_handler.assert_called_once()
                                call_kwargs = mock_handler.call_args[1]
                                assert call_kwargs["public_key"] == "pk-env"
                                assert call_kwargs["secret_key"] == "sk-env"
                                assert call_kwargs["host"] == "http://env-host:3000"

    def test_handler_not_created_when_langfuse_not_available(self, mock_config):
        """Test handler is None when langfuse package is not installed."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("nanobot_deep.agent.deep_agent.LANGFUSE_AVAILABLE", False):
                from nanobot_deep.agent.deep_agent import DeepAgent

                config = DeepAgentsConfig(
                    langfuse=DeepAgentsLangfuseConfig(
                        enabled=True,
                        public_key="pk-test",
                        secret_key="sk-test",
                    )
                )

                with patch.object(DeepAgent, "_create_agent"):
                    with patch.object(DeepAgent, "_init_model"):
                        with patch.object(DeepAgent, "_init_backend"):
                            agent = DeepAgent(
                                workspace=Path("/tmp/test"),
                                config=mock_config,
                                deepagents_config=config,
                            )
                            handler = agent._get_langfuse_handler()
                            assert handler is None
