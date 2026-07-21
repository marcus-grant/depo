# src/depo/cli/main.py
"""
CLI entry point using Click.

Author: Marcus Grant
Created: 2026-02-09
Revised: [2026-06-17]
License: Apache-2.0
"""

import sqlite3
import time
from dataclasses import fields

import click
from rich.console import Console
from rich.table import Table

from depo.cli.config import DepoConfig, load_config
from depo.model.user import User
from depo.repo.sqlite import SqliteRepository, check_migration_state, init_db
from depo.util.errors import SchemaVersionError, UniqueViolationError
from depo.util.password import hash_password
from depo.web.app import app_factory


@click.group()
@click.pass_context
def cli(ctx: click.Context) -> None:
    """depo — content-addressed paste/image service."""
    ctx.ensure_object(dict)
    if "config" not in ctx.obj:
        ctx.obj["config"] = load_config()


@cli.command()
@click.pass_context
def init(ctx: click.Context) -> None:
    """Initialize storage directories and database."""
    cfg: DepoConfig = ctx.obj["config"]
    cfg.db_path.parent.mkdir(parents=True, exist_ok=True)
    cfg.store_root.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(cfg.db_path))
    try:
        init_db(conn)
    finally:
        conn.close()


@cli.command()
@click.pass_context
def serve(ctx: click.Context) -> None:
    """Start the web server."""
    import uvicorn

    cfg: DepoConfig = ctx.obj["config"]
    if not cfg.db_path.exists():
        raise click.ClickException("database not initialized; run `depo init` first")
    conn = sqlite3.connect(str(cfg.db_path))
    try:
        check_migration_state(conn)
    except SchemaVersionError as e:
        raise click.ClickException(str(e)) from e
    finally:
        conn.close()
    app = app_factory(cfg)
    uvicorn.run(app, host=cfg.host, port=cfg.port)


@cli.group()
def config() -> None:
    """Configuration management."""


@config.command("show")
@click.pass_context
def config_show(ctx: click.Context) -> None:
    """Display resolved configuration."""
    cfg: DepoConfig = ctx.obj["config"]
    table = Table(title="Depo Configuration", show_header=False)
    table.add_column("Key", style="bold blue")
    table.add_column("Value")
    for f in fields(cfg):
        table.add_row(f.name, str(getattr(cfg, f.name)))
    console = Console()
    console.print(table)


@cli.command("create-user")
@click.option("--email", required=True, prompt=True)
@click.option("--name", required=True, prompt=True)
@click.password_option()
@click.pass_context
def create_user(ctx: click.Context, email: str, name: str, password: str) -> None:
    """Provision a new user with a hashed password."""
    cfg: DepoConfig = ctx.obj["config"]
    conn = sqlite3.connect(str(cfg.db_path))
    init_db(conn)
    repo = SqliteRepository(conn)
    kwargs = {"n": cfg.scrypt_n, "r": cfg.scrypt_r, "p": cfg.scrypt_p}
    pw_hash = hash_password(password, **kwargs)
    T = int(time.time())
    user = User(id=0, email=email, name=name, pw_hash=pw_hash, created_at=T)
    try:
        repo.insert_user(user)
        conn.commit()
    except UniqueViolationError as e:
        raise click.ClickException(f"{e.value} is already taken") from e
    finally:
        conn.close()


@cli.command("set-password")
@click.option("--target", required=True, prompt=True, help="Email or numeric user id.")
@click.password_option()
@click.pass_context
def set_password(ctx: click.Context, target: str, password: str) -> None:
    """Update an existing user's password."""
    cfg: DepoConfig = ctx.obj["config"]
    conn = sqlite3.connect(str(cfg.db_path))
    init_db(conn)
    repo = SqliteRepository(conn)
    try:
        if target.isdigit():
            uid = int(target)
        else:
            user = repo.get_user_by_email(target)
            if user is None:
                raise click.ClickException(f"No user found for {target}")
            uid = user.id
        kwargs = {"n": cfg.scrypt_n, "r": cfg.scrypt_r, "p": cfg.scrypt_p}
        pw_hash = hash_password(password, **kwargs)
        repo.update_user_pw_hash(uid, pw_hash)
        conn.commit()
    except click.ClickException:
        raise
    except Exception as e:
        raise click.ClickException(str(e)) from e
    finally:
        conn.close()
