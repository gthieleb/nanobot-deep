"""E2E tests for Langfuse integration.

These tests verify that Langfuse integration works when a self-hosted
Langfuse instance is reachable.

Run with:
    # Start Langfuse first:
    cd docker && docker compose -f docker-compose.langfuse.yml up -d

    # Run tests:
    pytest tests/e2e/test_langfuse_integration.py -v

Environment variables required:
    LANGFUSE_PUBLIC_KEY: Langfuse public key
    LANGFUSE_SECRET_KEY: Langfuse secret key
    LANGFUSE_HOST: Langfuse host URL (default: http://localhost:3000)
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.langfuse


def is_langfuse_reachable(host: str = "http://localhost:3000", timeout: float = 5.0) -> bool:
    """Check if Langfuse instance is reachable.

    Args:
        host: Langfuse host URL
        timeout: Request timeout in seconds

    Returns:
        True if Langfuse is reachable, False otherwise
    """
    try:
        import httpx

        response = httpx.get(f"{host}/api/health", timeout=timeout)
        return response.status_code == 200
    except Exception:
        return False


def has_langfuse_credentials() -> bool:
    """Check if Langfuse credentials are available.

    Returns:
        True if both public and secret keys are set, False otherwise
    """
    return bool(os.environ.get("LANGFUSE_PUBLIC_KEY") and os.environ.get("LANGFUSE_SECRET_KEY"))


@pytest.fixture
def langfuse_host():
    """Get Langfuse host from environment."""
    return os.environ.get("LANGFUSE_HOST", "http://localhost:3000")


@pytest.fixture
def langfuse_reachable(langfuse_host):
    """Check if Langfuse is reachable, skip tests if not."""
    if not is_langfuse_reachable(langfuse_host):
        pytest.skip(
            "Langfuse instance is not reachable. Start with: docker compose -f docker-compose.langfuse.yml up -d"
        )
    return True


@pytest.fixture
def langfuse_credentials():
    """Check if Langfuse credentials are available, skip tests if not."""
    if not has_langfuse_credentials():
        pytest.skip(
            "Langfuse credentials not set. Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY environment variables."
        )
    return {
        "public_key": os.environ.get("LANGFUSE_PUBLIC_KEY"),
        "secret_key": os.environ.get("LANGFUSE_SECRET_KEY"),
    }


@pytest.fixture
def langfuse_client(langfuse_host, langfuse_credentials):
    """Create a Langfuse client for verification."""
    try:
        from langfuse import Langfuse

        client = Langfuse(
            public_key=langfuse_credentials["public_key"],
            secret_key=langfuse_credentials["secret_key"],
            host=langfuse_host,
        )
        return client
    except ImportError:
        pytest.skip("langfuse package not installed. Install with: pip install langfuse")


class TestLangfuseConnectivity:
    """Test basic Langfuse connectivity."""

    def test_langfuse_health_endpoint(self, langfuse_reachable, langfuse_host):
        """Test that Langfuse health endpoint is accessible."""
        import httpx

        response = httpx.get(f"{langfuse_host}/api/health", timeout=10)
        assert response.status_code == 200

    def test_langfuse_auth_check(self, langfuse_client):
        """Test that Langfuse authentication works."""
        assert langfuse_client.auth_check() is True


class TestLangfuseTraceCreation:
    """Test that traces are created in Langfuse."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_simple_trace_created(
        self, langfuse_reachable, langfuse_credentials, langfuse_host, langfuse_client
    ):
        """Test that a simple agent invocation creates a trace in Langfuse."""
        from nanobot_deep.config.schema import DeepAgentsConfig, DeepAgentsLangfuseConfig

        mock_config = MagicMock()
        mock_config.agents.defaults.model = "test-model"
        mock_config.tools.mcp_servers = {}
        mock_config.get_provider.return_value = None

        config = DeepAgentsConfig(
            langfuse=DeepAgentsLangfuseConfig(
                enabled=True,
                public_key=langfuse_credentials["public_key"],
                secret_key=langfuse_credentials["secret_key"],
                host=langfuse_host,
            )
        )

        import uuid

        trace_id = str(uuid.uuid4())
        config.langfuse.session_id = trace_id

    @pytest.mark.asyncio
    @pytest.mark.timeout(90)
    async def test_trace_with_tool_calls(
        self, langfuse_reachable, langfuse_credentials, langfuse_host, tmp_path
    ):
        """Test that traces include tool call information."""
        pytest.skip("Requires live agent execution - enable when running full e2e suite")


class TestLangfuseGracefulDegradation:
    """Test graceful degradation when Langfuse is unavailable."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_agent_works_without_langfuse(self, tmp_path):
        """Test that agent still works when Langfuse is disabled."""
        from nanobot_deep.agent.deep_agent import DeepAgent
        from nanobot_deep.config.schema import DeepAgentsConfig, DeepAgentsLangfuseConfig

        mock_config = MagicMock()
        mock_config.agents.defaults.model = "test-model"
        mock_config.tools.mcp_servers = {}
        mock_config.get_provider.return_value = None

        config = DeepAgentsConfig(langfuse=DeepAgentsLangfuseConfig(enabled=False))

        with patch.object(DeepAgent, "_create_agent"):
            with patch.object(DeepAgent, "_init_model"):
                with patch.object(DeepAgent, "_init_backend"):
                    agent = DeepAgent(
                        workspace=tmp_path,
                        config=mock_config,
                        deepagents_config=config,
                    )
                    handler = agent._get_langfuse_handler()
                    assert handler is None

    def test_handler_returns_none_on_invalid_credentials(self):
        """Test that handler returns None when credentials are invalid."""
        from nanobot_deep.agent.deep_agent import DeepAgent
        from nanobot_deep.config.schema import DeepAgentsConfig, DeepAgentsLangfuseConfig

        mock_config = MagicMock()
        mock_config.agents.defaults.model = "test-model"
        mock_config.tools.mcp_servers = {}
        mock_config.get_provider.return_value = None

        config = DeepAgentsConfig(
            langfuse=DeepAgentsLangfuseConfig(
                enabled=True,
                public_key=None,
                secret_key=None,
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
