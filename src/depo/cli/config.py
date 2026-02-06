# src/depo/cli/config.py
"""
Application configuration.

Frozen dataclass with layered resolution:
defaults → XDG config.toml → ./depo.toml → DEPO_* env → --config flag.

Author: Marcus Grant
Created: 2026-02-06
License: Apache-2.0
"""

import os
from dataclasses import dataclass, field
from pathlib import Path

_XDG_DATA_HOME = "XDG_DATA_HOME"


def _default_store_dir() -> Path:
    """Return XDG_DATA_HOME/depo if set, else ./store for containerized deploys."""
    if xdg := os.environ.get(_XDG_DATA_HOME):
        return Path(xdg) / "depo" / "store"
    return Path.cwd() / "store"


def _default_db_path() -> Path:
    """Return default database path. XDG_DATA_HOME/depo/depo.db or ./depo.db."""
    if xdg := os.environ.get(_XDG_DATA_HOME):
        return Path(xdg) / "depo" / "depo.db"
    return Path.cwd() / "depo.db"


@dataclass(frozen=True, kw_only=True)
class DepoConfig:
    """Immutable application configuration."""

    # Paths / Dirs
    store_root: Path = field(default_factory=_default_store_dir)
    db_path: Path = field(default_factory=_default_db_path)
    # Network
    host: str = "127.0.0.1"
    port: int = 8000
    # Payload limits
    max_size_bytes: int = 10_485_760
    max_url_len: int = 2048
