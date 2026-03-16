"""Unit tests for DeepAgent class."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestDeepAgentInit:
    """Tests for DeepAgent initialization."""

    def test_init_without_deepagents_raises(self, tmp_path):
        """Test that initialization fails without deepagents installed."""
        with patch("nanobot_deep.agent.deep_agent.DEEPAGENTS_AVAILABLE", False):
            with patch("nanobot_deep.agent.deep_agent.create_deep_agent", None):
                from nanobot_deep.agent.deep_agent import DeepAgent

                config = self._create_mock_config(tmp_path)
                with pytest.raises(ImportError, match="deepagents is not installed"):
                    DeepAgent(workspace=tmp_path, config=config)

    def test_init_with_valid_config(self, tmp_path):
        """Test successful initialization with valid config."""
        from nanobot_deep.agent.deep_agent import DeepAgent
        from nanobot_deep.config.schema import DeepAgentsConfig

        config = self._create_mock_config(tmp_path)
        dg_config = DeepAgentsConfig()

        with patch("nanobot_deep.agent.deep_agent.DEEPAGENTS_AVAILABLE", True):
            agent = DeepAgent(
                workspace=tmp_path,
                config=config,
                checkpointer=None,
                deepagents_config=dg_config,
            )

            assert agent.workspace == tmp_path
            assert agent.config == config
            assert agent.checkpointer is None
            assert agent._agent is None

    def test_init_merges_nanobot_config(self, tmp_path):
        """Test that config is merged with nanobot config."""
        from nanobot_deep.agent.deep_agent import DeepAgent
        from nanobot_deep.config.schema import DeepAgentsConfig

        config = self._create_mock_config(tmp_path)
        dg_config = DeepAgentsConfig()

        with patch("nanobot_deep.agent.deep_agent.DEEPAGENTS_AVAILABLE", True):
            agent = DeepAgent(
                workspace=tmp_path,
                config=config,
                deepagents_config=dg_config,
            )

            assert agent.dg_config is not None

    def _create_mock_config(self, workspace_path):
        """Create a mock config with required attributes."""
        config = MagicMock()
        config.workspace_path = workspace_path
        config.agents = MagicMock()
        config.agents.defaults = MagicMock()
        config.agents.defaults.model = "test-model"
        config.agents.defaults.max_tool_iterations = 10
        config.tools = MagicMock()
        config.tools.mcp_servers = {}
        config.get_provider = MagicMock(return_value=None)
        return config


class TestDeepAgentModelInit:
    """Tests for model initialization."""

    def test_model_init_from_deepagents_config(self, tmp_path):
        """Test model initialization from deepagents config."""
        from nanobot_deep.agent.deep_agent import DeepAgent
        from nanobot_deep.config.schema import DeepAgentsConfig, DeepAgentsModelConfig

        config = self._create_mock_config(tmp_path)
        dg_config = DeepAgentsConfig(
            model=DeepAgentsModelConfig(
                name="openai/gpt-4",
                max_tokens=1000,
                temperature=0.5,
            )
        )

        with patch("nanobot_deep.agent.deep_agent.DEEPAGENTS_AVAILABLE", True):
            agent = DeepAgent(
                workspace=tmp_path,
                config=config,
                deepagents_config=dg_config,
            )

            with patch("langchain_litellm.ChatLiteLLM") as mock_llm:
                agent._init_model()
                mock_llm.assert_called_once()
                call_kwargs = mock_llm.call_args.kwargs
                assert call_kwargs["model"] == "openai/gpt-4"
                assert call_kwargs["max_tokens"] == 1000
                assert call_kwargs["temperature"] == 0.5

    def test_model_init_fallback_to_nanobot_config(self, tmp_path):
        """Test model initialization falls back to nanobot config."""
        from nanobot_deep.agent.deep_agent import DeepAgent
        from nanobot_deep.config.schema import DeepAgentsConfig

        config = self._create_mock_config(tmp_path)
        config.agents.defaults.model = "anthropic/claude-sonnet-4-5"

        provider_config = MagicMock()
        provider_config.api_key = "test-key"
        provider_config.api_base = "https://api.test.com"
        config.get_provider = MagicMock(return_value=provider_config)

        dg_config = DeepAgentsConfig()

        with patch("nanobot_deep.agent.deep_agent.DEEPAGENTS_AVAILABLE", True):
            agent = DeepAgent(
                workspace=tmp_path,
                config=config,
                deepagents_config=dg_config,
            )

            with patch("langchain_litellm.ChatLiteLLM") as mock_llm:
                agent._init_model()
                call_kwargs = mock_llm.call_args.kwargs
                assert call_kwargs["model"] == "anthropic/claude-sonnet-4-5"
                assert call_kwargs["api_key"] == "test-key"
                assert call_kwargs["api_base"] == "https://api.test.com"

    def test_model_init_default_model(self, tmp_path):
        """Test model initialization uses default when no model specified."""
        from nanobot_deep.agent.deep_agent import DeepAgent
        from nanobot_deep.config.schema import DeepAgentsConfig

        config = self._create_mock_config(tmp_path)
        config.agents.defaults.model = None
        config.get_provider = MagicMock(return_value=None)

        dg_config = DeepAgentsConfig()

        with patch("nanobot_deep.agent.deep_agent.DEEPAGENTS_AVAILABLE", True):
            agent = DeepAgent(
                workspace=tmp_path,
                config=config,
                deepagents_config=dg_config,
            )

            with patch("langchain_litellm.ChatLiteLLM") as mock_llm:
                agent._init_model()
                call_kwargs = mock_llm.call_args.kwargs
                assert call_kwargs["model"] == "anthropic/claude-sonnet-4-5"

    def _create_mock_config(self, workspace_path):
        config = MagicMock()
        config.workspace_path = workspace_path
        config.agents = MagicMock()
        config.agents.defaults = MagicMock()
        config.agents.defaults.model = "test-model"
        config.agents.defaults.max_tool_iterations = 10
        config.tools = MagicMock()
        config.tools.mcp_servers = {}
        config.get_provider = MagicMock(return_value=None)
        return config


class TestDeepAgentProcess:
    """Tests for message processing."""

    @pytest.mark.asyncio
    async def test_process_returns_outbound_message(self, tmp_path):
        """Test that process returns an OutboundMessage."""
        from nanobot.bus.events import InboundMessage, OutboundMessage

        from nanobot_deep.agent.deep_agent import DeepAgent
        from nanobot_deep.config.schema import DeepAgentsConfig

        config = self._create_mock_config(tmp_path)
        dg_config = DeepAgentsConfig()

        with patch("nanobot_deep.agent.deep_agent.DEEPAGENTS_AVAILABLE", True):
            agent = DeepAgent(
                workspace=tmp_path,
                config=config,
                deepagents_config=dg_config,
            )

            mock_compiled = AsyncMock()
            mock_compiled.ainvoke.return_value = {
                "messages": [MagicMock(content="Test response", type="ai")]
            }
            agent._agent = mock_compiled

            msg = InboundMessage(
                channel="cli",
                sender_id="user",
                chat_id="test",
                content="Hello",
            )

            response = await agent.process(msg)

            assert isinstance(response, OutboundMessage)
            assert response.channel == "cli"
            assert response.chat_id == "test"

    @pytest.mark.asyncio
    async def test_process_handles_exception(self, tmp_path):
        """Test that process handles exceptions gracefully."""
        from nanobot.bus.events import InboundMessage, OutboundMessage

        from nanobot_deep.agent.deep_agent import DeepAgent
        from nanobot_deep.config.schema import DeepAgentsConfig

        config = self._create_mock_config(tmp_path)
        dg_config = DeepAgentsConfig()

        with patch("nanobot_deep.agent.deep_agent.DEEPAGENTS_AVAILABLE", True):
            agent = DeepAgent(
                workspace=tmp_path,
                config=config,
                deepagents_config=dg_config,
            )

            mock_compiled = AsyncMock()
            mock_compiled.ainvoke.side_effect = Exception("API error")
            agent._agent = mock_compiled

            msg = InboundMessage(
                channel="cli",
                sender_id="user",
                chat_id="test",
                content="Hello",
            )

            response = await agent.process(msg)

            assert isinstance(response, OutboundMessage)
            assert "error" in response.content.lower()

    @pytest.mark.asyncio
    async def test_process_with_progress_callback(self, tmp_path):
        """Test that process calls progress callback."""
        from nanobot.bus.events import InboundMessage

        from nanobot_deep.agent.deep_agent import DeepAgent
        from nanobot_deep.config.schema import DeepAgentsConfig

        config = self._create_mock_config(tmp_path)
        dg_config = DeepAgentsConfig()

        with patch("nanobot_deep.agent.deep_agent.DEEPAGENTS_AVAILABLE", True):
            agent = DeepAgent(
                workspace=tmp_path,
                config=config,
                deepagents_config=dg_config,
            )

            mock_compiled = AsyncMock()
            mock_compiled.astream_events = AsyncMock()
            mock_compiled.astream_events.return_value = self._mock_stream_events()
            agent._agent = mock_compiled

            msg = InboundMessage(
                channel="cli",
                sender_id="user",
                chat_id="test",
                content="Hello",
            )

            progress_calls = []

            async def on_progress(text: str, is_tool_hint: bool = False):
                progress_calls.append((text, is_tool_hint))

            await agent.process(msg, on_progress=on_progress)

    def _mock_stream_events(self):
        """Generate mock stream events."""

        async def _gen():
            yield {
                "event": "on_chain_end",
                "name": "LangGraph",
                "data": {"output": {"messages": []}},
            }

        return _gen()

    def _create_mock_config(self, workspace_path):
        config = MagicMock()
        config.workspace_path = workspace_path
        config.agents = MagicMock()
        config.agents.defaults = MagicMock()
        config.agents.defaults.model = "test-model"
        config.agents.defaults.max_tool_iterations = 10
        config.tools = MagicMock()
        config.tools.mcp_servers = {}
        config.get_provider = MagicMock(return_value=None)
        return config


class TestDeepAgentSession:
    """Tests for session management."""

    def test_clear_session_calls_checkpointer(self, tmp_path):
        """Test clear_session calls checkpointer.delete_thread."""
        from nanobot_deep.agent.deep_agent import DeepAgent
        from nanobot_deep.config.schema import DeepAgentsConfig

        config = self._create_mock_config(tmp_path)
        dg_config = DeepAgentsConfig()

        mock_checkpointer = MagicMock()
        mock_checkpointer.delete_thread = MagicMock()

        with patch("nanobot_deep.agent.deep_agent.DEEPAGENTS_AVAILABLE", True):
            agent = DeepAgent(
                workspace=tmp_path,
                config=config,
                checkpointer=mock_checkpointer,
                deepagents_config=dg_config,
            )

            agent.clear_session("test-session")

            mock_checkpointer.delete_thread.assert_called_once_with("test-session")

    def test_clear_session_handles_no_checkpointer(self, tmp_path):
        """Test clear_session handles missing checkpointer."""
        from nanobot_deep.agent.deep_agent import DeepAgent
        from nanobot_deep.config.schema import DeepAgentsConfig

        config = self._create_mock_config(tmp_path)
        dg_config = DeepAgentsConfig()

        with patch("nanobot_deep.agent.deep_agent.DEEPAGENTS_AVAILABLE", True):
            agent = DeepAgent(
                workspace=tmp_path,
                config=config,
                checkpointer=None,
                deepagents_config=dg_config,
            )

            agent.clear_session("test-session")

    def test_get_history_returns_empty_without_checkpointer(self, tmp_path):
        """Test get_history returns empty list without checkpointer."""
        from nanobot_deep.agent.deep_agent import DeepAgent
        from nanobot_deep.config.schema import DeepAgentsConfig

        config = self._create_mock_config(tmp_path)
        dg_config = DeepAgentsConfig()

        with patch("nanobot_deep.agent.deep_agent.DEEPAGENTS_AVAILABLE", True):
            agent = DeepAgent(
                workspace=tmp_path,
                config=config,
                checkpointer=None,
                deepagents_config=dg_config,
            )

            history = agent.get_history("test-session")

            assert history == []

    def _create_mock_config(self, workspace_path):
        config = MagicMock()
        config.workspace_path = workspace_path
        config.agents = MagicMock()
        config.agents.defaults = MagicMock()
        config.agents.defaults.model = "test-model"
        config.agents.defaults.max_tool_iterations = 10
        config.tools = MagicMock()
        config.tools.mcp_servers = {}
        config.get_provider = MagicMock(return_value=None)
        return config


class TestDeepAgentClose:
    """Tests for cleanup."""

    @pytest.mark.asyncio
    async def test_close_cleans_up_mcp(self, tmp_path):
        """Test close cleans up MCP connections."""
        from nanobot_deep.agent.deep_agent import DeepAgent
        from nanobot_deep.config.schema import DeepAgentsConfig

        config = self._create_mock_config(tmp_path)
        dg_config = DeepAgentsConfig()

        with patch("nanobot_deep.agent.deep_agent.DEEPAGENTS_AVAILABLE", True):
            agent = DeepAgent(
                workspace=tmp_path,
                config=config,
                deepagents_config=dg_config,
            )

            mock_stack = AsyncMock()
            mock_stack.aclose = AsyncMock()
            agent._mcp_stack = mock_stack

            await agent.close()

            mock_stack.aclose.assert_called_once()
            assert agent._mcp_stack is None
            assert agent._mcp_connected is False

    @pytest.mark.asyncio
    async def test_close_handles_exception(self, tmp_path):
        """Test close handles exceptions during cleanup."""
        from nanobot_deep.agent.deep_agent import DeepAgent
        from nanobot_deep.config.schema import DeepAgentsConfig

        config = self._create_mock_config(tmp_path)
        dg_config = DeepAgentsConfig()

        with patch("nanobot_deep.agent.deep_agent.DEEPAGENTS_AVAILABLE", True):
            agent = DeepAgent(
                workspace=tmp_path,
                config=config,
                deepagents_config=dg_config,
            )

            mock_stack = AsyncMock()
            mock_stack.aclose.side_effect = Exception("Cleanup error")
            agent._mcp_stack = mock_stack

            await agent.close()

            assert agent._mcp_stack is None

    def _create_mock_config(self, workspace_path):
        config = MagicMock()
        config.workspace_path = workspace_path
        config.agents = MagicMock()
        config.agents.defaults = MagicMock()
        config.agents.defaults.model = "test-model"
        config.agents.defaults.max_tool_iterations = 10
        config.tools = MagicMock()
        config.tools.mcp_servers = {}
        config.get_provider = MagicMock(return_value=None)
        return config
