from __future__ import annotations

import os
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import SimpleNamespace

import pytest


def _load_e2e_conftest_module():
    conftest_path = Path(__file__).parent / "e2e" / "conftest.py"
    spec = spec_from_file_location("tests_e2e_conftest", conftest_path)
    module = module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


class TestE2ELiveModelConfig:
    def test_apply_test_api_key_override_requires_model_spec(self, monkeypatch):
        e2e_conftest = _load_e2e_conftest_module()
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        error = e2e_conftest._apply_test_api_key_override(None, "sk-test")

        assert error is not None
        assert "DEEPAGENTS_TEST_MODEL" in error

    def test_apply_test_api_key_override_sets_provider_env(self, monkeypatch):
        e2e_conftest = _load_e2e_conftest_module()
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        error = e2e_conftest._apply_test_api_key_override("openai:gpt-5.2", "sk-test")

        assert error is None
        assert "sk-test" == os.environ["OPENAI_API_KEY"]

    def test_live_model_result_prefers_deepagents_test_model(self, monkeypatch):
        e2e_conftest = _load_e2e_conftest_module()
        monkeypatch.setenv("DEEPAGENTS_TEST_MODEL", "openai:gpt-5.2")
        monkeypatch.setenv("NANOBOT_TEST_MODEL", "anthropic:claude-sonnet-4-6")
        monkeypatch.delenv("NANOBOT_TEST_API_KEY", raising=False)

        calls: list[str | None] = []

        def fake_create_model(model_spec):
            calls.append(model_spec)
            return SimpleNamespace(provider="openai", model_name="gpt-5.2")

        monkeypatch.setattr("deepagents_cli.config.create_model", fake_create_model)

        result = e2e_conftest.live_model_result.__wrapped__()

        assert calls == ["openai:gpt-5.2"]
        assert result.provider == "openai"

    def test_live_model_result_skips_when_model_config_invalid(self, monkeypatch):
        e2e_conftest = _load_e2e_conftest_module()
        from deepagents_cli.config import ModelConfigError

        monkeypatch.setenv("DEEPAGENTS_TEST_MODEL", "invalid:model")
        monkeypatch.delenv("NANOBOT_TEST_MODEL", raising=False)
        monkeypatch.delenv("NANOBOT_TEST_API_KEY", raising=False)

        def raise_model_error(_model_spec):
            raise ModelConfigError("bad model")

        monkeypatch.setattr("deepagents_cli.config.create_model", raise_model_error)

        with pytest.raises(pytest.skip.Exception, match="DeepAgents model config is not ready"):
            e2e_conftest.live_model_result.__wrapped__()

    def test_live_model_result_skips_when_test_api_key_has_no_model(self, monkeypatch):
        e2e_conftest = _load_e2e_conftest_module()
        monkeypatch.delenv("DEEPAGENTS_TEST_MODEL", raising=False)
        monkeypatch.delenv("NANOBOT_TEST_MODEL", raising=False)
        monkeypatch.setenv("NANOBOT_TEST_API_KEY", "sk-test")

        with pytest.raises(pytest.skip.Exception, match="DEEPAGENTS_TEST_MODEL"):
            e2e_conftest.live_model_result.__wrapped__()
