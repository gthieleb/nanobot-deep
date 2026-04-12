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


def resolve_deepagents_cli():
    try:
        from deepagents_cli import config as deepagents_config
        from deepagents_cli.mcp_tools import resolve_and_load_mcp_tools
        from deepagents_cli.project_utils import ProjectContext
    except ImportError:
        return None

    try:
        from deepagents_cli import model_config
    except ImportError:
        model_config_error = Exception
    else:
        model_config_error = getattr(model_config, "ModelConfigError", Exception)

    model_config_error = getattr(deepagents_config, "ModelConfigError", model_config_error)
    return (
        deepagents_config.create_model,
        model_config_error,
        resolve_and_load_mcp_tools,
        ProjectContext,
    )
