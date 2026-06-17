# tests/cli/test_main.py
"""
Tests for CLI commands.

Author: Marcus Grant
Created: 2026-02-09
Revised [2026-06-17]
License: Apache-2.0
"""

from dataclasses import fields
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner
from tests.factories import make_config

from depo.cli.config import DepoConfig
from depo.cli.main import cli


def _invoke(*args, tmp_path: Path | None = None):
    cfg = make_config(tmp_path) if tmp_path else DepoConfig()
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
        assert make_config(tmp_path).db_path.is_file()

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
        assert str(make_config(tmp_path).host) in result.output
        assert str(make_config(tmp_path).port) in result.output
        assert str(make_config(tmp_path).max_size_bytes) in result.output
        assert str(make_config(tmp_path).max_url_len) in result.output

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

    def test_calls_uvicorn(self, tmp_path):
        with patch("uvicorn.run") as mock_run:
            result = _invoke("serve", tmp_path=tmp_path)
        assert result.exit_code == 0
        mock_run.assert_called_once()


@pytest.mark.skip(reason="create-user not implemented until final ft/credentials unit")
class TestCreateUser:
    """Gating e2e: create-user provisions a verifiable password hash."""

    def test_creates_user_with_verifying_hash(self, tmp_path):
        import sqlite3

        from depo.util.password import verify_password  # type: ignore[import]

        from depo.repo.sqlite import SqliteRepository, init_db

        pw = "s3cr3tpassword"
        cfg = make_config(tmp_path)
        runner = CliRunner()
        _invoke("init", tmp_path=tmp_path)
        result = runner.invoke(
            cli,
            ["create-user", "--email", "newuser@example.com", "--name", "NewUser"],
            obj={"config": cfg},
            input=f"{pw}\n{pw}\n",
            env={"COLUMNS": "300"},
        )
        assert result.exit_code == 0
        conn = sqlite3.connect(str(cfg.db_path))
        init_db(conn)
        repo = SqliteRepository(conn)
        user = repo.get_user_by_email("newuser@example.com")
        assert user is not None
        assert verify_password(pw, user.pw_hash)
        assert not verify_password("wrongpassword", user.pw_hash)
