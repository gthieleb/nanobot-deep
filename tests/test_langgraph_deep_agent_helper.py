from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from nanobot_deep.langgraph import deep_agent_helper


def test_create_backend_none(monkeypatch, tmp_path):
    class FakeFilesystemBackend:
        def __init__(self, root_dir):
            self.root_dir = root_dir

    from deepagents import backends as deep_backends

    monkeypatch.setattr(deep_backends, "FilesystemBackend", FakeFilesystemBackend)

    backend = deep_agent_helper._create_backend("none", tmp_path)
    assert isinstance(backend, FakeFilesystemBackend)
    assert backend.root_dir == tmp_path


def test_create_backend_unknown():
    with pytest.raises(ValueError):
        deep_agent_helper._create_backend("unknown", Path("/tmp"))


@pytest.mark.asyncio
async def test_run_ralph_mode_stream_false(monkeypatch, tmp_path):
    class FakeAgent:
        async def ainvoke(self, _state, _config):
            return {"messages": [SimpleNamespace(content="done")]}

    def fake_create_model(model_spec=None):
        return SimpleNamespace(model=object())

    def fake_create_deep_agent(**_kwargs):
        return FakeAgent()

    monkeypatch.setattr(
        deep_agent_helper,
        "resolve_deepagents_cli",
        lambda: (fake_create_model, Exception, None, None),
    )
    monkeypatch.setattr(deep_agent_helper, "_create_backend", lambda _sandbox, _workspace: object())

    import deepagents

    monkeypatch.setattr(deepagents, "create_deep_agent", fake_create_deep_agent)

    await deep_agent_helper.run_ralph_mode(
        task="test",
        max_iterations=1,
        workspace=tmp_path,
        stream=False,
    )
