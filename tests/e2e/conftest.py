"""Pytest fixtures for E2E tests with real LLM calls.

Usage:
    # Option 1: Use existing nanobot config (recommended)
    export NANOBOT_CONFIG_PATH=~/.nanobot/config.json
    pytest tests/e2e/ -m live -v

    # Option 2: Override with env vars (takes precedence)
    NANOBOT_TEST_MODEL=gpt-5-mini pytest tests/e2e/ -m live -v

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
    from nanobot.agent.loop import AgentLoop
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


@pytest.fixture
def live_api_key(nanobot_test_config: "Config") -> str:
    """Get API key for live tests from config or env var."""
    key = os.environ.get("NANOBOT_TEST_API_KEY")
    if key:
        return key

    model = nanobot_test_config.agents.defaults.model
    provider_config = nanobot_test_config.get_provider(model)
    if provider_config and provider_config.api_key:
        return provider_config.api_key

    pytest.skip(
        f"No API key found for model {model}. Set NANOBOT_TEST_API_KEY or configure in nanobot.json"
    )


@pytest.fixture
def live_model(nanobot_test_config: "Config") -> str:
    """Get model for live tests from config or env var."""
    model = os.environ.get("NANOBOT_TEST_MODEL")
    if model:
        return model
    return nanobot_test_config.agents.defaults.model


@pytest.fixture
def live_provider(live_api_key: str, live_model: str):
    """Create real LLM provider for live tests."""
    from nanobot.providers.litellm_provider import LiteLLMProvider

    return LiteLLMProvider(
        api_key=live_api_key,
        default_model=live_model,
    )


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
    live_provider,
    live_model: str,
):
    """Start gateway with real LLM for live testing.

    Yields dict with:
        - bus: MessageBus for sending/receiving messages
        - agent: AgentLoop instance
        - provider: LLM provider
    """
    from nanobot.bus.queue import MessageBus
    from nanobot.agent.loop import AgentLoop

    bus = MessageBus()

    agent = AgentLoop(
        bus=bus,
        provider=live_provider,
        workspace=workspace,
        model=live_model,
        max_iterations=10,
        temperature=0.1,
    )

    agent_task = asyncio.create_task(agent.run())

    yield {
        "bus": bus,
        "agent": agent,
        "provider": live_provider,
        "workspace": workspace,
    }

    agent.stop()
    agent_task.cancel()
    try:
        await asyncio.wait_for(agent_task, timeout=2.0)
    except (asyncio.CancelledError, asyncio.TimeoutError):
        pass


@pytest.fixture
async def live_gateway_no_cancel(
    workspace: Path,
    live_provider,
    live_model: str,
):
    """Start gateway without auto-cancellation (for tests that need to stop manually)."""
    from nanobot.bus.queue import MessageBus
    from nanobot.agent.loop import AgentLoop

    bus = MessageBus()

    agent = AgentLoop(
        bus=bus,
        provider=live_provider,
        workspace=workspace,
        model=live_model,
        max_iterations=10,
        temperature=0.1,
    )

    agent_task = asyncio.create_task(agent.run())

    yield {
        "bus": bus,
        "agent": agent,
        "provider": live_provider,
        "workspace": workspace,
        "task": agent_task,
    }

    agent.stop()
    try:
        await asyncio.wait_for(agent_task, timeout=5.0)
    except (asyncio.CancelledError, asyncio.TimeoutError):
        pass


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
def deep_checkpointer(workspace: Path):
    """Create a session checkpointer for DeepAgent tests."""
    from nanobot_deep.langgraph.checkpointer import SessionCheckpointer

    db_path = workspace.parent / "test_sessions.db"
    checkpointer = SessionCheckpointer(db_path)
    checkpointer.setup()
    return checkpointer


@pytest.fixture
def deep_agent_config(live_api_key: str, live_model: str):
    """Create DeepAgentsConfig for live tests."""
    from nanobot_deep.config.schema import DeepAgentsConfig, DeepAgentsModelConfig

    return DeepAgentsConfig(
        model=DeepAgentsModelConfig(
            name=live_model,
            api_key=live_api_key,
            max_tokens=4096,
            temperature=0.1,
        ),
        recursion_limit=50,
        debug=False,
    )


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
    from pathlib import Path

    api_id = telegram_api_credentials["api_id"]
    api_hash = telegram_api_credentials["api_hash"]
    phone = telegram_api_credentials["phone"]

    session_path = Path(__file__).parent / "test_session_user"
    print(f"Session path: {session_path.absolute()}")

    client = TelegramClient(str(session_path), api_id, api_hash)

    try:
        await client.connect()

        if not await client.is_user_authorized():
            print("User not authorized. Attempting authentication...")
            await client.send_code_request(phone)
            code = os.environ.get("TELEGRAM_AUTH_CODE", "")
            if not code:
                code = input(f"Enter code for {phone}: ")
            await client.sign_in(phone, code)
            print(f"Session created: {session_path.absolute()}")
        else:
            print(f"Using existing session: {session_path.absolute()}")

        yield client

    finally:
        await client.disconnect()


@pytest.fixture
async def telegram_bot_entity(telegram_user_client, telegram_api_credentials, request):
    """Get bot entity to test against - DM or group mode.

    Resolves to bot username based on TELEGRAM_LOCAL_MODE:
    - If mode is "group": Returns group entity using get_input_entity(int(group_id))
    - If mode is "dm" or not set: Returns bot entity using bot username

    Resolves to bot username and yields to bot entity.
    """
    import os

    bot_username = telegram_api_credentials["bot_username"]
    mode = os.environ.get("TELEGRAM_LOCAL_MODE", "dm").lower()

    if mode == "group":
        # Group mode (nanobot-deep-ci group)
        group_id = os.environ.get("TELEGRAM_CI_GROUP_ID")
        if not group_id:
            pytest.skip("TELEGRAM_CI_GROUP_ID not set for group mode")

        # For groups, use get_input_entity() with channel ID (not get_entity() with user ID)
        bot = await telegram_user_client.get_input_entity(int(group_id))
        yield bot
    else:
        # DM mode (local development)
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
