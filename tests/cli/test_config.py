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

from depo.cli import defaults
from depo.cli.config import DepoConfig, _coerce_bool, load_config
from depo.cli.defaults import _XDG_DATA_HOME, default_db_path, default_store_dir
from depo.util.errors import ConfigError, Severity


def _clear_depo_env(monkeypatch) -> None:
    for key in list(os.environ):
        if key.startswith("DEPO_"):
            monkeypatch.delenv(key)


def _set_depo_env(monkeypatch, **kwargs) -> None:
    """Set DEPO_* env vars from kwargs, names uppercased and prefixed.
    basically: setenv "DEPO_${kwargs:key}"="${kwargs[value]}" """
    for key, val in kwargs.items():
        monkeypatch.setenv(f"DEPO_{key.upper()}", str(val))


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
        assert default_store_dir() == tmp_path / "depo" / "store"

    def test_store_dir_fallback(self, monkeypatch):
        monkeypatch.delenv(_XDG_DATA_HOME, raising=False)
        assert default_store_dir() == Path.cwd() / "store"

    def test_db_path_xdg(self, monkeypatch, tmp_path):
        monkeypatch.setenv(_XDG_DATA_HOME, str(tmp_path))
        assert default_db_path() == tmp_path / "depo" / "depo.db"

    def test_db_path_fallback(self, monkeypatch):
        monkeypatch.delenv(_XDG_DATA_HOME, raising=False)
        assert default_db_path() == Path.cwd() / "depo.db"


class TestDepoConfig:
    """Tests for DepoConfig frozen dataclass."""

    @pytest.mark.parametrize(
        ("name", "typ", "required", "default"),
        [
            ("host", str, False, "127.0.0.1"),
            ("port", int, False, 8765),
            ("max_size_bytes", int, False, defaults.MAX_SIZE_BYTES),
            ("max_url_len", int, False, defaults.MAX_URL_LEN),
            ("min_code_len", int, False, defaults.MIN_CODE_LEN),
            ("log_level", Severity, False, Severity.WARNING),
            ("scrypt_n", int, False, defaults.SCRYPT_N),
            ("scrypt_r", int, False, defaults.SCRYPT_R),
            ("scrypt_p", int, False, defaults.SCRYPT_P),
            ("session_secret", str, False, defaults.SESSION_SECRET),
            ("session_https_only", bool, False, defaults.SESSION_HTTPS_ONLY),
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
        assert cfg.max_size_bytes == defaults.MAX_SIZE_BYTES
        assert cfg.max_url_len == defaults.MAX_URL_LEN


class TestCoerceBool:
    """Tests for the _coerce_bool helper function."""

    def test_native_bool_passthrough(self):
        """Native bools are returned unchanged."""
        assert _coerce_bool(True, "test") is True
        assert _coerce_bool(False, "test") is False

    @pytest.mark.parametrize("val", ["true", "True", "TRUE", "1", "yes", "on", "1", 1])
    def test_truthy_tokens(self, val):
        """Recognized truthy tokens coerce to True, case-insensitive."""
        assert _coerce_bool(val, "test") is True

    @pytest.mark.parametrize("token", ["false", "False", "FALSE", "no", "off", "0", 0])
    def test_falsy_tokens(self, token):
        """Recognized falsy tokens coerce to False, case-insensitive."""
        assert _coerce_bool(token, "test") is False

    @pytest.mark.parametrize("val", ["banana", "truth", 42, -1, 99])
    def test_invalid_raises(self, val):
        """An unrecognized token raises ConfigError naming the key and bad value."""
        with pytest.raises(ConfigError) as e:
            _coerce_bool(val, "some_field")
        assert e.value.key == "some_field"
        assert e.value.value == val


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
        assert cfg.max_size_bytes == defaults.MAX_SIZE_BYTES

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
        assert cfg.max_url_len == defaults.MAX_URL_LEN

    def test_toml_log_level(self, monkeypatch, tmp_path):
        """log_level resolves from a TOML config file."""
        _clear_depo_env(monkeypatch)
        _write_toml(tmp_path / "xdg/depo/config.toml", log_level="DEBUG")
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
        monkeypatch.chdir(tmp_path)
        assert load_config().log_level == Severity.DEBUG


class TestLoadConfigEnv:
    """Tests for DEPO_* environment variable overrides."""

    @pytest.fixture(autouse=True)
    def _isolate_env(self, monkeypatch, tmp_path):
        """Clear DEPO_* env.vars, point XDG_CONFIG_HOME to tmp_path and chdir to it"""
        _clear_depo_env(monkeypatch)
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        monkeypatch.chdir(tmp_path)

    def test_env_overrides_toml(self, monkeypatch, tmp_path):
        """Env.vars overrides any TOML config of respective config key-value pair"""
        _write_toml(tmp_path / "depo.toml", port=7000)
        _set_depo_env(monkeypatch, PORT="5555")
        assert load_config().port == 5555

    def test_env_host(self, monkeypatch):
        """DEPO_HOST env var overrides the default host."""
        _set_depo_env(monkeypatch, HOST="192.168.1.1")
        assert load_config().host == "192.168.1.1"

    def test_env_path_tilda_expansion(self, monkeypatch):
        """Path configs correctly coerces tildas to home path prefixes"""
        _set_depo_env(monkeypatch, db_path="~/test.db")
        assert load_config().db_path == Path.home() / "test.db"

    def test_env_int_coercion(self, monkeypatch):
        """Int values are correctly cast from string config values"""
        monkeypatch.setenv("DEPO_MAX_SIZE_BYTES", "5242880")
        assert load_config().max_size_bytes == 5_242_880

    def test_env_log_level(self, monkeypatch):
        """DEPO_LOG_LEVEL overrides the default log_level."""
        _set_depo_env(monkeypatch, log_level="DEBUG")
        assert load_config().log_level == Severity.DEBUG

    def test_env_log_level_case_insensitive(self, monkeypatch):
        """A lowercase DEPO_LOG_LEVEL still resolves to a Severity member."""
        _set_depo_env(monkeypatch, LOG_level="deBug")
        assert load_config().log_level == Severity.DEBUG

    def test_env_log_level_invalid_raises(self, monkeypatch):
        """An unknown DEPO_LOG_LEVEL raises ConfigError."""
        _set_depo_env(monkeypatch, log_level="BANANA")
        with pytest.raises(ConfigError) as e:
            load_config()
        assert e.value.key == "log_level"
        assert e.value.value == "BANANA"

    def test_env_scrypt_int_coercion(self, monkeypatch):
        """DEPO_SCRYPT_N/R/P env vars coerce to int on DepoConfig."""
        _set_depo_env(monkeypatch, SCRYPT_N=4096, SCRYPT_R=4, SCRYPT_P=2)
        config = load_config()
        assert config.scrypt_n == 4096
        assert config.scrypt_r == 4
        assert config.scrypt_p == 2

    def test_env_session_https_only_coerces(self, monkeypatch):
        """Bool env var coerces and lands correctly on config."""
        _set_depo_env(monkeypatch, SESSION_HTTPS_ONLY="yEs")
        assert load_config().session_https_only is True

    def test_env_session_https_only_invalid_propagates(self, monkeypatch):
        """Invalid bool env var propagates ConfigError through load_config."""
        _set_depo_env(monkeypatch, SESSION_HTTPS_ONLY="not_a_boolean")
        with pytest.raises(ConfigError):
            load_config()


class TestLoadConfigFlag:
    """Tests for config_path parameter (--config flag)."""

    def test_config_path_overrides_toml_chain(self, monkeypatch, tmp_path):
        _clear_depo_env(monkeypatch)
        _write_toml(tmp_path / "xdg/depo/config.toml", port=9000)
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
        monkeypatch.chdir(tmp_path)
        explicit = tmp_path / "custom.toml"
        _write_toml(explicit, port=1234)
        cfg = load_config(config_path=explicit)
        assert cfg.port == 1234

    def test_missing_config_path_raises(self, monkeypatch, tmp_path):
        _clear_depo_env(monkeypatch)
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "empty"))
        monkeypatch.chdir(tmp_path)
        with pytest.raises(FileNotFoundError):
            load_config(config_path=tmp_path / "nonexistent.toml")

    def test_env_layers_on_config_path(self, monkeypatch, tmp_path):
        _clear_depo_env(monkeypatch)
        explicit = tmp_path / "custom.toml"
        _write_toml(explicit, port=1234)
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "empty"))
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("DEPO_HOST", "10.0.0.5")
        cfg = load_config(config_path=explicit)
        assert cfg.port == 1234
        assert cfg.host == "10.0.0.5"
