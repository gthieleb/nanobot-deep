"""Tests for CLI config loading behavior.

Validates that _load_config() correctly resolves the config file path.
"""

from __future__ import annotations

import json

import pytest

import nanobot.config.loader as config_loader

from nanobot_deep.cli import _load_config


@pytest.mark.xfail(
    reason="NANOBOT_CONFIG_PATH env var is not read by _load_config(). "
    "Config is passed via --config CLI flag instead. See PR #138.",
    strict=True,
)
def test_load_config_uses_nanobot_config_path_env(monkeypatch, tmp_path):
    """_load_config() should respect NANOBOT_CONFIG_PATH when no --config is given.

    This test documents that the env var is NOT read — it is expected to fail (xfail).
    The intended fix is to always pass --config via Docker command instead of relying
    on the environment variable.
    """
    env_config_path = tmp_path / "config-nanobot-deep.json"
    default_config_path = tmp_path / "config.json"

    env_config_path.write_text(
        json.dumps(
            {
                "agents": {"defaults": {"workspace": str(tmp_path / "env-ws")}},
                "channels": {"telegram": {"enabled": True, "token": "ENV_TOKEN_STOLZIBOT"}},
            }
        ),
        encoding="utf-8",
    )

    default_config_path.write_text(
        json.dumps(
            {
                "agents": {"defaults": {"workspace": str(tmp_path / "default-ws")}},
                "channels": {"telegram": {"enabled": True, "token": "DEFAULT_TOKEN_EAST79BOT"}},
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv("NANOBOT_CONFIG_PATH", str(env_config_path))
    monkeypatch.setattr(config_loader, "_current_config_path", None, raising=False)
    monkeypatch.setattr(config_loader, "get_config_path", lambda: default_config_path)

    loaded = _load_config()

    assert loaded.agents.defaults.workspace == str(tmp_path / "env-ws"), (
        f"Expected env config workspace '{tmp_path / 'env-ws'}', "
        f"got '{loaded.agents.defaults.workspace}'. "
        "_load_config() ignored NANOBOT_CONFIG_PATH and used the default path."
    )
