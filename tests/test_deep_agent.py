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

    def test_model_init_uses_extra_kwargs(self, tmp_path):
        """Test model init passes extra kwargs to deepagents CLI."""
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

            mock_result = MagicMock(model=object(), provider="test", model_name="test")

            with patch(
                "deepagents_cli.config.create_model", return_value=mock_result
            ) as mock_create:
                model = agent._init_model()
                assert model is mock_result.model
                mock_create.assert_called_once()
                call_kwargs = mock_create.call_args.kwargs
                assert call_kwargs["extra_kwargs"]["max_tokens"] == 1000
                assert call_kwargs["extra_kwargs"]["temperature"] == 0.5

    def test_model_init_uses_env_model_spec(self, tmp_path, monkeypatch):
        """Test model init uses DEEPAGENTS_TEST_MODEL when set."""
        from nanobot_deep.agent.deep_agent import DeepAgent
        from nanobot_deep.config.schema import DeepAgentsConfig

        config = self._create_mock_config(tmp_path)
        dg_config = DeepAgentsConfig()

        monkeypatch.setenv("DEEPAGENTS_TEST_MODEL", "openai:gpt-4o-mini")

        with patch("nanobot_deep.agent.deep_agent.DEEPAGENTS_AVAILABLE", True):
            agent = DeepAgent(
                workspace=tmp_path,
                config=config,
                deepagents_config=dg_config,
            )

            mock_result = MagicMock(model=object(), provider="test", model_name="test")

            with patch(
                "deepagents_cli.config.create_model", return_value=mock_result
            ) as mock_create:
                agent._init_model()
                call_kwargs = mock_create.call_args.kwargs
                assert call_kwargs["model_spec"] == "openai:gpt-4o-mini"

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

            agent._connect_mcp = AsyncMock()

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

            agent._connect_mcp = AsyncMock()

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

            agent._connect_mcp = AsyncMock()

            mock_compiled = AsyncMock()
            mock_compiled.astream_events = MagicMock(return_value=self._mock_stream_events())
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

            assert ("streaming chunk", False) in progress_calls

    @pytest.mark.asyncio
    async def test_process_direct_streaming_callback(self, tmp_path):
        """Test process_direct forwards streaming output."""
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

            agent._connect_mcp = AsyncMock()

            mock_compiled = AsyncMock()
            mock_compiled.astream_events = MagicMock(return_value=self._mock_stream_events())
            agent._agent = mock_compiled

            progress_calls = []

            async def on_progress(text: str):
                progress_calls.append(text)

            await agent.process_direct("Hello", on_progress=on_progress)

            assert "streaming chunk" in progress_calls

    def _mock_stream_events(self):
        """Generate mock stream events."""

        async def _gen():
            class DummyChunk:
                def __init__(self, content: str):
                    self.content = content

            yield {
                "event": "on_chat_model_stream",
                "data": {"chunk": DummyChunk("streaming chunk")},
            }
            yield {
                "event": "on_chain_end",
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


class TestDeepAgentMcp:
    """Tests for MCP configuration handling."""

    @pytest.mark.asyncio
    async def test_connect_mcp_skips_when_disabled(self, tmp_path):
        from nanobot_deep.agent.deep_agent import DeepAgent
        from nanobot_deep.config.schema import DeepAgentsConfig

        config = self._create_mock_config(tmp_path)
        dg_config = DeepAgentsConfig()

        with patch("nanobot_deep.agent.deep_agent.DEEPAGENTS_AVAILABLE", True):
            agent = DeepAgent(
                workspace=tmp_path,
                config=config,
                deepagents_config=dg_config,
                no_mcp=True,
            )

            await agent._connect_mcp()

            assert agent._mcp_connected is True
            assert agent._tools == []

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

            mock_manager = AsyncMock()
            mock_manager.cleanup = AsyncMock()
            agent._mcp_session_manager = mock_manager

            await agent.close()

            mock_manager.cleanup.assert_called_once()
            assert agent._mcp_session_manager is None
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

            mock_manager = AsyncMock()
            mock_manager.cleanup.side_effect = Exception("Cleanup error")
            agent._mcp_session_manager = mock_manager

            await agent.close()

            assert agent._mcp_session_manager is None

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
