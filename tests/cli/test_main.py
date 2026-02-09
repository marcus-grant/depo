# tests/cli/test_main.py
"""
Tests for CLI commands.

Author: Marcus Grant
Created: 2026-02-09
License: Apache-2.0
"""

from dataclasses import fields
from pathlib import Path

from click.testing import CliRunner

from depo.cli.config import DepoConfig
from depo.cli.main import cli


# TODO: Should this be a fixture?
def _depo_cfg(p: Path) -> DepoConfig:
    return DepoConfig(db_path=p / "data" / "depo.db", store_root=p / "store")


def _invoke(*args, tmp_path: Path | None = None):
    cfg = _depo_cfg(tmp_path) if tmp_path else DepoConfig()
    runner = CliRunner()
    return runner.invoke(cli, list(args), obj={"config": cfg}, env={"COLUMNS": "300"})  # type: ignore


class TestInit:
    """Tests for `depo init`."""

    def test_creates_directories(self, tmp_path):
        result = _invoke("init", tmp_path=tmp_path)
        assert result.exit_code == 0
        assert (tmp_path / "data").is_dir()
        assert (tmp_path / "store").is_dir()

    def test_creates_database(self, tmp_path):
        _invoke("init", tmp_path=tmp_path)
        assert _depo_cfg(tmp_path).db_path.is_file()

    def test_idempotent(self, tmp_path):
        _invoke("init", tmp_path=tmp_path)
        result = _invoke("init", tmp_path=tmp_path)
        assert result.exit_code == 0


class TestConfigShow:
    """Tests for `depo config show`."""

    def test_prints_all_cfg_fields(self, tmp_path):
        """Prints all expected config fields & shows exit code 0"""
        result = _invoke("config", "show", tmp_path=tmp_path)
        assert result.exit_code == 0
        assert "store" in result.output
        assert "depo.db" in result.output
        assert str(_depo_cfg(tmp_path).host) in result.output
        assert str(_depo_cfg(tmp_path).port) in result.output
        assert str(_depo_cfg(tmp_path).max_size_bytes) in result.output
        assert str(_depo_cfg(tmp_path).max_url_len) in result.output

    def test_shows_all_expected_fields(self, tmp_path):
        """Tests gaps in coverage for new/different DepoConfig fields"""
        result = _invoke("config", "show", tmp_path=tmp_path)
        for f in fields(DepoConfig):
            assert f.name in result.output

    def test_reflects_overrides(self):
        """Shows overridden values, not defaults."""
        cfg = DepoConfig(host="10.0.0.1", port=3000)
        runner = CliRunner()
        result = runner.invoke(  # Doesnt use _invoke to modify config overrides
            cli, ["config", "show"], obj={"config": cfg}, env={"COLUMNS": "300"}
        )
        assert "10.0.0.1" in result.output
        assert "3000" in result.output


class TestServe:
    """Tests for `depo serve`."""

    def test_placeholder(self, tmp_path):
        result = _invoke("serve", tmp_path=tmp_path)
        assert result.exit_code == 0
        assert "not implemented" in result.output.lower()
