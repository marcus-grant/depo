# tests/cli/test_defaults.py
"""
Tests for cli/defaults.py value production.
Author: Marcus Grant
Created: 2026-06-04
License: Apache-2.0
"""

from pathlib import Path

from depo.cli.defaults import _XDG_DATA_HOME, default_db_path, default_store_dir


class TestDefaultPaths:
    """Tests for path resolution helpers."""

    def test_store_dir_xdg(self, monkeypatch, tmp_path):
        """XDG_DATA_HOME set yields its depo/store subdir."""
        monkeypatch.setenv(_XDG_DATA_HOME, str(tmp_path))
        assert default_store_dir() == tmp_path / "depo" / "store"

    def test_store_dir_fallback(self, monkeypatch):
        """No XDG_DATA_HOME falls back to ./store."""
        monkeypatch.delenv(_XDG_DATA_HOME, raising=False)
        assert default_store_dir() == Path.cwd() / "store"

    def test_db_path_xdg(self, monkeypatch, tmp_path):
        """XDG_DATA_HOME set yields its depo/depo.db path."""
        monkeypatch.setenv(_XDG_DATA_HOME, str(tmp_path))
        assert default_db_path() == tmp_path / "depo" / "depo.db"

    def test_db_path_fallback(self, monkeypatch):
        """No XDG_DATA_HOME falls back to ./depo.db."""
        monkeypatch.delenv(_XDG_DATA_HOME, raising=False)
        assert default_db_path() == Path.cwd() / "depo.db"
