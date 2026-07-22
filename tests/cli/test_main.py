# tests/cli/test_main.py
"""
Tests for CLI commands.

Author: Marcus Grant
Created: 2026-02-09
Revised [2026-06-17]
License: Apache-2.0
"""

import sqlite3
from dataclasses import fields
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner
from tests.factories import make_config

from depo.cli.config import DepoConfig
from depo.cli.main import cli
from depo.repo.sqlite import SqliteRepository, init_db
from depo.util.password import verify_password


def _invoke(*args, tmp_path: Path | None = None):
    cfg = make_config(tmp_path) if tmp_path else DepoConfig()
    runner = CliRunner()
    return runner.invoke(cli, list(args), obj={"config": cfg}, env={"COLUMNS": "300"})  # type: ignore


def _invoke_create_user(tmppath: Path, email: str, name: str, password: str):
    runner = CliRunner()
    return runner.invoke(
        cli,
        ["create-user", "--email", email, "--name", name],
        obj={"config": make_config(tmppath)},
        input=f"{password}\n{password}\n",
        env={"COLUMNS": "300"},
    )


def _invoke_set_password(tmp_path, target: str, password: str):
    runner = CliRunner()
    return runner.invoke(
        cli,
        ["set-password", "--target", target],
        obj={"config": make_config(tmp_path)},
        input=f"{password}\n{password}\n",
        env={"COLUMNS": "300"},
    )


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


class TestServeGuard:
    """Tests for serve's migration-state gate."""

    def test_aborts_when_db_uninitialized(self, tmp_path, monkeypatch):
        """serve exits non-zero with guidance when the store is absent."""
        monkeypatch.setattr("uvicorn.run", lambda *a, **k: None)
        result = _invoke("serve", tmp_path=tmp_path)
        assert result.exit_code != 0
        assert "init" in result.output.lower()

    def test_aborts_when_schema_unsafe(self, tmp_path, monkeypatch):
        """serve exits non-zero when the store schema is unsafe."""
        _invoke("init", tmp_path=tmp_path)
        monkeypatch.setattr("depo.repo.sqlite.available_migrations", lambda: ["9.9.9"])
        monkeypatch.setattr("uvicorn.run", lambda *a, **k: None)
        result = _invoke("serve", tmp_path=tmp_path)
        assert result.exit_code != 0


class TestServe:
    """Tests for `depo serve`."""

    def test_calls_uvicorn(self, tmp_path):
        _invoke("init", tmp_path=tmp_path)  # Needs an initialized database first
        with patch("uvicorn.run") as mock_run:
            result = _invoke("serve", tmp_path=tmp_path)
        assert result.exit_code == 0
        mock_run.assert_called_once()


class TestCreateUser:
    """Gating e2e: create-user provisions a verifiable password hash."""

    def test_creates_user_with_verifying_hash(self, tmp_path):
        pw = "s3cr3tpassword"
        cfg = make_config(tmp_path)
        runner = CliRunner()
        _invoke("init", tmp_path=tmp_path)
        args = ["create-user", "--email", "newuser@example.com", "--name", "NewUser"]
        result = runner.invoke(
            cli,
            args,
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

    def test_duplicate_email_errors(self, tmp_path):
        """Errors cleanly when a user with the same email already exists."""
        _invoke("init", tmp_path=tmp_path)
        _invoke_create_user(tmp_path, "dupe@example.com", "UserOne", "password")
        args = tmp_path, "dupe@example.com", "UserTwo", "password"
        result = _invoke_create_user(*args)
        assert result.exit_code != 0
        assert "dupe@example.com" in result.output

    def test_duplicate_name_errors(self, tmp_path):
        """Errors cleanly when a user with the same name already exists."""
        _invoke("init", tmp_path=tmp_path)
        args = (tmp_path, "user1@example.com", "SharedName", "password")
        _invoke_create_user(*args)
        args = tmp_path, "user2@example.com", "SharedName", "password"
        result = _invoke_create_user(*args)
        assert result.exit_code != 0
        assert "SharedName" in result.output

    def test_password_not_echoed(self, tmp_path):
        """Password input is not echoed to output."""
        _invoke("init", tmp_path=tmp_path)
        args = tmp_path, "user@example.com", "User", "s3cr3tpassword"
        result = _invoke_create_user(*args)
        assert "s3cr3tpassword" not in result.output


class TestSetPassword:
    """Tests for the set-password admin command."""

    def test_changes_password_by_email(self, tmp_path):
        """New password verifies; old password no longer does."""
        _invoke("init", tmp_path=tmp_path)
        args = (tmp_path, "user@example.com", "User", "oldpassword")
        _invoke_create_user(*args)
        _invoke_set_password(tmp_path, "user@example.com", "newpassword")
        conn = sqlite3.connect(str(make_config(tmp_path).db_path))
        init_db(conn)
        user = SqliteRepository(conn).get_user_by_email("user@example.com")
        assert user is not None
        assert verify_password("newpassword", user.pw_hash)
        assert not verify_password("oldpassword", user.pw_hash)

    def test_changes_password_by_id(self, tmp_path):
        """Accepts a numeric user id in place of email."""
        _invoke("init", tmp_path=tmp_path)
        _invoke_create_user(tmp_path, "user@example.com", "User", "oldpassword")
        conn = sqlite3.connect(str(make_config(tmp_path).db_path))
        init_db(conn)
        user = SqliteRepository(conn).get_user_by_email("user@example.com")
        assert user is not None
        conn.close()
        _invoke_set_password(tmp_path, str(user.id), "newpassword")
        conn = sqlite3.connect(str(make_config(tmp_path).db_path))
        init_db(conn)
        user = SqliteRepository(conn).get_user_by_email("user@example.com")
        assert user is not None
        assert verify_password("newpassword", user.pw_hash)

    def test_errors_on_unknown_user(self, tmp_path):
        """Errors cleanly when the target user does not exist."""
        _invoke("init", tmp_path=tmp_path)
        result = _invoke_set_password(tmp_path, "ghost@example.com", "password")
        assert result.exit_code != 0

    def test_password_not_echoed(self, tmp_path):
        """New password input is not echoed to output."""
        _invoke("init", tmp_path=tmp_path)
        _invoke_create_user(tmp_path, "user@example.com", "User", "oldpassword")
        result = _invoke_set_password(tmp_path, "user@example.com", "s3cr3tnew")
        assert "s3cr3tnew" not in result.output
