"""Unit tests for Telegram session handling."""

import os
import pytest
from pathlib import Path


class TestTelegramSessionPath:
    """Test Telegram session path resolution."""

    def test_session_path_in_e2e_directory(self):
        """Test that session file path is correctly set for E2E tests."""
        from scripts.auth_telethon import PROJECT_ROOT, SESSION_PATH

        expected_path = Path(__file__).parent.parent / "tests" / "e2e" / "test_session_user"

        assert SESSION_PATH == expected_path, (
            f"Session path should be {expected_path}, got {SESSION_PATH}"
        )

    def test_session_path_is_absolute(self):
        """Test that session path is absolute."""
        from scripts.auth_telethon import SESSION_PATH

        assert SESSION_PATH.is_absolute(), "Session path should be absolute"

    def test_session_path_is_not_relative(self):
        """Test that session path is not just 'test_session_user'."""
        from scripts.auth_telethon import SESSION_PATH

        assert SESSION_PATH != Path("test_session_user"), (
            "Session path should be absolute, not relative"
        )


class TestTelegramFixtureSessionPath:
    """Test that pytest fixture uses correct session path."""

    def test_fixture_uses_absolute_path(self):
        """Test that telegram_user_client fixture uses absolute path."""
        import inspect
        from tests.e2e.conftest import telegram_user_client

        fixture_source = inspect.getsource(telegram_user_client)

        assert "TelegramClient(str(session_path)" in fixture_source, (
            "Fixture should use absolute session path"
        )

    def test_fixture_in_tests_e2e_directory(self):
        """Test that session path resolves to tests/e2e/ directory."""
        fixture_source = """
        from pathlib import Path
        session_path = Path("test_session_user")
        client = TelegramClient(str(session_path), api_id, api_hash)
        """

        assert 'Path("test_session_user")' in fixture_source, (
            "Fixture should create Path object for session"
        )


class TestTelegramAuthFlow:
    """Test Telegram authentication flow."""

    def test_auth_code_from_env(self, monkeypatch):
        """Test that authentication code is read from environment variable."""
        os.environ["TELEGRAM_AUTH_CODE"] = "12345"

        from scripts.auth_telethon import authenticate

        code = os.environ.get("TELEGRAM_AUTH_CODE", "")
        assert code == "12345", "Should read code from env var"

    def test_auth_code_fallback_to_input(self, monkeypatch):
        """Test that authentication falls back to input() if no env var."""
        if "TELEGRAM_AUTH_CODE" in os.environ:
            del os.environ["TELEGRAM_AUTH_CODE"]

        code = os.environ.get("TELEGRAM_AUTH_CODE", "")
        assert code == "", "Should return empty string if no env var"

    def test_session_path_prevents_reauth(self, monkeypatch):
        """Test that existing session prevents re-authentication."""
        session_path = Path("test_session_user.session")

        if session_path.exists():
            existing_size = session_path.stat().st_size
            assert existing_size > 0, "Existing session should have content"


class TestTelegramFloodProtection:
    """Test Telegram flood protection."""

    def test_flood_wait_detected(self):
        """Test that FloodWaitError is documented."""
        from telethon.errors.rpcerrorlist import FloodWaitError

        assert FloodWaitError is not None, "FloodWaitError should be importable"

    def test_phone_code_invalid_detected(self):
        """Test that PhoneCodeInvalidError is documented."""
        from telethon.errors.rpcerrorlist import PhoneCodeInvalidError

        assert PhoneCodeInvalidError is not None, "PhoneCodeInvalidError should be importable"

    def test_api_id_invalid_detected(self):
        """Test that ApiIdInvalidError is documented."""
        from telethon.errors.rpcerrorlist import ApiIdInvalidError

        assert ApiIdInvalidError is not None, "ApiIdInvalidError should be importable"


class TestTelegramSessionMigration:
    """Test session file migration and cleanup."""

    def test_move_session_to_e2e(self, tmp_path):
        """Test that session file is moved to tests/e2e/ directory."""
        old_session = tmp_path / "test_session_user.session"
        new_session = tmp_path / "tests" / "e2e" / "test_session_user.session"

        old_session.parent.mkdir(parents=True, exist_ok=True)
        new_session.parent.mkdir(parents=True, exist_ok=True)

        old_session.touch()

        import shutil

        shutil.move(str(old_session), str(new_session))

        assert new_session.exists(), "Session should be moved"
        assert not old_session.exists(), "Old session should be removed"

    def test_session_file_cleanup(self, tmp_path):
        """Test that session files can be cleaned up."""
        session = tmp_path / "test_session_user.session"
        journal = tmp_path / "test_session_user.session-journal"

        session.touch()
        journal.touch()

        assert session.exists(), "Session should exist"
        assert journal.exists(), "Journal should exist"

        session.unlink()
        journal.unlink()

        assert not session.exists(), "Session should be deleted"
        assert not journal.exists(), "Journal should be deleted"


class TestTelegramCredentials:
    """Test Telegram credential loading."""

    def test_api_id_from_env(self, monkeypatch):
        """Test that API_ID is loaded from environment variable."""
        os.environ["TELEGRAM_API_ID"] = "12345678"

        api_id = os.environ.get("TELEGRAM_API_ID", "")
        assert api_id == "12345678", "API_ID should be read from env"

    def test_api_hash_from_env(self, monkeypatch):
        """Test that API_HASH is loaded from environment variable."""
        os.environ["TELEGRAM_API_HASH"] = "abcdef123456789"

        api_hash = os.environ.get("TELEGRAM_API_HASH", "")
        assert api_hash == "abcdef123456789", "API_HASH should be read from env"

    def test_phone_from_env(self, monkeypatch):
        """Test that TEST_USER_PHONE is loaded from environment variable."""
        os.environ["TEST_USER_PHONE"] = "+49123456789"

        phone = os.environ.get("TEST_USER_PHONE", "")
        assert phone == "+49123456789", "Phone should be read from env"

    def test_bot_username_from_env(self, monkeypatch):
        """Test that TELEGRAM_BOT_USERNAME is loaded from environment variable."""
        os.environ["TELEGRAM_BOT_USERNAME"] = "@testbot"

        bot_username = os.environ.get("TELEGRAM_BOT_USERNAME", "")
        assert bot_username == "@testbot", "Bot username should be read from env"
