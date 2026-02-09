# src/depo/cli/main.py
"""
CLI entry point using Click.

Author: Marcus Grant
Created: 2026-02-09
License: Apache-2.0
"""

import click

from depo.cli.config import DepoConfig, load_config


@click.group()
def cli() -> None:
    """depo — content-addressed paste/image service."""


@cli.command()
def init() -> None:
    """Initialize storage directories and database."""
    raise NotImplementedError


@cli.command()
def serve() -> None:
    """Start the web server."""
    raise NotImplementedError


@cli.group()
def config() -> None:
    """Configuration management."""


@config.command("show")
def config_show() -> None:
    """Display resolved configuration."""
    raise NotImplementedError
