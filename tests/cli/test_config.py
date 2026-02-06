# tests/cli/test_config.py
"""
Tests for CLI configuration.

Author: Marcus Grant
Created: 2026-02-06
License: Apache-2.0
"""

from pathlib import Path

import pytest
from tests.helpers.assertions import assert_field

from depo.cli.config import (
    _XDG_DATA_HOME,
    DepoConfig,
    _default_db_path,
    _default_store_dir,
)


class TestDefaultPaths:
    """Tests for path resolution helpers."""

    def test_store_dir_xdg(self, monkeypatch, tmp_path):
        monkeypatch.setenv(_XDG_DATA_HOME, str(tmp_path))
        assert _default_store_dir() == tmp_path / "depo" / "store"

    def test_store_dir_fallback(self, monkeypatch):
        monkeypatch.delenv(_XDG_DATA_HOME, raising=False)
        assert _default_store_dir() == Path.cwd() / "store"

    def test_db_path_xdg(self, monkeypatch, tmp_path):
        monkeypatch.setenv(_XDG_DATA_HOME, str(tmp_path))
        assert _default_db_path() == tmp_path / "depo" / "depo.db"

    def test_db_path_fallback(self, monkeypatch):
        monkeypatch.delenv(_XDG_DATA_HOME, raising=False)
        assert _default_db_path() == Path.cwd() / "depo.db"


class TestDepoConfig:
    """Tests for DepoConfig frozen dataclass."""

    @pytest.mark.parametrize(
        ("name", "typ", "required", "default"),
        [
            ("host", str, False, "127.0.0.1"),
            ("port", int, False, 8000),
            ("max_size_bytes", int, False, 10_485_760),
            ("max_url_len", int, False, 2048),
        ],
    )
    def test_simple_fields(self, name, typ, required, default):
        assert_field(DepoConfig, name, typ, required, default)

    @pytest.mark.parametrize("name", ["db_path", "store_root"])
    def test_path_fields_are_paths(self, name):
        """Factory defaults resolve to Path — value depends on env."""
        cfg = DepoConfig()
        assert isinstance(getattr(cfg, name), Path)

    def test_frozen(self):
        cfg = DepoConfig()
        with pytest.raises(AttributeError):
            cfg.port = 9999  # type: ignore[misc]

    def test_keyword_only(self):
        with pytest.raises(TypeError):
            DepoConfig("127.0.0.1")  # type: ignore[misc]

    def test_override_preserves_defaults(self):
        cfg = DepoConfig(host="0.0.0.0", port=3000)
        assert cfg.host == "0.0.0.0"
        assert cfg.port == 3000
        assert cfg.max_size_bytes == 10_485_760
        assert cfg.max_url_len == 2048
