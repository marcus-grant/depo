# tests/cli/test_config.py
"""
Tests for CLI configuration.

Author: Marcus Grant
Created: 2026-02-06
License: Apache-2.0
"""

import os
from pathlib import Path

import pytest
from tests.helpers.assertions import assert_field

from depo.cli.config import (
    _XDG_DATA_HOME,
    DepoConfig,
    _default_db_path,
    _default_store_dir,
    load_config,
)


def _clear_depo_env(monkeypatch):
    for key in list(os.environ):
        if key.startswith("DEPO_"):
            monkeypatch.delenv(key)


def _write_toml(path: Path, **kwargs) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for k, v in kwargs.items():
        if isinstance(v, str):
            lines.append(f'{k} = "{v}"')
        else:
            lines.append(f"{k} = {v}")
    path.write_text("\n".join(lines) + "\n")


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
            ("port", int, False, 8765),
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


class TestLoadConfigToml:
    """Tests for TOML file resolution chain."""

    def test_xdg_config_overrides_defaults(self, monkeypatch, tmp_path):
        _clear_depo_env(monkeypatch)
        toml_cfgs = {"host": "0.0.0.0", "port": 9000}
        _write_toml(tmp_path / "xdg/depo/config.toml", **toml_cfgs)
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
        monkeypatch.chdir(tmp_path)
        cfg = load_config()
        assert cfg.host == "0.0.0.0"
        assert cfg.port == 9000
        assert cfg.max_size_bytes == 10_485_760

    def test_local_toml_overrides_xdg(self, monkeypatch, tmp_path):
        _clear_depo_env(monkeypatch)
        # XDG says port 9000
        xdg_cfg = tmp_path / "xdg"
        (xdg_cfg / "depo").mkdir(parents=True)
        (xdg_cfg / "depo" / "config.toml").write_text("port = 9000\n")
        monkeypatch.setenv("XDG_CONFIG_HOME", str(xdg_cfg))
        # Local says port 7000
        workdir = tmp_path / "project"
        workdir.mkdir()
        (workdir / "depo.toml").write_text("port = 7000\n")
        monkeypatch.chdir(workdir)
        cfg = load_config()
        assert cfg.port == 7000

    def test_partial_toml_preserves_defaults(self, monkeypatch, tmp_path):
        _clear_depo_env(monkeypatch)
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "empty"))
        workdir = tmp_path / "proj"
        workdir.mkdir()
        (workdir / "depo.toml").write_text('host = "10.0.0.1"\n')
        monkeypatch.chdir(workdir)
        cfg = load_config()
        assert cfg.host == "10.0.0.1"
        assert cfg.port == 8765
        assert cfg.max_url_len == 2048


class TestLoadConfigEnv:
    """Tests for DEPO_* environment variable overrides."""

    def _clear_depo_env(self, monkeypatch):
        for key in list(os.environ):
            if key.startswith("DEPO_"):
                monkeypatch.delenv(key)

    def test_env_overrides_toml(self, monkeypatch, tmp_path):
        self._clear_depo_env(monkeypatch)
        workdir = tmp_path / "proj"
        workdir.mkdir()
        _write_toml(workdir / "depo.toml", port=7000)
        monkeypatch.chdir(workdir)
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "empty"))
        monkeypatch.setenv("DEPO_PORT", "5555")
        cfg = load_config()
        assert cfg.port == 5555

    def test_env_host(self, monkeypatch, tmp_path):
        self._clear_depo_env(monkeypatch)
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "empty"))
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("DEPO_HOST", "192.168.1.1")
        cfg = load_config()
        assert cfg.host == "192.168.1.1"

    def test_env_path_expansion(self, monkeypatch, tmp_path):
        self._clear_depo_env(monkeypatch)
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "empty"))
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("DEPO_DB_PATH", "~/my-depo/data.db")
        cfg = load_config()
        assert cfg.db_path == Path.home() / "my-depo/data.db"

    def test_env_int_coercion(self, monkeypatch, tmp_path):
        self._clear_depo_env(monkeypatch)
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "empty"))
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("DEPO_MAX_SIZE_BYTES", "5242880")
        cfg = load_config()
        assert cfg.max_size_bytes == 5_242_880


class TestLoadConfigFlag:
    """Tests for config_path parameter (--config flag)."""

    def _clear_depo_env(self, monkeypatch):
        for key in list(os.environ):
            if key.startswith("DEPO_"):
                monkeypatch.delenv(key)

    def test_config_path_overrides_toml_chain(self, monkeypatch, tmp_path):
        self._clear_depo_env(monkeypatch)
        _write_toml(tmp_path / "xdg/depo/config.toml", port=9000)
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
        monkeypatch.chdir(tmp_path)
        explicit = tmp_path / "custom.toml"
        _write_toml(explicit, port=1234)
        cfg = load_config(config_path=explicit)
        assert cfg.port == 1234

    def test_missing_config_path_raises(self, monkeypatch, tmp_path):
        self._clear_depo_env(monkeypatch)
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "empty"))
        monkeypatch.chdir(tmp_path)
        with pytest.raises(FileNotFoundError):
            load_config(config_path=tmp_path / "nonexistent.toml")

    def test_env_layers_on_config_path(self, monkeypatch, tmp_path):
        self._clear_depo_env(monkeypatch)
        explicit = tmp_path / "custom.toml"
        _write_toml(explicit, port=1234)
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "empty"))
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("DEPO_HOST", "10.0.0.5")
        cfg = load_config(config_path=explicit)
        assert cfg.port == 1234
        assert cfg.host == "10.0.0.5"
