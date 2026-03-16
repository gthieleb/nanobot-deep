"""Pytest fixtures for E2E tests with real LLM calls.

Usage:
    # Option 1: Use existing nanobot config for channels/workspace
    export NANOBOT_CONFIG_PATH=~/.nanobot/config.json
    # Optional: Override DeepAgents config.toml path
    export DEEPAGENTS_CONFIG_PATH=~/.deepagents/config.toml
    # Optional: Use minimal deepagents test config
    export NANOBOT_TEST_DEEPAGENTS_CONFIG=tests/e2e/deepagents.test.json
    pytest tests/e2e/ -m live -v

    # Option 2: Override DeepAgents model
    DEEPAGENTS_TEST_MODEL=openai:gpt-4o-mini pytest tests/e2e/ -m live -v

    # Option 3: Explicit nanobot config path
    NANOBOT_TEST_CONFIG=~/.nanobot/config.json pytest tests/e2e/ -m live -v

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
from typing import cast
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

    Uses NANOBOT_TEST_CONFIG or NANOBOT_CONFIG_PATH if set, otherwise default
    ~/.nanobot/config.json.
    """
    from nanobot.config.loader import load_config

    config_path = os.environ.get("NANOBOT_TEST_CONFIG") or os.environ.get("NANOBOT_CONFIG_PATH")
    if config_path:
        config_path = Path(config_path)
    else:
        config_path = Path.home() / ".nanobot" / "config.json"

    if not config_path.exists():
        pytest.skip(
            f"Config not found at {config_path}. Set NANOBOT_TEST_CONFIG or "
            "NANOBOT_CONFIG_PATH, or create a default config."
        )

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
    from nanobot_deep.config.deepagents_cli import apply_deepagents_config_path

    model_spec = os.environ.get("DEEPAGENTS_TEST_MODEL") or os.environ.get("NANOBOT_TEST_MODEL")
    test_api_key = os.environ.get("NANOBOT_TEST_API_KEY")
    if test_api_key:
        error = _apply_test_api_key_override(model_spec, test_api_key)
        if error:
            pytest.skip(error)

    apply_deepagents_config_path()
    try:
        return create_model(model_spec)
    except ModelConfigError as e:
        pytest.skip(
            "DeepAgents model config is not ready for live tests: "
            f"{e}. Configure ~/.deepagents/config.toml (or set DEEPAGENTS_CONFIG_PATH) "
            "or set provider credentials env vars."
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
    from nanobot.agent.loop import AgentLoop
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
    from nanobot.agent.loop import AgentLoop
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
    from nanobot_deep.config.loader import load_deepagents_config
    from nanobot_deep.config.schema import DeepAgentsConfig

    config_path = os.environ.get("NANOBOT_TEST_DEEPAGENTS_CONFIG")
    if config_path:
        return load_deepagents_config(Path(config_path).expanduser().resolve())

    default_path = Path(__file__).parent / "deepagents.test.json"
    if default_path.exists():
        return load_deepagents_config(default_path)

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


@pytest.fixture(scope="session")
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
        "api_id": int(cast(str, api_id)),
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
    from pathlib import Path

    from telethon import TelegramClient

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
        disconnect_result = client.disconnect()
        if asyncio.iscoroutine(disconnect_result):
            await disconnect_result


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
        bot = await telegram_user_client.get_input_entity(int(cast(str, group_id)))
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
    import os

    bot_username = os.environ.get("TELEGRAM_BOT_USERNAME", "").lstrip("@")
    mode = os.environ.get("TELEGRAM_LOCAL_MODE", "dm").lower()
    bot_id = None

    if bot_username:
        try:
            bot_entity = await telegram_user_client.get_entity(bot_username)
            bot_id = getattr(bot_entity, "id", None)
        except Exception:
            bot_id = None

    def normalize_content(content: str) -> str:
        if mode != "group" or not bot_username:
            return content

        if content.startswith("/"):
            first, *rest = content.split(" ", 1)
            if "@" not in first:
                first = f"{first}@{bot_username}"
            if rest:
                return f"{first} {rest[0]}"
            return first

        mention = f"@{bot_username}"
        if mention.lower() in content.lower():
            return content
        return f"{mention} {content}"

    async def _send(content: str, timeout: float = 20.0):
        if not telegram_user_client.is_connected():
            await telegram_user_client.connect()

        normalized = normalize_content(content)
        send_kwargs = {}
        if mode == "group" and not normalized.startswith("/") and bot_id is not None:
            recent = await telegram_user_client.get_messages(telegram_bot_entity, limit=10)
            for recent_msg in recent:
                if getattr(recent_msg, "sender_id", None) == bot_id:
                    send_kwargs["reply_to"] = recent_msg.id
                    break

        sent_message = await telegram_user_client.send_message(
            telegram_bot_entity,
            normalized,
            **send_kwargs,
        )

        start_time = asyncio.get_event_loop().time()
        while True:
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > timeout:
                raise TimeoutError(f"Bot did not respond within {timeout} seconds")

            messages = await telegram_user_client.get_messages(
                telegram_bot_entity, limit=5, min_id=sent_message.id
            )

            for msg in reversed(messages):
                if not msg or not isinstance(msg, Message) or msg.id <= sent_message.id:
                    continue

                msg_sender_id = getattr(msg, "sender_id", None)
                if bot_id is not None and msg_sender_id != bot_id:
                    continue

                reply_to = getattr(msg, "reply_to", None)
                reply_to_msg_id = getattr(reply_to, "reply_to_msg_id", None)
                if reply_to_msg_id is not None and reply_to_msg_id != sent_message.id:
                    continue

                return msg

            await asyncio.sleep(0.5)

    return _send
