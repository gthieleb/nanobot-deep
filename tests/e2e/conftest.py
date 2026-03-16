"""Pytest fixtures for E2E tests with real LLM calls.

Usage:
    NANOBOT_TEST_CONFIG=~/.nanobot/config.json pytest tests/e2e/ -m live -v

The tests use a minimal deepagents config (tests/e2e/deepagents.test.json) to reduce
token usage and API costs. This config disables most middleware and uses low max_tokens.

To use your own deepagents config, set NANOBOT_TEST_DEEPAGENTS_CONFIG env var.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from nanobot.bus.queue import MessageBus
    from nanobot.config.schema import Config


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "live: tests that require real LLM API key (expensive)")
    config.addinivalue_line("markers", "slow: tests that take more than 60 seconds")
    config.addinivalue_line("markers", "timeout: set test timeout in seconds")


@pytest.fixture
def live_config_path() -> Path:
    """Get path to nanobot config.json."""
    config_path = os.environ.get("NANOBOT_TEST_CONFIG")
    if not config_path:
        pytest.skip("Set NANOBOT_TEST_CONFIG=/path/to/config.json to run live tests")

    path = Path(config_path).expanduser().resolve()
    if not path.exists():
        pytest.skip(f"Config file not found: {path}")
    return path


@pytest.fixture
def test_deepagents_config_path() -> Path:
    """Get path to test deepagents config."""
    config_path = os.environ.get("NANOBOT_TEST_DEEPAGENTS_CONFIG")
    if config_path:
        return Path(config_path).expanduser().resolve()
    return Path(__file__).parent / "deepagents.test.json"


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    """Create test workspace with basic structure."""
    ws = tmp_path / "workspace"
    ws.mkdir()
    (ws / "skills").mkdir()
    return ws


@pytest.fixture
def live_config(live_config_path: Path, workspace: Path) -> "Config":
    """Load nanobot config for live tests.

    Uses NANOBOT_TEST_CONFIG env var pointing to a real nanobot config.json.
    The workspace is overridden to a temp directory for test isolation.
    """
    from nanobot.config.loader import load_config, set_config_path

    set_config_path(live_config_path)
    config = load_config(live_config_path)

    config.agents.defaults.workspace = str(workspace)

    return config


@pytest.fixture
async def live_deep_gateway(
    live_config: "Config", workspace: Path, test_deepagents_config_path: Path
):
    """Start DeepGateway with DeepAgent for live testing.

    Yields dict with:
        - bus: MessageBus for sending/receiving messages
        - agent: DeepAgent instance
        - gateway: DeepGateway instance
        - workspace: workspace path
    """
    import aiosqlite
    from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

    from nanobot_deep.agent.deep_agent import DeepAgent
    from nanobot_deep.config.loader import load_deepagents_config
    from nanobot_deep.gateway import DeepGateway

    db_path = workspace.parent / "sessions.db"

    conn = await aiosqlite.connect(str(db_path))
    checkpointer = AsyncSqliteSaver(conn)
    await checkpointer.setup()

    gateway = DeepGateway(live_config, workspace, verbose=False)
    gateway.checkpointer = checkpointer

    deepagents_config = load_deepagents_config(test_deepagents_config_path)

    gateway.agent = DeepAgent(
        workspace=workspace,
        config=live_config,
        checkpointer=checkpointer,
        deepagents_config=deepagents_config,
    )

    gateway._running = True
    inbound_task = asyncio.create_task(gateway._consume_inbound_loop())

    yield {
        "bus": gateway.bus,
        "agent": gateway.agent,
        "gateway": gateway,
        "workspace": workspace,
        "checkpointer": checkpointer,
    }

    gateway._running = False
    inbound_task.cancel()
    try:
        await asyncio.wait_for(inbound_task, timeout=2.0)
    except (asyncio.CancelledError, asyncio.TimeoutError):
        pass

    if gateway.agent:
        await gateway.agent.close()


@pytest.fixture
def assert_response():
    """Helper for asserting response content."""

    def _assert(
        response,
        contains: str | list[str] | None = None,
        not_contains: str | list[str] | None = None,
    ):
        content = response.content.lower()

        if contains:
            items = [contains] if isinstance(contains, str) else contains
            for item in items:
                assert item.lower() in content, (
                    f"Expected '{item}' in response: {response.content[:200]}"
                )

        if not_contains:
            items = [not_contains] if isinstance(not_contains, str) else not_contains
            for item in items:
                assert item.lower() not in content, f"Did not expect '{item}' in response"

    return _assert


@pytest.fixture
async def send_and_wait():
    """Helper to send message and wait for response."""

    async def _send(
        bus: "MessageBus",
        content: str,
        channel: str = "test",
        sender_id: str = "user1",
        chat_id: str = "chat1",
        timeout: float = 60.0,
    ):
        from nanobot.bus.events import InboundMessage

        await bus.publish_inbound(
            InboundMessage(
                channel=channel,
                sender_id=sender_id,
                chat_id=chat_id,
                content=content,
            )
        )

        response = await asyncio.wait_for(bus.consume_outbound(), timeout=timeout)
        return response

    return _send
