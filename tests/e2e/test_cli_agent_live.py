"""nanobot-deep CLI live tests."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.live


def _resolve_config_path() -> Path:
    config_path = os.environ.get("NANOBOT_TEST_CONFIG")
    if config_path:
        return Path(config_path).expanduser().resolve()
    return Path.home() / ".nanobot" / "config.json"


class TestCliAgent:
    def test_agent_message_responds(self, tmp_path, live_model_result):
        config_path = _resolve_config_path()
        if not config_path.exists():
            pytest.skip(
                f"Config not found at {config_path}. Set NANOBOT_TEST_CONFIG."
            )

        workspace = tmp_path / "workspace"
        workspace.mkdir()

        command = [
            sys.executable,
            "-m",
            "nanobot_deep.cli",
            "agent",
            "-m",
            "Reply with exactly the word 'pong' and nothing else",
            "--config",
            str(config_path),
            "--workspace",
            str(workspace),
            "--timeout",
            "60",
            "--no-markdown",
            "--no-logs",
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            env=os.environ.copy(),
            timeout=120,
        )

        assert result.returncode == 0, result.stderr or result.stdout
        assert "pong" in result.stdout.lower()
