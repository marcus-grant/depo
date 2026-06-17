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

from depo.cli import defaults
from depo.util.errors import ConfigError, Severity


@dataclass(frozen=True, kw_only=True)
class DepoConfig:
    """Immutable application configuration."""

    # Paths / Dirs
    store_root: Path = field(default_factory=defaults.default_store_dir)
    db_path: Path = field(default_factory=defaults.default_db_path)
    # Network
    host: str = defaults.HOST
    port: int = defaults.PORT
    # Limits/thresholds
    max_size_bytes: int = defaults.MAX_SIZE_BYTES
    max_url_len: int = defaults.MAX_URL_LEN
    min_code_len: int = defaults.MIN_CODE_LEN
    # Logging/ErrorHandling
    log_level: Severity = defaults.LOG_LEVEL
    # Scrypt cost parameters
    scrypt_n: int = defaults.SCRYPT_N
    scrypt_r: int = defaults.SCRYPT_R
    scrypt_p: int = defaults.SCRYPT_P


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
    int_fields = {"port", "max_size_bytes", "max_url_len", "min_code_len"}
    int_fields |= {"scrypt_n", "scrypt_r", "scrypt_p"}
    path_fields = {"db_path", "store_root"}
    out = {}
    for k, v in overrides.items():
        if k in int_fields:
            out[k] = int(v)
        elif k in path_fields:
            out[k] = Path(v).expanduser()
        elif k == "log_level":  # Special case, needs to be a Severity enum member
            try:
                out[k] = Severity[str(v).upper()]
            except KeyError:
                err = ConfigError("log_level", v, expected=Severity.__members__)
                raise err from None
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
