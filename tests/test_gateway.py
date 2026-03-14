"""Unit tests for the gateway module."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestDeepGateway:
    """Tests for DeepGateway class."""

    def test_gateway_initialization(self, tmp_path):
        """Test gateway initializes correctly."""
        from nanobot_deep.gateway import DeepGateway

        config = self._create_mock_config(tmp_path)

        with patch("nanobot.channels.manager.ChannelManager"):
            gateway = DeepGateway(config, tmp_path)

            assert gateway.config == config
            assert gateway.workspace == tmp_path
            assert gateway.agent is None
            assert gateway.checkpointer is None
            assert gateway._running is False

    def test_gateway_setup_checkpointer(self, tmp_path):
        """Test checkpointer setup."""
        from nanobot_deep.gateway import DeepGateway

        config = self._create_mock_config(tmp_path)

        with patch("nanobot.channels.manager.ChannelManager"):
            gateway = DeepGateway(config, tmp_path)

            with patch(
                "nanobot_deep.langgraph.checkpointer.SessionCheckpointer"
            ) as mock_checkpointer_cls:
                mock_checkpointer = MagicMock()
                mock_checkpointer_cls.return_value = mock_checkpointer

                checkpointer = gateway._setup_checkpointer()

                assert checkpointer is not None
                mock_checkpointer_cls.assert_called_once()

    def test_gateway_stop(self, tmp_path):
        """Test gateway stop signal."""
        from nanobot_deep.gateway import DeepGateway

        config = self._create_mock_config(tmp_path)

        with patch("nanobot.channels.manager.ChannelManager"):
            gateway = DeepGateway(config, tmp_path)
            gateway._running = True

            gateway.stop()

            assert gateway._running is False
            assert gateway._shutdown_event.is_set()

    @pytest.mark.asyncio
    async def test_process_inbound_message(self, tmp_path):
        """Test processing an inbound message."""
        from nanobot.bus.events import InboundMessage, OutboundMessage

        from nanobot_deep.gateway import DeepGateway

        config = self._create_mock_config(tmp_path)

        with patch("nanobot.channels.manager.ChannelManager"):
            gateway = DeepGateway(config, tmp_path)

            mock_agent = AsyncMock()
            mock_agent.process.return_value = OutboundMessage(
                channel="cli",
                chat_id="test",
                content="Test response",
            )
            gateway.agent = mock_agent

            msg = InboundMessage(
                channel="cli",
                sender_id="user",
                chat_id="test",
                content="Hello",
            )

            await gateway._process_inbound(msg)

            mock_agent.process.assert_called_once_with(msg)
            assert gateway.bus.outbound_size == 1

    @pytest.mark.asyncio
    async def test_process_inbound_error_handling(self, tmp_path):
        """Test error handling when processing fails."""
        from nanobot.bus.events import InboundMessage

        from nanobot_deep.gateway import DeepGateway

        config = self._create_mock_config(tmp_path)

        with patch("nanobot.channels.manager.ChannelManager"):
            gateway = DeepGateway(config, tmp_path)

            mock_agent = AsyncMock()
            mock_agent.process.side_effect = Exception("Test error")
            gateway.agent = mock_agent

            msg = InboundMessage(
                channel="cli",
                sender_id="user",
                chat_id="test",
                content="Hello",
            )

            await gateway._process_inbound(msg)

            assert gateway.bus.outbound_size == 1

    @pytest.mark.asyncio
    async def test_consume_inbound_loop_stops_on_cancel(self, tmp_path):
        """Test that consume loop stops when gateway stops."""
        from nanobot_deep.gateway import DeepGateway

        config = self._create_mock_config(tmp_path)

        with patch("nanobot.channels.manager.ChannelManager"):
            gateway = DeepGateway(config, tmp_path)
            gateway._running = True

            async def stop_after_delay():
                await asyncio.sleep(0.05)
                gateway._running = False

            await asyncio.gather(
                stop_after_delay(),
                gateway._consume_inbound_loop(),
            )

            assert gateway._running is False

    def _create_mock_config(self, workspace_path):
        """Create a mock config with required attributes."""
        config = MagicMock()
        config.workspace_path = workspace_path
        config.channels = MagicMock()
        config.channels.telegram = MagicMock()
        config.channels.telegram.enabled = False
        config.channels.whatsapp = MagicMock()
        config.channels.whatsapp.enabled = False
        config.channels.discord = MagicMock()
        config.channels.discord.enabled = False
        config.channels.feishu = MagicMock()
        config.channels.feishu.enabled = False
        config.channels.mochat = MagicMock()
        config.channels.mochat.enabled = False
        config.channels.slack = MagicMock()
        config.channels.slack.enabled = False
        config.channels.dingtalk = MagicMock()
        config.channels.dingtalk.enabled = False
        config.channels.qq = MagicMock()
        config.channels.qq.enabled = False
        config.channels.email = MagicMock()
        config.channels.email.enabled = False
        config.agents = MagicMock()
        config.agents.defaults = MagicMock()
        config.agents.defaults.model = "test-model"
        config.agents.defaults.max_tool_iterations = 10
        config.tools = MagicMock()
        config.tools.mcp_servers = {}
        return config


class TestRunGateway:
    """Tests for run_gateway function."""

    @pytest.mark.asyncio
    async def test_run_gateway_creates_and_runs(self, tmp_path):
        """Test that run_gateway creates gateway and runs it."""
        from nanobot_deep.gateway import DeepGateway, run_gateway

        config = MagicMock()
        config.workspace_path = tmp_path
        config.channels = MagicMock()
        config.channels.telegram = MagicMock()
        config.channels.telegram.enabled = False
        config.channels.whatsapp = MagicMock()
        config.channels.whatsapp.enabled = False
        config.channels.discord = MagicMock()
        config.channels.discord.enabled = False
        config.channels.feishu = MagicMock()
        config.channels.feishu.enabled = False
        config.channels.mochat = MagicMock()
        config.channels.mochat.enabled = False
        config.channels.slack = MagicMock()
        config.channels.slack.enabled = False
        config.channels.dingtalk = MagicMock()
        config.channels.dingtalk.enabled = False
        config.channels.qq = MagicMock()
        config.channels.qq.enabled = False
        config.channels.email = MagicMock()
        config.channels.email.enabled = False

        with patch("nanobot.channels.manager.ChannelManager"):
            with patch.object(DeepGateway, "run", new_callable=AsyncMock) as mock_run:
                await run_gateway(config, tmp_path, verbose=False)
                mock_run.assert_called_once()


class TestGatewayIntegration:
    """Integration tests for gateway with DeepAgent."""

    @pytest.mark.asyncio
    async def test_gateway_with_mock_agent(self, tmp_path):
        """Test gateway with mocked DeepAgent."""
        from nanobot.bus.events import InboundMessage, OutboundMessage

        from nanobot_deep.gateway import DeepGateway

        config = MagicMock()
        config.workspace_path = tmp_path
        config.channels = MagicMock()
        config.channels.telegram = MagicMock()
        config.channels.telegram.enabled = False
        config.channels.whatsapp = MagicMock()
        config.channels.whatsapp.enabled = False
        config.channels.discord = MagicMock()
        config.channels.discord.enabled = False
        config.channels.feishu = MagicMock()
        config.channels.feishu.enabled = False
        config.channels.mochat = MagicMock()
        config.channels.mochat.enabled = False
        config.channels.slack = MagicMock()
        config.channels.slack.enabled = False
        config.channels.dingtalk = MagicMock()
        config.channels.dingtalk.enabled = False
        config.channels.qq = MagicMock()
        config.channels.qq.enabled = False
        config.channels.email = MagicMock()
        config.channels.email.enabled = False
        config.agents = MagicMock()
        config.agents.defaults = MagicMock()
        config.agents.defaults.model = "test-model"
        config.agents.defaults.max_tool_iterations = 10
        config.tools = MagicMock()
        config.tools.mcp_servers = {}

        with patch("nanobot.channels.manager.ChannelManager"):
            gateway = DeepGateway(config, tmp_path)

            mock_agent = AsyncMock()
            mock_agent.process.return_value = OutboundMessage(
                channel="cli",
                chat_id="test",
                content="Response",
            )
            gateway.agent = mock_agent

            msg = InboundMessage(
                channel="cli",
                sender_id="user",
                chat_id="test",
                content="Test message",
            )

            await gateway._process_inbound(msg)

            mock_agent.process.assert_called_once()
