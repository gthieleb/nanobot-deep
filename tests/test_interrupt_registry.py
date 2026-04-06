"""Tests for HITL interrupt registry."""

import asyncio

import pytest

from nanobot_deep.langgraph.interrupt_registry import (
    PendingInterrupt,
    InterruptRegistry,
    format_interrupt_message,
)


@pytest.fixture
def registry():
    """Create a fresh registry for each test."""
    return InterruptRegistry()


@pytest.fixture
def sample_interrupt():
    """Create a sample pending interrupt."""
    return PendingInterrupt(
        session_key="test:session:1",
        chat_id="123456",
        tool_call_id="call_abc123",
        tool_name="execute",
        tool_args={"command": "rm -rf /tmp/*"},
        description="Execute command requires approval",
        allowed_decisions=["approve", "reject"],
        timeout=60.0,
    )


class TestPendingInterrupt:
    """Tests for PendingInterrupt dataclass."""

    def test_create_interrupt(self):
        """Test creating a pending interrupt."""
        interrupt = PendingInterrupt(
            session_key="test:session:1",
            chat_id="123456",
            tool_call_id="call_abc",
            tool_name="execute",
            tool_args={"command": "ls"},
            description="Test",
            allowed_decisions=["approve", "reject"],
        )
        assert interrupt.session_key == "test:session:1"
        assert interrupt.tool_name == "execute"
        assert interrupt.tool_call_id == "call_abc"
        assert interrupt.allowed_decisions == ["approve", "reject"]

    def test_default_timeout(self):
        """Test default timeout value."""
        interrupt = PendingInterrupt(
            session_key="test:session:1",
            chat_id="123456",
            tool_call_id="call_abc",
            tool_name="execute",
            tool_args={},
            description="Test",
            allowed_decisions=["approve"],
        )
        assert interrupt.timeout == 60.0


class TestInterruptRegistry:
    """Tests for InterruptRegistry."""

    @pytest.mark.asyncio
    async def test_register_interrupt(self, registry, sample_interrupt):
        """Test registering an interrupt."""
        await registry.register(sample_interrupt)
        stored = await registry.get(sample_interrupt.tool_call_id)
        assert stored is not None
        assert stored.tool_name == "execute"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, registry):
        """Test getting a non-existent interrupt returns None."""
        result = await registry.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_session(self, registry, sample_interrupt):
        """Test getting all interrupts for a session."""
        await registry.register(sample_interrupt)

        other = PendingInterrupt(
            session_key="other:session",
            chat_id="789",
            tool_call_id="call_other",
            tool_name="edit_file",
            tool_args={},
            description="Other",
            allowed_decisions=["approve"],
        )
        await registry.register(other)

        session_interrupts = await registry.get_by_session("test:session:1")
        assert len(session_interrupts) == 1
        assert session_interrupts[0].tool_call_id == sample_interrupt.tool_call_id

    @pytest.mark.asyncio
    async def test_resolve_interrupt(self, registry, sample_interrupt):
        """Test resolving an interrupt with a decision."""
        await registry.register(sample_interrupt)
        await registry.resolve(sample_interrupt.tool_call_id, "approve")

        resolution = await registry.wait_for_resolution(sample_interrupt.tool_call_id, timeout=1.0)
        assert resolution is not None
        assert resolution["type"] == "approve"

    @pytest.mark.asyncio
    async def test_resolve_with_reject_message(self, registry, sample_interrupt):
        """Test resolving with reject and message."""
        await registry.register(sample_interrupt)
        await registry.resolve(
            sample_interrupt.tool_call_id,
            "reject",
            message="Too dangerous",
        )

        resolution = await registry.wait_for_resolution(sample_interrupt.tool_call_id, timeout=1.0)
        assert resolution["type"] == "reject"
        assert resolution["message"] == "Too dangerous"

    @pytest.mark.asyncio
    async def test_resolve_with_edit(self, registry, sample_interrupt):
        """Test resolving with edit decision."""
        await registry.register(sample_interrupt)

        edited_action = {
            "name": "execute",
            "args": {"command": "ls"},
        }
        await registry.resolve(sample_interrupt.tool_call_id, "edit", edited_action=edited_action)

        resolution = await registry.wait_for_resolution(sample_interrupt.tool_call_id, timeout=1.0)
        assert resolution["type"] == "edit"
        assert resolution["edited_action"] == edited_action

    @pytest.mark.asyncio
    async def test_wait_for_resolution_timeout(self, registry, sample_interrupt):
        """Test timeout when waiting for resolution."""
        await registry.register(sample_interrupt)

        resolution = await registry.wait_for_resolution(sample_interrupt.tool_call_id, timeout=0.1)
        assert resolution is not None
        assert resolution["type"] == "reject"
        assert "Timeout" in resolution["message"]

    @pytest.mark.asyncio
    async def test_unregister_interrupt(self, registry, sample_interrupt):
        """Test unregistering an interrupt."""
        await registry.register(sample_interrupt)
        await registry.unregister(sample_interrupt.tool_call_id)

        stored = await registry.get(sample_interrupt.tool_call_id)
        assert stored is None

    @pytest.mark.asyncio
    async def test_unregister_session(self, registry, sample_interrupt):
        """Test unregistering all interrupts for a session."""
        await registry.register(sample_interrupt)

        other = PendingInterrupt(
            session_key="test:session:1",
            chat_id="123456",
            tool_call_id="call_other",
            tool_name="edit_file",
            tool_args={},
            description="Other",
            allowed_decisions=["approve"],
        )
        await registry.register(other)

        await registry.unregister_session("test:session:1")

        remaining = await registry.get_by_session("test:session:1")
        assert len(remaining) == 0

    @pytest.mark.asyncio
    async def test_set_message_id(self, registry, sample_interrupt):
        """Test setting the Telegram message ID."""
        await registry.register(sample_interrupt)
        registry.set_message_id(sample_interrupt.tool_call_id, 42)

        stored = await registry.get(sample_interrupt.tool_call_id)
        assert stored.message_id == 42

    @pytest.mark.asyncio
    async def test_callback_on_register(self, registry, sample_interrupt):
        """Test callback is called when interrupt is registered."""
        callback_called = []

        async def callback(interrupt):
            callback_called.append(interrupt)

        registry.on_register(callback)
        await registry.register(sample_interrupt)

        assert len(callback_called) == 1
        assert callback_called[0].tool_call_id == sample_interrupt.tool_call_id

    @pytest.mark.asyncio
    async def test_callback_handles_exception(self, registry, sample_interrupt):
        """Test callback exception doesn't break registration."""

        async def bad_callback(interrupt):
            raise RuntimeError("Callback error")

        registry.on_register(bad_callback)
        await registry.register(sample_interrupt)

        stored = await registry.get(sample_interrupt.tool_call_id)
        assert stored is not None


class TestFormatInterruptMessage:
    """Tests for interrupt message formatting."""

    @pytest.mark.asyncio
    async def test_format_execute_command(self):
        """Test formatting an execute interrupt."""
        interrupt = PendingInterrupt(
            session_key="test:session",
            chat_id="123",
            tool_call_id="call_abc",
            tool_name="execute",
            tool_args={"command": "rm -rf /"},
            description="Execute requires approval",
            allowed_decisions=["approve", "reject"],
        )

        message = await format_interrupt_message(interrupt)
        assert "execute" in message.lower()
        assert "rm -rf /" in message
        assert "approval" in message.lower()

    @pytest.mark.asyncio
    async def test_format_edit_file(self):
        """Test formatting an edit_file interrupt."""
        interrupt = PendingInterrupt(
            session_key="test:session",
            chat_id="123",
            tool_call_id="call_abc",
            tool_name="edit_file",
            tool_args={
                "file_path": "/tmp/test.py",
                "old_string": "hello",
                "new_string": "world",
            },
            description="Edit file requires approval",
            allowed_decisions=["approve", "reject"],
        )

        message = await format_interrupt_message(interrupt)
        assert "edit_file" in message.lower()
        assert "/tmp/test.py" in message
        assert "hello" in message
        assert "world" in message

    @pytest.mark.asyncio
    async def test_format_write_file(self):
        """Test formatting a write_file interrupt."""
        interrupt = PendingInterrupt(
            session_key="test:session",
            chat_id="123",
            tool_call_id="call_abc",
            tool_name="write_file",
            tool_args={
                "file_path": "/tmp/new.py",
                "content": "print('hello')",
            },
            description="Write file requires approval",
            allowed_decisions=["approve", "reject"],
        )

        message = await format_interrupt_message(interrupt)
        assert "write_file" in message.lower()
        assert "/tmp/new.py" in message
        assert "hello" in message

    @pytest.mark.asyncio
    async def test_truncates_long_content(self):
        """Test that long content is truncated."""
        long_content = "x" * 300
        interrupt = PendingInterrupt(
            session_key="test:session",
            chat_id="123",
            tool_call_id="call_abc",
            tool_name="write_file",
            tool_args={
                "file_path": "/tmp/new.py",
                "content": long_content,
            },
            description="Write file",
            allowed_decisions=["approve", "reject"],
        )

        message = await format_interrupt_message(interrupt)
        assert "..." in message
        assert len(message) < 1000
