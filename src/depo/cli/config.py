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
import tomllib
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
    port: int = 8765
    # Limits/thresholds
    max_size_bytes: int = 10_485_760
    max_url_len: int = 2048


def _xdg_config_home() -> Path:
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg)
    return Path.home() / ".config"


def _load_toml(path: Path) -> dict:
    if path.is_file():
        with open(path, "rb") as f:
            return tomllib.load(f)
    return {}


def _coerce(overrides: dict) -> dict:
    """Coerce string values from env/TOML to expected types."""
    int_fields = {"port", "max_size_bytes", "max_url_len"}
    path_fields = {"db_path", "store_root"}
    out = {}
    for k, v in overrides.items():
        if k in int_fields:
            out[k] = int(v)
        elif k in path_fields:
            out[k] = Path(v).expanduser()
        else:
            out[k] = v
    return out


def _env_overrides() -> dict:
    """Collect DEPO_* env vars, stripped of prefix and lowercased."""
    prefix = "DEPO_"
    out = {}
    for k, v in os.environ.items():
        if k.startswith(prefix):
            out[k[len(prefix) :].lower()] = v
    return out


def load_config(*, config_path: Path | None = None) -> DepoConfig:
    """
    Build DepoConfig from layered sources.

    Resolution:
        defaults → XDG config.toml → ./depo.toml → DEPO_* env → config_path flag.

    Args:
        config_path: Explicit TOML path (--config flag). Replaces XDG/local resolution.

    Returns:
        Resolved DepoConfig.

    Raises:
        FileNotFoundError: If config_path provided but missing.
    """
    overrides: dict = {}

    if config_path is not None:
        if not config_path.is_file():
            raise FileNotFoundError(config_path)
        overrides.update(_load_toml(config_path))
    else:
        # XDG config
        overrides.update(_load_toml(_xdg_config_home() / "depo" / "config.toml"))
        # Local ./depo.toml
        overrides.update(_load_toml(Path.cwd() / "depo.toml"))

    # Env vars layer on top of everything
    overrides.update(_env_overrides())

    return DepoConfig(**_coerce(overrides))
