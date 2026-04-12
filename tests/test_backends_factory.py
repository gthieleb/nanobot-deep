from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from nanobot_deep.backends import factory as backend_factory


def test_get_available_backends_defaults(monkeypatch):
    def fake_find_spec(_name: str):
        return None

    monkeypatch.setattr(importlib.util, "find_spec", fake_find_spec)

    available = backend_factory.get_available_backends()
    assert available == [backend_factory.BackendType.LOCAL, backend_factory.BackendType.STATE]


def test_get_available_backends_with_optional(monkeypatch):
    def fake_find_spec(name: str):
        if name in {"langchain_modal", "langchain_daytona", "langchain_runloop"}:
            return object()
        return None

    monkeypatch.setattr(importlib.util, "find_spec", fake_find_spec)

    available = backend_factory.get_available_backends()
    assert backend_factory.BackendType.MODAL in available
    assert backend_factory.BackendType.DAYTONA in available
    assert backend_factory.BackendType.RUNLOOP in available


def test_create_backend_invalid_type():
    with pytest.raises(ValueError):
        backend_factory.create_backend("unknown")


def test_create_backend_local(monkeypatch, tmp_path):
    class FakeFilesystemBackend:
        def __init__(self, root_dir: Path):
            self.root_dir = root_dir

    from deepagents import backends as deep_backends

    monkeypatch.setattr(deep_backends, "FilesystemBackend", FakeFilesystemBackend)

    backend = backend_factory.create_backend("local", workspace=tmp_path)
    assert isinstance(backend, FakeFilesystemBackend)
    assert backend.root_dir == tmp_path


def test_create_backend_state(monkeypatch):
    class FakeStateBackend:
        def __init__(self, runtime):
            self.runtime = runtime

    from deepagents import backends as deep_backends

    monkeypatch.setattr(deep_backends, "StateBackend", FakeStateBackend)

    backend_factory_fn = backend_factory.create_backend("state")
    runtime = object()
    instance = backend_factory_fn(runtime)
    assert isinstance(instance, FakeStateBackend)
    assert instance.runtime is runtime


def test_create_backend_modal_import_error():
    if importlib.util.find_spec("langchain_modal") is not None:
        pytest.skip("langchain_modal installed")
    with pytest.raises(ImportError):
        backend_factory.create_backend("modal")
