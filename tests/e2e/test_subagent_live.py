"""Subagent spawning tests with real LLM calls.

Tests spawn tool and subagent execution.

Run with:
    NANOBOT_TEST_API_KEY=sk-... pytest tests/e2e/test_subagent_live.py -m live -v
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from nanobot.bus.events import InboundMessage

pytestmark = [pytest.mark.live, pytest.mark.slow]


class TestSubagentBasic:
    """Basic subagent functionality tests."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_spawn_creates_file(self, live_gateway, workspace, send_and_wait):
        """Test that spawn tool creates file through subagent."""
        bus = live_gateway["bus"]

        response = await send_and_wait(
            bus,
            "Use the task tool to create a file called spawned_file.txt with content 'created by subagent'. Reply 'done' when finished.",
            chat_id="spawn_test",
            timeout=30,
        )
        assert response.content

        # Verify file was created
        spawned_file = workspace / "spawned_file.txt"
        assert spawned_file.exists(), f"File not found in {workspace}: {list(workspace.iterdir())}"
        content = spawned_file.read_text()
        assert "subagent" in content.lower() or "created" in content.lower()

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_spawn_research_task(self, live_gateway, send_and_wait):
        """Test spawn for research-like task."""
        bus = live_gateway["bus"]

        response = await send_and_wait(
            bus,
            "Use the task tool to write the numbers 1 through 5 to a file called numbers.txt, one per line. Reply 'ok' when done.",
            chat_id="spawn_research",
            timeout=30,
        )

        # Should get some response
        assert response.content


class TestSubagentIsolation:
    """Test subagent isolation from main agent context."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_subagent_no_main_context(self, live_gateway, workspace, send_and_wait):
        """Test that subagent doesn't see main conversation context."""
        bus = live_gateway["bus"]

        # Set context in main agent
        await send_and_wait(bus, "Remember this secret: MAIN_SECRET_123", chat_id="isolation_test")

        # Spawn subagent - it shouldn't know the secret
        await send_and_wait(
            bus,
            "Use the task tool to create a file called check_secret.txt. Write 'secret found: [any secret you know]'. Reply 'ok' when done.",
            chat_id="isolation_test",
            timeout=30,
        )

        # Check file - should NOT contain MAIN_SECRET_123
        check_file = workspace / "check_secret.txt"
        if check_file.exists():
            content = check_file.read_text()
            # Subagent shouldn't know the main secret
            assert "MAIN_SECRET_123" not in content


class TestSubagentNotification:
    """Test subagent completion notifications."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_subagent_notifies_completion(self, live_gateway, workspace, send_and_wait):
        """Test that subagent sends notification when done."""
        bus = live_gateway["bus"]

        response = await send_and_wait(
            bus,
            "Use the task tool to create notify_test.txt with content 'done'. Reply with 'completed' when finished.",
            chat_id="notify_test",
            timeout=30,
        )

        content_lower = response.content.lower()
        assert any(
            word in content_lower for word in ["complet", "finish", "done", "created", "spawn"]
        )


class TestSubagentMultiple:
    """Test multiple subagent operations."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_sequential_spawns(self, live_gateway, workspace, send_and_wait):
        """Test multiple sequential spawn operations."""
        bus = live_gateway["bus"]

        # First spawn
        await send_and_wait(
            bus,
            "Use the task tool to create file1.txt with content 'first'",
            chat_id="multi_spawn",
            timeout=30,
        )

        # Second spawn
        await send_and_wait(
            bus,
            "Use the task tool to create file2.txt with content 'second'",
            chat_id="multi_spawn",
            timeout=30,
        )

        # Verify both files
        assert (workspace / "file1.txt").exists()
        assert (workspace / "file2.txt").exists()


class TestSubagentErrors:
    """Test subagent error handling."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_subagent_handles_error(self, live_gateway, send_and_wait):
        """Test that subagent errors are handled gracefully."""
        bus = live_gateway["bus"]

        # Ask subagent to do something that might fail
        response = await send_and_wait(
            bus,
            "Use the task tool to try reading a file that doesn't exist called nonexistent_12345.txt. Report what happens.",
            chat_id="error_test",
            timeout=30,
        )

        # Should get some response, not crash
        assert response.content
        assert len(response.content) > 0
