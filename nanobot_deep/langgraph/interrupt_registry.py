"""Interrupt registry for HITL (Human-in-the-Loop) requests.

This module provides a registry for storing pending interrupts that require
user approval via Telegram buttons.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from loguru import logger

if TYPE_CHECKING:
    pass


@dataclass
class PendingInterrupt:
    """Represents a pending human-in-the-loop interrupt."""

    session_key: str
    chat_id: str
    tool_call_id: str
    tool_name: str
    tool_args: dict[str, Any]
    description: str
    allowed_decisions: list[str]
    message_id: int | None = None
    message_thread_id: str | None = None
    timeout: float = 60.0
    created_at: float = field(default_factory=time.time)


class InterruptRegistry:
    """Registry for pending HITL interrupts.

    Stores interrupts that require user approval and provides methods
    to register, retrieve, and resolve interrupts.

    Usage:
        1. Register interrupt: await REGISTRY.register(interrupt)
        2. Channel sends message with buttons
        3. User clicks button: await REGISTRY.resolve(tool_call_id, "approve")
        4. Agent resumes: decision = await REGISTRY.wait_for_resolution(tool_call_id)
    """

    def __init__(self) -> None:
        self._interrupts: dict[str, PendingInterrupt] = {}
        self._lock = asyncio.Lock()
        self._resolution_events: dict[str, asyncio.Event] = {}
        self._resolutions: dict[str, dict[str, Any]] = {}
        self._on_register_callbacks: list[callable] = []

    def on_register(self, callback: callable) -> None:
        """Register a callback to be called when interrupts are registered.

        The callback receives (interrupt: PendingInterrupt) as argument.

        Args:
            callback: Async function to call
        """
        self._on_register_callbacks.append(callback)

    async def register(self, interrupt: PendingInterrupt) -> None:
        """Register a pending interrupt.

        Args:
            interrupt: The interrupt to register
        """
        async with self._lock:
            self._interrupts[interrupt.tool_call_id] = interrupt
            self._resolution_events[interrupt.tool_call_id] = asyncio.Event()

        for callback in self._on_register_callbacks:
            try:
                await callback(interrupt)
            except Exception as e:
                logger.warning(f"Interrupt callback failed: {e}")

    async def get(self, tool_call_id: str) -> PendingInterrupt | None:
        """Get a pending interrupt by tool call ID.

        Args:
            tool_call_id: The tool call ID

        Returns:
            The pending interrupt or None if not found
        """
        async with self._lock:
            return self._interrupts.get(tool_call_id)

    async def get_by_session(self, session_key: str) -> list[PendingInterrupt]:
        """Get all pending interrupts for a session.

        Args:
            session_key: The session key

        Returns:
            List of pending interrupts for the session
        """
        async with self._lock:
            return [
                interrupt
                for interrupt in self._interrupts.values()
                if interrupt.session_key == session_key
            ]

    async def resolve(
        self,
        tool_call_id: str,
        decision: str,
        edited_action: dict[str, Any] | None = None,
        message: str | None = None,
    ) -> None:
        """Resolve a pending interrupt with a user decision.

        Args:
            tool_call_id: The tool call ID
            decision: The user's decision (approve, reject, edit)
            edited_action: Optional edited action for 'edit' decision
            message: Optional message for 'reject' decision
        """
        async with self._lock:
            if tool_call_id not in self._resolution_events:
                return

            resolution = {"type": decision}
            if decision == "edit" and edited_action:
                resolution["edited_action"] = edited_action
            elif decision == "reject" and message:
                resolution["message"] = message

            self._resolutions[tool_call_id] = resolution
            self._resolution_events[tool_call_id].set()

    async def wait_for_resolution(
        self, tool_call_id: str, timeout: float = 60.0
    ) -> dict[str, Any] | None:
        """Wait for a user decision on an interrupt.

        Args:
            tool_call_id: The tool call ID
            timeout: Timeout in seconds

        Returns:
            The user's decision or None if timeout
        """
        event = self._resolution_events.get(tool_call_id)
        if event is None:
            return None

        try:
            await asyncio.wait_for(event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            return {"type": "reject", "message": "Timeout: User did not respond"}

        return self._resolutions.get(tool_call_id)

    async def unregister(self, tool_call_id: str) -> None:
        """Unregister a pending interrupt.

        Args:
            tool_call_id: The tool call ID
        """
        async with self._lock:
            self._interrupts.pop(tool_call_id, None)
            self._resolution_events.pop(tool_call_id, None)
            self._resolutions.pop(tool_call_id, None)

    async def unregister_session(self, session_key: str) -> None:
        """Unregister all interrupts for a session.

        Args:
            session_key: The session key
        """
        async with self._lock:
            to_remove = [
                tc_id
                for tc_id, interrupt in self._interrupts.items()
                if interrupt.session_key == session_key
            ]
            for tc_id in to_remove:
                self._interrupts.pop(tc_id, None)
                self._resolution_events.pop(tc_id, None)
                self._resolutions.pop(tc_id, None)

    def set_message_id(self, tool_call_id: str, message_id: int) -> None:
        """Set the Telegram message ID for an interrupt.

        Args:
            tool_call_id: The tool call ID
            message_id: The Telegram message ID
        """
        if tool_call_id in self._interrupts:
            self._interrupts[tool_call_id].message_id = message_id


REGISTRY = InterruptRegistry()


async def format_interrupt_message(interrupt: PendingInterrupt) -> str:
    """Format an interrupt as a Telegram message.

    Args:
        interrupt: The pending interrupt

    Returns:
        Formatted message text
    """
    tool_name = interrupt.tool_name
    tool_args = interrupt.tool_args

    lines = ["⚠️ <b>Action requires approval</b>\n"]
    lines.append(f"<b>Tool:</b> {tool_name}\n\n")

    if tool_name == "execute" and "command" in tool_args:
        command = tool_args["command"]
        escaped_command = command.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        lines.append(f"<b>Command:</b>\n<code>{escaped_command}</code>\n")
    elif tool_name == "edit_file" and "file_path" in tool_args:
        file_path = tool_args["file_path"]
        lines.append(f"<b>File:</b> {file_path}\n")
        if "old_string" in tool_args:
            old = (
                tool_args["old_string"][:100] + "..."
                if len(tool_args["old_string"]) > 100
                else tool_args["old_string"]
            )
            lines.append(f"<b>Old:</b>\n<code>{old}</code>\n")
        if "new_string" in tool_args:
            new = (
                tool_args["new_string"][:100] + "..."
                if len(tool_args["new_string"]) > 100
                else tool_args["new_string"]
            )
            lines.append(f"<b>New:</b>\n<code>{new}</code>\n")
    elif tool_name == "write_file" and "file_path" in tool_args:
        file_path = tool_args["file_path"]
        lines.append(f"<b>File:</b> {file_path}\n")
        if "content" in tool_args:
            content = (
                tool_args["content"][:200] + "..."
                if len(tool_args["content"]) > 200
                else tool_args["content"]
            )
            lines.append(f"<b>Content:</b>\n<code>{content}</code>\n")
    elif tool_args:
        args_str = str(tool_args)[:500]
        lines.append(f"<b>Args:</b>\n<code>{args_str}</code>\n")

    if interrupt.timeout:
        lines.append(f"\n<i>Auto-reject after {int(interrupt.timeout)}s</i>")

    return "".join(lines)
