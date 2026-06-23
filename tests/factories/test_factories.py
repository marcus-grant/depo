# tests/factories/test_factories.py
"""
Tests for the test factories.
Exercises the reusable builders in tests/factories,
starting with make_config keyword overrides.
Author: Marcus Grant
Created: 2026-06-04
License: Apache-2.0
"""

from pathlib import Path

from depo.model.user import User
from tests.factories import make_config
from tests.factories.models import make_user


class TestMakeConfig:
    """Tests for the make_config factory."""

    def test_override_reaches_config(self, tmp_path: Path) -> None:
        """An applied keyword override lands on the returned config."""
        assert make_config(tmp_path, max_size_bytes=1).max_size_bytes == 1
        assert make_config(tmp_path, log_level="INFO").log_level == "INFO"

    def test_default_session_secret_present(self, tmp_path: Path) -> None:
        """make_config provides a non-empty session_secret by default."""
        assert make_config(tmp_path).session_secret != ""


class TestMakeUser:
    """Tests for the make_user factory."""

    def test_returns_user(self):
        """make_user() returns a User instance."""
        assert isinstance(make_user(), User)

    def test_overrides_apply(self):
        """Keyword overrides replace default field values."""
        assert make_user(id=99).id == 99
