"""Pytest fixtures for E2E tests with real LLM calls.

Usage:
    # Option 1: Use existing nanobot config for channels/workspace
    export NANOBOT_CONFIG_PATH=~/.nanobot/config.json
    pytest tests/e2e/ -m live -v

    # Option 2: Override DeepAgents model
    DEEPAGENTS_TEST_MODEL=openai:gpt-4o-mini pytest tests/e2e/ -m live -v

    # Telegram E2E tests (require real Telegram user account):
    # 1. Get API credentials: https://my.telegram.org/apps
    # 2. Set environment variables:
    #    export TELEGRAM_API_ID=12345
    #    export TELEGRAM_API_HASH=abc123...
    #    export TEST_USER_PHONE=+49...
    #    export TELEGRAM_BOT_USERNAME=@your_bot
    # 3. Run tests: pytest tests/e2e/ -m live -v
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


@pytest.fixture
def nanobot_test_config() -> "Config":
    """Load nanobot config for tests.

    Uses NANOBOT_CONFIG_PATH env var if set, otherwise default ~/.nanobot/config.json
    """
    from nanobot.config.loader import load_config

    config_path = os.environ.get("NANOBOT_CONFIG_PATH")
    if config_path:
        config_path = Path(config_path)
    else:
        config_path = Path.home() / ".nanobot" / "config.json"

    if not config_path.exists():
        pytest.skip(f"Config not found at {config_path}. Set NANOBOT_CONFIG_PATH or create config.")

    return load_config(config_path)


def _apply_test_api_key_override(model_spec: str | None, test_api_key: str) -> str | None:
    """Apply NANOBOT_TEST_API_KEY to the provider env var for model_spec.

    Returns an error message if mapping cannot be determined.
    """
    from deepagents_cli.model_config import ModelSpec, get_credential_env_var

    parsed = ModelSpec.try_parse(model_spec) if model_spec else None
    if parsed is None:
        return (
            "NANOBOT_TEST_API_KEY requires DEEPAGENTS_TEST_MODEL in provider:model format "
            "(for example: openai:gpt-4o-mini)"
        )

    env_var = get_credential_env_var(parsed.provider)
    if not env_var:
        return (
            f"Provider '{parsed.provider}' has no known credential env mapping. "
            "Set the provider env var directly and rerun."
        )

    os.environ[env_var] = test_api_key
    return None


@pytest.fixture
def live_model_result():
    """Resolve a DeepAgents model for live tests using DeepAgents config."""
    from deepagents_cli.config import ModelConfigError, create_model

    model_spec = os.environ.get("DEEPAGENTS_TEST_MODEL") or os.environ.get("NANOBOT_TEST_MODEL")
    test_api_key = os.environ.get("NANOBOT_TEST_API_KEY")
    if test_api_key:
        error = _apply_test_api_key_override(model_spec, test_api_key)
        if error:
            pytest.skip(error)

    try:
        return create_model(model_spec)
    except ModelConfigError as e:
        pytest.skip(
            "DeepAgents model config is not ready for live tests: "
            f"{e}. Configure ~/.deepagents/config.toml or set provider credentials env vars."
        )


@pytest.fixture
def live_model(live_model_result) -> str:
    """Resolved model string for backwards-compatible test usage."""
    return f"{live_model_result.provider}:{live_model_result.model_name}"


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    """Create test workspace with basic structure."""
    ws = tmp_path / "workspace"
    ws.mkdir()
    (ws / "skills").mkdir()
    return ws


@pytest.fixture
async def live_gateway(
    workspace: Path,
    mock_nanobot_config,
    deep_checkpointer,
    deep_agent_config,
    live_model_result,
):
    """Start gateway with DeepAgent for live testing.

    Yields dict with:
        - bus: MessageBus for sending/receiving messages
        - agent: DeepAgent instance
        - provider: DeepAgents provider name
    """
    from nanobot.bus.queue import MessageBus
    from nanobot_deep.agent.deep_agent import DeepAgent

    bus = MessageBus()

    agent = DeepAgent(
        workspace=workspace,
        config=mock_nanobot_config,
        checkpointer=deep_checkpointer,
        deepagents_config=deep_agent_config,
    )

    async def consume_and_process():
        while True:
            msg = None
            try:
                msg = await asyncio.wait_for(bus.consume_inbound(), timeout=1.0)
                response = await agent.process(msg)
                await bus.publish_outbound(response)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                from nanobot.bus.events import OutboundMessage

                if msg:
                    await bus.publish_outbound(
                        OutboundMessage(
                            channel=msg.channel,
                            chat_id=msg.chat_id,
                            content=f"Error: {e}",
                        )
                    )

    agent_task = asyncio.create_task(consume_and_process())

    yield {
        "bus": bus,
        "agent": agent,
        "provider": live_model_result.provider,
        "workspace": workspace,
    }

    agent_task.cancel()
    try:
        await asyncio.wait_for(agent_task, timeout=2.0)
    except (asyncio.CancelledError, asyncio.TimeoutError):
        pass

    await agent.close()


@pytest.fixture
async def live_gateway_no_cancel(
    workspace: Path,
    mock_nanobot_config,
    deep_checkpointer,
    deep_agent_config,
    live_model_result,
):
    """Start DeepAgent gateway without auto-cancellation."""
    from nanobot.bus.queue import MessageBus
    from nanobot_deep.agent.deep_agent import DeepAgent

    bus = MessageBus()

    agent = DeepAgent(
        workspace=workspace,
        config=mock_nanobot_config,
        checkpointer=deep_checkpointer,
        deepagents_config=deep_agent_config,
    )

    async def consume_and_process():
        while True:
            msg = None
            try:
                msg = await asyncio.wait_for(bus.consume_inbound(), timeout=1.0)
                response = await agent.process(msg)
                await bus.publish_outbound(response)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                from nanobot.bus.events import OutboundMessage

                if msg:
                    await bus.publish_outbound(
                        OutboundMessage(
                            channel=msg.channel,
                            chat_id=msg.chat_id,
                            content=f"Error: {e}",
                        )
                    )

    agent_task = asyncio.create_task(consume_and_process())

    yield {
        "bus": bus,
        "agent": agent,
        "provider": live_model_result.provider,
        "workspace": workspace,
        "task": agent_task,
    }

    try:
        await asyncio.wait_for(agent_task, timeout=5.0)
    except (asyncio.CancelledError, asyncio.TimeoutError):
        pass

    await agent.close()


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
        from nanobot.bus.events import InboundMessage, OutboundMessage

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


@pytest.fixture
async def deep_checkpointer(workspace: Path):
    """Create an AsyncSqliteSaver checkpointer for DeepAgent tests."""
    import aiosqlite
    from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

    db_path = workspace.parent / "test_sessions.db"
    conn = await aiosqlite.connect(str(db_path))
    checkpointer = AsyncSqliteSaver(conn)
    await checkpointer.setup()
    try:
        yield checkpointer
    finally:
        await conn.close()


@pytest.fixture
def deep_agent_config():
    """Create DeepAgents runtime config for live tests."""
    from nanobot_deep.config.schema import DeepAgentsConfig

    return DeepAgentsConfig(recursion_limit=50, debug=False)


@pytest.fixture
def mock_nanobot_config(workspace: Path, nanobot_test_config: "Config"):
    """Create a nanobot config for DeepAgent tests with test workspace."""
    config = nanobot_test_config.model_copy(deep=True)
    config.agents.defaults.workspace = str(workspace)
    return config


@pytest.fixture
async def live_deep_agent(
    workspace: Path,
    mock_nanobot_config,
    deep_checkpointer,
    deep_agent_config,
    live_model_result,
):
    """Create a DeepAgent instance for live testing."""
    from nanobot_deep.agent.deep_agent import DeepAgent

    agent = DeepAgent(
        workspace=workspace,
        config=mock_nanobot_config,
        checkpointer=deep_checkpointer,
        deepagents_config=deep_agent_config,
    )

    yield agent

    await agent.close()


@pytest.fixture
async def live_deep_gateway(
    workspace: Path,
    mock_nanobot_config,
    deep_checkpointer,
    deep_agent_config,
    live_model_result,
):
    """Start DeepGateway with DeepAgent for live testing.

    Yields dict with:
        - bus: MessageBus for sending/receiving messages
        - agent: DeepAgent instance
        - gateway: DeepGateway instance
        - consumer_task: Background task consuming from bus
    """
    from nanobot.bus.queue import MessageBus
    from nanobot_deep.agent.deep_agent import DeepAgent
    from nanobot_deep.gateway import DeepGateway

    bus = MessageBus()

    agent = DeepAgent(
        workspace=workspace,
        config=mock_nanobot_config,
        checkpointer=deep_checkpointer,
        deepagents_config=deep_agent_config,
    )

    async def consume_and_process():
        """Simple consumer that processes messages."""
        while True:
            msg = None
            try:
                msg = await asyncio.wait_for(bus.consume_inbound(), timeout=1.0)
                response = await agent.process(msg)
                await bus.publish_outbound(response)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                from nanobot.bus.events import OutboundMessage

                if msg:
                    await bus.publish_outbound(
                        OutboundMessage(
                            channel=msg.channel,
                            chat_id=msg.chat_id,
                            content=f"Error: {e}",
                        )
                    )

    consumer_task = asyncio.create_task(consume_and_process())

    yield {
        "bus": bus,
        "agent": agent,
        "consumer_task": consumer_task,
    }

    consumer_task.cancel()
    try:
        await asyncio.wait_for(consumer_task, timeout=2.0)
    except (asyncio.CancelledError, asyncio.TimeoutError):
        pass

    await agent.close()


@pytest.fixture
async def deep_send_and_wait():
    """Helper to send message to DeepAgent and wait for response."""

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


@pytest.fixture
def telegram_api_credentials():
    """Load Telegram API credentials for E2E testing.

    Requires these environment variables:
    - TELEGRAM_API_ID: From https://my.telegram.org/apps
    - TELEGRAM_API_HASH: From https://my.telegram.org/apps
    - TEST_USER_PHONE: Phone number for test user account
    - TELEGRAM_BOT_USERNAME: Bot username to test (e.g., @my_bot)

    Returns dict with credentials or skips test if not set.
    """
    api_id = os.environ.get("TELEGRAM_API_ID")
    api_hash = os.environ.get("TELEGRAM_API_HASH")
    phone = os.environ.get("TEST_USER_PHONE")
    bot_username = os.environ.get("TELEGRAM_BOT_USERNAME")

    missing = [
        var
        for var, val in [
            ("TELEGRAM_API_ID", api_id),
            ("TELEGRAM_API_HASH", api_hash),
            ("TEST_USER_PHONE", phone),
            ("TELEGRAM_BOT_USERNAME", bot_username),
        ]
        if not val
    ]

    if missing:
        pytest.skip(
            f"Telegram E2E tests require: {', '.join(missing)}\n"
            "Get credentials from https://my.telegram.org/apps\n"
            "Example:\n"
            "  export TELEGRAM_API_ID=12345\n"
            "  export TELEGRAM_API_HASH=abc123...\n"
            "  export TEST_USER_PHONE=+49...\n"
            "  export TELEGRAM_BOT_USERNAME=@your_bot"
        )

    return {
        "api_id": int(api_id),
        "api_hash": api_hash,
        "phone": phone,
        "bot_username": bot_username,
    }


@pytest.fixture
async def telegram_user_client(telegram_api_credentials):
    """Create and connect a Telethon client for testing.

    Yields a connected TelegramClient instance.
    Client is disconnected after test.
    """
    from telethon import TelegramClient

    api_id = telegram_api_credentials["api_id"]
    api_hash = telegram_api_credentials["api_hash"]
    phone = telegram_api_credentials["phone"]

    client = TelegramClient("test_session_user", api_id, api_hash)

    try:
        await client.connect()

        if not await client.is_user_authorized():
            await client.send_code_request(phone)
            await client.sign_in(phone, input(f"Enter code for {phone}: "))

        yield client

    finally:
        await client.disconnect()


@pytest.fixture
async def telegram_bot_entity(telegram_user_client, telegram_api_credentials):
    """Get the bot entity to test against.

    Resolves the bot username and yields the bot entity.
    """
    bot_username = telegram_api_credentials["bot_username"]

    bot = await telegram_user_client.get_entity(bot_username)
    yield bot


@pytest.fixture
async def telegram_send_and_wait(telegram_user_client, telegram_bot_entity):
    """Helper to send message to bot and wait for response.

    Sends a message to the bot via Telegram and waits for a response.

    Args:
        content: Message content to send

    Returns:
        The bot's response message

    Usage:
        response = await telegram_send_and_wait("Hello")
        assert response.message.lower() == "pong"
    """
    from telethon.tl.types import Message

    async def _send(content: str, timeout: float = 60.0):
        sent_message = await telegram_user_client.send_message(telegram_bot_entity, content)

        start_time = asyncio.get_event_loop().time()
        while True:
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > timeout:
                raise TimeoutError(f"Bot did not respond within {timeout} seconds")

            messages = await telegram_user_client.get_messages(
                telegram_bot_entity, limit=5, min_id=sent_message.id
            )

            for msg in messages:
                if msg and isinstance(msg, Message) and msg.id > sent_message.id:
                    return msg

            await asyncio.sleep(0.5)

    return _send
