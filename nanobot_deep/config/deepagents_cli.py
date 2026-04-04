"""Helpers for DeepAgents CLI configuration."""

from __future__ import annotations

import os
from pathlib import Path


def apply_deepagents_config_path() -> Path | None:
    config_path = os.environ.get("DEEPAGENTS_CONFIG_PATH")
    if not config_path:
        return None

    path = Path(config_path).expanduser()
    try:
        from deepagents_cli import model_config
    except ImportError:
        return path

    model_config.DEFAULT_CONFIG_PATH = path
    model_config.DEFAULT_CONFIG_DIR = path.parent
    model_config.clear_caches()
    return path
