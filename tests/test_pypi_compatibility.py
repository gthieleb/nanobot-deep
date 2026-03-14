"""Unit tests for PyPI nanobot-ai compatibility.

Tests that nanobot-deep works correctly with the nanobot-ai package from PyPI,
handling differences in config schema between versions.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from nanobot_deep.config.schema import (
    DeepAgentsConfig,
    DeepAgentsBackendConfig,
)
from nanobot_deep.config.loader import (
    merge_with_nanobot_config,
    load_deepagents_config,
)


class TestPyPICompatibility:
    """Tests for compatibility with nanobot-ai from PyPI."""

    def _make_pypi_nanobot_config(self, **kwargs):
        """Create mock nanobot config matching PyPI nanobot-ai schema.

        PyPI version has:
        - agents.defaults.max_tool_iterations (no 'sandbox')
        - tools.exec.timeout, path_append
        - tools.restrict_to_workspace (NOT tools.exec.restrict_to_workspace)
        """
        mock = MagicMock()

        mock.agents.defaults.max_tool_iterations = kwargs.get("max_tool_iterations", 40)
        mock.agents.defaults.max_tokens = kwargs.get("max_tokens", 4096)
        mock.agents.defaults.temperature = kwargs.get("temperature", 0.1)
        mock.agents.defaults.memory_window = kwargs.get("memory_window", 10)
        mock.agents.defaults.model = kwargs.get("model", "gpt-4")

        mock.tools.exec.timeout = kwargs.get("exec_timeout", 60)
        mock.tools.exec.path_append = kwargs.get("path_append", "")

        mock.tools.restrict_to_workspace = kwargs.get("restrict_to_workspace", False)

        mock.workspace_path = kwargs.get("workspace", Path("/workspace"))

        return mock

    def test_pypi_config_recursion_limit(self):
        """Test recursion_limit is derived from max_tool_iterations in PyPI config."""
        nanobot = self._make_pypi_nanobot_config(max_tool_iterations=50)

        merged = merge_with_nanobot_config(nanobot)

        assert merged.recursion_limit == 60

    def test_pypi_config_exec_timeout(self):
        """Test exec_timeout from PyPI config is merged correctly."""
        nanobot = self._make_pypi_nanobot_config(exec_timeout=120)

        merged = merge_with_nanobot_config(nanobot)

        assert merged.backend.exec_timeout == 120

    def test_pypi_config_path_append(self):
        """Test path_append from PyPI config is merged correctly."""
        nanobot = self._make_pypi_nanobot_config(path_append="/usr/local/bin")

        merged = merge_with_nanobot_config(nanobot)

        assert merged.backend.path_append == "/usr/local/bin"

    def test_pypi_config_restrict_to_workspace(self):
        """Test restrict_to_workspace from tools level (PyPI schema)."""
        nanobot = self._make_pypi_nanobot_config(restrict_to_workspace=True)

        merged = merge_with_nanobot_config(nanobot)

        assert merged.backend.restrict_to_workspace is True

    def test_pypi_config_default_workspace_skills(self):
        """Test skills default to workspace/skills."""
        nanobot = self._make_pypi_nanobot_config(workspace=Path("/my/workspace"))

        merged = merge_with_nanobot_config(nanobot)

        assert len(merged.skills) >= 1
        assert "/my/workspace/skills" in merged.skills

    def test_pypi_config_no_sandbox_attribute(self):
        """Test that missing 'sandbox' attribute doesn't break loader.

        PyPI version doesn't have agents.defaults.sandbox attribute.
        The loader should not require it.
        """
        nanobot = self._make_pypi_nanobot_config()

        merged = merge_with_nanobot_config(nanobot)

        assert merged is not None
        assert isinstance(merged, DeepAgentsConfig)

    def test_pypi_config_all_defaults(self):
        """Test merge with all PyPI defaults."""
        nanobot = self._make_pypi_nanobot_config()

        merged = merge_with_nanobot_config(nanobot)

        assert merged.recursion_limit == 50
        assert merged.backend.exec_timeout == 60
        assert merged.backend.path_append == ""
        assert merged.backend.restrict_to_workspace is False


class TestSchemaCompatibility:
    """Tests for handling schema differences between nanobot versions."""

    def test_tools_restrict_to_workspace_at_tools_level(self):
        """Test restrict_to_workspace at tools level (PyPI schema)."""
        mock = MagicMock()
        mock.agents.defaults.max_tool_iterations = 40
        mock.tools.exec.timeout = 60
        mock.tools.exec.path_append = ""
        mock.tools.restrict_to_workspace = True
        mock.workspace_path = Path("/workspace")

        merged = merge_with_nanobot_config(mock)

        assert merged.backend.restrict_to_workspace is True

    def test_tools_restrict_to_workspace_missing(self):
        """Test graceful handling when restrict_to_workspace is missing."""
        mock = MagicMock()
        mock.agents.defaults.max_tool_iterations = 40
        mock.tools.exec.timeout = 60
        mock.tools.exec.path_append = ""
        mock.workspace_path = Path("/workspace")

        del mock.tools.restrict_to_workspace

        merged = merge_with_nanobot_config(mock)

        assert merged.backend.restrict_to_workspace is False


class TestRealConfigLoading:
    """Tests with actual nanobot config if available."""

    def test_load_real_nanobot_config(self):
        """Test loading real nanobot config from ~/.nanobot/config.json."""
        config_path = Path.home() / ".nanobot" / "config.json"

        if not config_path.exists():
            pytest.skip("No ~/.nanobot/config.json found")

        try:
            from nanobot.config.loader import load_config

            config = load_config()

            assert config.workspace_path is not None
            assert config.agents.defaults.max_tool_iterations > 0

            merged = merge_with_nanobot_config(config)

            assert merged.recursion_limit > 0
            assert len(merged.skills) > 0

        except Exception as e:
            pytest.fail(f"Failed to load/merge real config: {e}")

    def test_deepagents_config_with_real_nanobot(self):
        """Test DeepAgentsConfig creation with real nanobot config."""
        config_path = Path.home() / ".nanobot" / "config.json"

        if not config_path.exists():
            pytest.skip("No ~/.nanobot/config.json found")

        from nanobot.config.loader import load_config

        nanobot_config = load_config()
        deep_config = load_deepagents_config()

        merged = merge_with_nanobot_config(nanobot_config, deep_config)

        assert isinstance(merged, DeepAgentsConfig)
        assert merged.recursion_limit == nanobot_config.agents.defaults.max_tool_iterations + 10


class TestFutureCompatibility:
    """Tests for forward compatibility with potential future nanobot versions."""

    def test_handles_extra_nanobot_attributes(self):
        """Test that extra nanobot attributes don't break merging."""
        mock = MagicMock()
        mock.agents.defaults.max_tool_iterations = 40
        mock.tools.exec.timeout = 60
        mock.tools.exec.path_append = ""
        mock.tools.restrict_to_workspace = False
        mock.workspace_path = Path("/workspace")

        mock.agents.defaults.future_attribute = "some_value"
        mock.tools.future_tool = MagicMock()

        merged = merge_with_nanobot_config(mock)

        assert merged is not None
        assert isinstance(merged, DeepAgentsConfig)

    def test_deepagents_config_preserves_settings(self, tmp_path):
        """Test that deepagents.json settings are preserved during merge."""
        dg_path = tmp_path / "deepagents.json"
        dg_path.write_text(
            json.dumps(
                {
                    "debug": True,
                    "interrupt_on": {"edit_file": True, "execute": True},
                    "middleware": {"enable_todolist": False},
                }
            )
        )

        mock = MagicMock()
        mock.agents.defaults.max_tool_iterations = 40
        mock.tools.exec.timeout = 60
        mock.tools.exec.path_append = ""
        mock.tools.restrict_to_workspace = False
        mock.workspace_path = Path("/workspace")

        with patch("nanobot_deep.config.loader.get_deepagents_config_path", return_value=dg_path):
            merged = merge_with_nanobot_config(mock)

        assert merged.debug is True
        assert merged.interrupt_on.edit_file is True
        assert merged.interrupt_on.execute is True
        assert merged.middleware.enable_todolist is False
