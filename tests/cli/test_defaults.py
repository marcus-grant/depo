# tests/cli/test_defaults.py
"""
Tests for cli/defaults.py value production.
Author: Marcus Grant
Created: 2026-06-04
License: Apache-2.0
"""

from pathlib import Path

from depo.cli import defaults


class TestDefaultPaths:
    """Tests for path resolution helpers."""

    def test_store_dir_xdg(self, monkeypatch, tmp_path):
        """XDG_DATA_HOME set yields its depo/store subdir."""
        monkeypatch.setenv(defaults._XDG_DATA_HOME, str(tmp_path))
        assert defaults.default_store_dir() == tmp_path / "depo" / "store"

    def test_store_dir_fallback(self, monkeypatch):
        """No XDG_DATA_HOME falls back to ./store."""
        monkeypatch.delenv(defaults._XDG_DATA_HOME, raising=False)
        assert defaults.default_store_dir() == Path.cwd() / "store"

    def test_db_path_xdg(self, monkeypatch, tmp_path):
        """XDG_DATA_HOME set yields its depo/depo.db path."""
        monkeypatch.setenv(defaults._XDG_DATA_HOME, str(tmp_path))
        assert defaults.default_db_path() == tmp_path / "depo" / "depo.db"

    def test_db_path_fallback(self, monkeypatch):
        """No XDG_DATA_HOME falls back to ./depo.db."""
        monkeypatch.delenv(defaults._XDG_DATA_HOME, raising=False)
        assert defaults.default_db_path() == Path.cwd() / "depo.db"


class TestScryptDefaults:
    """Tests for scrypt cost constants in defaults."""

    def test_scrypt_constants(self):
        """SCRYPT_N, SCRYPT_R, SCRYPT_P have correct default values."""
        assert defaults.SCRYPT_N == 2**16
        assert defaults.SCRYPT_R == 8
        assert defaults.SCRYPT_P == 1
