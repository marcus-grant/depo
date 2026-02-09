# src/depo/cli/main.py
"""
CLI entry point using Click.

Author: Marcus Grant
Created: 2026-02-09
License: Apache-2.0
"""

import sqlite3
from dataclasses import fields

import click
from rich.console import Console
from rich.table import Table

from depo.cli.config import DepoConfig, load_config
from depo.repo.sqlite import init_db


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
def serve() -> None:
    """Start the web server."""
    raise NotImplementedError


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
