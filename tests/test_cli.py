from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
import typer

from nanobot_deep import cli


def test_load_config_missing_path(tmp_path):
    missing = tmp_path / "missing.json"
    with pytest.raises(typer.Exit) as exc:
        cli._load_config(str(missing))
    assert exc.value.exit_code == 1


def test_load_config_sets_workspace(tmp_path, monkeypatch):
    cfg_file = tmp_path / "config.json"
    cfg_file.write_text("{}")

    defaults = SimpleNamespace(workspace=None)
    agents = SimpleNamespace(defaults=defaults)
    config = SimpleNamespace(agents=agents)

    import nanobot.config.loader as config_loader

    def fake_load_config(_path=None):
        return config

    def fake_set_config_path(_path):
        return None

    monkeypatch.setattr(config_loader, "load_config", fake_load_config)
    monkeypatch.setattr(config_loader, "set_config_path", fake_set_config_path, raising=False)

    loaded = cli._load_config(str(cfg_file), workspace="/tmp/work")
    assert loaded.agents.defaults.workspace == "/tmp/work"


def test_sync_workspace_templates(monkeypatch, tmp_path):
    called = {}

    def fake_sync(path: Path):
        called["path"] = path

    import nanobot.utils.helpers as helpers

    monkeypatch.setattr(helpers, "sync_workspace_templates", fake_sync)
    cli._sync_workspace_templates(tmp_path)
    assert called["path"] == tmp_path


def test_main_no_subcommand(monkeypatch):
    output = {}

    def fake_echo(msg):
        output["msg"] = msg

    monkeypatch.setattr(typer, "echo", fake_echo)
    ctx = SimpleNamespace(invoked_subcommand=None)
    cli.main(ctx)
    assert "--help" in output["msg"]
