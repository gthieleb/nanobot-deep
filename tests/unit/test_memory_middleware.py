"""Unit tests for memory middleware configuration."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from nanobot_deep.config.schema import (
    DeepAgentsConfig,
    DeepAgentsMemorySourceConfig,
)


class TestMemoryConfigLoading:
    """Tests for memory config parsing from dict."""

    def test_memory_config_loading(self):
        """Test that memory config parses correctly from dict."""
        data = {
            "type": "conversation",
            "path": "~/.nanobot/workspace/memory/MEMORY.md",
            "max_tokens": 4000,
        }

        config = DeepAgentsMemorySourceConfig(**data)

        assert config.type == "conversation"
        assert config.path == "~/.nanobot/workspace/memory/MEMORY.md"
        assert config.max_tokens == 4000
        assert config.enabled is True

    def test_memory_config_from_dict_with_knowledge_type(self):
        """Test memory config with knowledge type."""
        data = {
            "type": "knowledge",
            "path": "/absolute/path/knowledge.md",
            "max_tokens": 8000,
            "enabled": False,
        }

        config = DeepAgentsMemorySourceConfig(**data)

        assert config.type == "knowledge"
        assert config.path == "/absolute/path/knowledge.md"
        assert config.max_tokens == 8000
        assert config.enabled is False

    def test_memory_config_in_deepagents_config(self):
        """Test memory config is properly included in DeepAgentsConfig."""
        config = DeepAgentsConfig(
            memory=[
                DeepAgentsMemorySourceConfig(
                    type="conversation",
                    path="~/MEMORY.md",
                    max_tokens=2000,
                )
            ]
        )

        assert len(config.memory) == 1
        assert config.memory[0].type == "conversation"
        assert config.memory[0].path == "~/MEMORY.md"
        assert config.memory[0].max_tokens == 2000

    def test_memory_config_from_dict_nested(self):
        """Test loading nested memory config via model_validate."""
        config = DeepAgentsConfig.model_validate(
            {
                "memory": [
                    {
                        "type": "conversation",
                        "path": "~/.nanobot/MEMORY.md",
                        "max_tokens": 6000,
                    }
                ]
            }
        )

        assert len(config.memory) == 1
        assert config.memory[0].type == "conversation"
        assert config.memory[0].max_tokens == 6000


class TestMemoryMiddlewareInitialization:
    """Tests for DeepAgentsMemorySourceConfig initialization."""

    def test_memory_middleware_initialization(self):
        """Test DeepAgentsMemorySourceConfig initialization."""
        config = DeepAgentsMemorySourceConfig(
            type="conversation",
            path="~/memory.md",
            max_tokens=4000,
        )

        assert config.type == "conversation"
        assert config.path == "~/memory.md"
        assert config.max_tokens == 4000
        assert config.enabled is True

    def test_initialization_minimal(self):
        """Test initialization with only required fields."""
        config = DeepAgentsMemorySourceConfig(path="~/memory.md")

        assert config.type == "conversation"
        assert config.max_tokens == 4000
        assert config.enabled is True

    def test_initialization_all_fields(self):
        """Test initialization with all fields specified."""
        config = DeepAgentsMemorySourceConfig(
            type="knowledge",
            path="/custom/path/memory.md",
            max_tokens=16000,
            enabled=False,
        )

        assert config.type == "knowledge"
        assert config.path == "/custom/path/memory.md"
        assert config.max_tokens == 16000
        assert config.enabled is False


class TestMemoryFileMissing:
    """Tests for handling of missing memory files."""

    def test_memory_file_missing_graceful(self):
        """Test handling of missing memory file (graceful)."""
        config = DeepAgentsMemorySourceConfig(path="~/nonexistent/memory.md")

        expanded = config.get_expanded_path()
        assert isinstance(expanded, str)
        assert "nonexistent/memory.md" in expanded

    def test_memory_file_missing_does_not_raise(self, tmp_path):
        """Test that missing file doesn't raise during config creation."""
        missing_path = tmp_path / "nonexistent" / "MEMORY.md"

        config = DeepAgentsMemorySourceConfig(path=str(missing_path))

        assert config.path == str(missing_path)

    def test_get_memory_paths_returns_path_even_if_missing(self, tmp_path):
        """Test get_memory_paths returns path even if file doesn't exist."""
        config = DeepAgentsConfig(
            memory=[DeepAgentsMemorySourceConfig(path=str(tmp_path / "missing" / "MEMORY.md"))]
        )

        paths = config.get_memory_paths()
        assert len(paths) == 1
        assert "missing/MEMORY.md" in paths[0]


class TestMemoryInvalidPath:
    """Tests for validation of invalid paths."""

    def test_memory_path_empty_string_accepted(self):
        """Test empty path is accepted (validation happens at runtime)."""
        config = DeepAgentsMemorySourceConfig(path="")
        assert config.path == ""

    def test_memory_path_expansion_empty_returns_current_dir(self):
        """Test that empty path expands to current directory."""
        config = DeepAgentsMemorySourceConfig(path="")
        expanded = config.get_expanded_path()
        assert expanded == "."

    def test_memory_max_tokens_below_minimum(self):
        """Test validation rejects max_tokens below minimum."""
        with pytest.raises(ValidationError) as exc_info:
            DeepAgentsMemorySourceConfig(
                path="~/memory.md",
                max_tokens=50,
            )

        errors = exc_info.value.errors()
        assert any("max_tokens" in str(e["loc"]) for e in errors)

    def test_memory_max_tokens_above_maximum(self):
        """Test validation rejects max_tokens above maximum."""
        with pytest.raises(ValidationError) as exc_info:
            DeepAgentsMemorySourceConfig(
                path="~/memory.md",
                max_tokens=20000,
            )

        errors = exc_info.value.errors()
        assert any("max_tokens" in str(e["loc"]) for e in errors)

    def test_memory_invalid_type(self):
        """Test validation rejects invalid memory type."""
        with pytest.raises(ValidationError) as exc_info:
            DeepAgentsMemorySourceConfig(
                type="invalid_type",
                path="~/memory.md",
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("type",) for e in errors)

    def test_memory_path_as_none(self):
        """Test validation rejects None as path."""
        with pytest.raises(ValidationError) as exc_info:
            DeepAgentsMemorySourceConfig(path=None)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("path",) for e in errors)


class TestMemoryDisabledSource:
    """Tests for disabled memory sources."""

    def test_memory_disabled_source(self):
        """Test that disabled memory sources are excluded."""
        config = DeepAgentsConfig(
            memory=[
                DeepAgentsMemorySourceConfig(
                    path="~/enabled.md",
                    enabled=True,
                ),
                DeepAgentsMemorySourceConfig(
                    path="~/disabled.md",
                    enabled=False,
                ),
            ]
        )

        paths = config.get_memory_paths()

        assert len(paths) == 1
        assert "enabled.md" in paths[0]
        assert "disabled.md" not in paths[0]

    def test_all_sources_disabled(self):
        """Test when all memory sources are disabled."""
        config = DeepAgentsConfig(
            memory=[
                DeepAgentsMemorySourceConfig(
                    path="~/first.md",
                    enabled=False,
                ),
                DeepAgentsMemorySourceConfig(
                    path="~/second.md",
                    enabled=False,
                ),
            ]
        )

        paths = config.get_memory_paths()
        assert len(paths) == 0

    def test_enabled_field_default_true(self):
        """Test that enabled defaults to True."""
        config = DeepAgentsMemorySourceConfig(path="~/memory.md")

        assert config.enabled is True


class TestMemoryPathExpansion:
    """Tests for path expansion in memory config."""

    def test_memory_path_expansion(self):
        """Test ~ expansion in paths."""
        config = DeepAgentsMemorySourceConfig(path="~/workspace/memory/MEMORY.md")

        expanded = config.get_expanded_path()
        home = str(Path.home())

        assert expanded == f"{home}/workspace/memory/MEMORY.md"
        assert "~" not in expanded

    def test_path_expansion_absolute(self):
        """Test absolute paths are preserved."""
        config = DeepAgentsMemorySourceConfig(path="/absolute/path/MEMORY.md")

        expanded = config.get_expanded_path()

        assert expanded == "/absolute/path/MEMORY.md"

    def test_path_expansion_with_workspace(self):
        """Test relative paths are resolved relative to workspace."""
        config = DeepAgentsMemorySourceConfig(path="relative/memory.md")

        workspace = Path("/workspace")
        expanded = config.get_expanded_path(workspace)

        assert expanded == "/workspace/relative/memory.md"

    def test_path_expansion_absolute_ignores_workspace(self):
        """Test absolute paths ignore workspace parameter."""
        config = DeepAgentsMemorySourceConfig(path="/absolute/MEMORY.md")

        workspace = Path("/workspace")
        expanded = config.get_expanded_path(workspace)

        assert expanded == "/absolute/MEMORY.md"

    def test_get_memory_paths_expansion(self):
        """Test get_memory_paths expands all paths."""
        config = DeepAgentsConfig(
            memory=[
                DeepAgentsMemorySourceConfig(path="~/first.md"),
                DeepAgentsMemorySourceConfig(path="/absolute/second.md"),
            ]
        )

        paths = config.get_memory_paths()
        home = str(Path.home())

        assert paths[0] == f"{home}/first.md"
        assert paths[1] == "/absolute/second.md"

    def test_get_memory_paths_with_workspace(self):
        """Test get_memory_paths with workspace for relative paths."""
        config = DeepAgentsConfig(
            memory=[
                DeepAgentsMemorySourceConfig(path="~/absolute.md"),
                DeepAgentsMemorySourceConfig(path="relative.md"),
            ]
        )

        workspace = Path("/my/workspace")
        paths = config.get_memory_paths(workspace)
        home = str(Path.home())

        assert paths[0] == f"{home}/absolute.md"
        assert paths[1] == "/my/workspace/relative.md"


class TestMemoryConfigDefaults:
    """Tests for default values in memory config."""

    def test_memory_config_defaults(self):
        """Test default values for memory config."""
        config = DeepAgentsMemorySourceConfig(path="~/memory.md")

        assert config.type == "conversation"
        assert config.max_tokens == 4000
        assert config.enabled is True

    def test_deepagents_config_memory_defaults_empty(self):
        """Test DeepAgentsConfig has empty memory list by default."""
        config = DeepAgentsConfig()

        assert config.memory == []
        assert config.get_memory_paths() == []

    def test_max_tokens_boundary_values(self):
        """Test max_tokens at boundary values."""
        min_config = DeepAgentsMemorySourceConfig(
            path="~/memory.md",
            max_tokens=100,
        )
        assert min_config.max_tokens == 100

        max_config = DeepAgentsMemorySourceConfig(
            path="~/memory.md",
            max_tokens=16000,
        )
        assert max_config.max_tokens == 16000


class TestMultipleMemorySources:
    """Tests for multiple memory sources in config."""

    def test_multiple_memory_sources(self):
        """Test multiple memory sources in config."""
        config = DeepAgentsConfig(
            memory=[
                DeepAgentsMemorySourceConfig(
                    type="conversation",
                    path="~/conversation.md",
                    max_tokens=4000,
                ),
                DeepAgentsMemorySourceConfig(
                    type="knowledge",
                    path="~/knowledge.md",
                    max_tokens=8000,
                ),
            ]
        )

        assert len(config.memory) == 2
        assert config.memory[0].type == "conversation"
        assert config.memory[1].type == "knowledge"
        assert config.memory[0].max_tokens == 4000
        assert config.memory[1].max_tokens == 8000

    def test_get_memory_paths_order_preserved(self):
        """Test that get_memory_paths preserves order."""
        config = DeepAgentsConfig(
            memory=[
                DeepAgentsMemorySourceConfig(path="~/first.md"),
                DeepAgentsMemorySourceConfig(path="~/second.md"),
                DeepAgentsMemorySourceConfig(path="~/third.md"),
            ]
        )

        paths = config.get_memory_paths()

        assert len(paths) == 3
        assert "first.md" in paths[0]
        assert "second.md" in paths[1]
        assert "third.md" in paths[2]

    def test_multiple_sources_from_dict(self):
        """Test loading multiple sources from dict."""
        config = DeepAgentsConfig.model_validate(
            {
                "memory": [
                    {
                        "type": "conversation",
                        "path": "~/.nanobot/memory/conversation.md",
                        "max_tokens": 2000,
                    },
                    {
                        "type": "knowledge",
                        "path": "~/.nanobot/memory/knowledge.md",
                        "max_tokens": 6000,
                        "enabled": False,
                    },
                    {
                        "type": "conversation",
                        "path": "/absolute/memory.md",
                    },
                ]
            }
        )

        assert len(config.memory) == 3
        assert config.memory[0].enabled is True
        assert config.memory[1].enabled is False
        assert config.memory[2].max_tokens == 4000

    def test_mixed_enabled_disabled_sources(self):
        """Test filtering with mixed enabled/disabled sources."""
        config = DeepAgentsConfig(
            memory=[
                DeepAgentsMemorySourceConfig(path="~/enabled1.md", enabled=True),
                DeepAgentsMemorySourceConfig(path="~/disabled1.md", enabled=False),
                DeepAgentsMemorySourceConfig(path="~/enabled2.md", enabled=True),
                DeepAgentsMemorySourceConfig(path="~/disabled2.md", enabled=False),
            ]
        )

        paths = config.get_memory_paths()

        assert len(paths) == 2
        assert any("enabled1.md" in p for p in paths)
        assert any("enabled2.md" in p for p in paths)
        assert not any("disabled1.md" in p for p in paths)
        assert not any("disabled2.md" in p for p in paths)


class TestMemoryTypeValidation:
    """Tests for memory type validation."""

    def test_conversation_type_valid(self):
        """Test conversation type is valid."""
        config = DeepAgentsMemorySourceConfig(
            type="conversation",
            path="~/memory.md",
        )
        assert config.type == "conversation"

    def test_knowledge_type_valid(self):
        """Test knowledge type is valid."""
        config = DeepAgentsMemorySourceConfig(
            type="knowledge",
            path="~/memory.md",
        )
        assert config.type == "knowledge"

    def test_type_case_sensitive(self):
        """Test that type validation is case sensitive."""
        with pytest.raises(ValidationError):
            DeepAgentsMemorySourceConfig(
                type="Conversation",
                path="~/memory.md",
            )
