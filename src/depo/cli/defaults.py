# src/depo/cli/defaults.py
"""
Default value production for DepoConfig.
Scalar defaults and path-discovery helpers, kept apart from
config.py's structuring and override-resolution logic.
Author: Marcus Grant
Created: 2026-06-04
License: Apache-2.0
"""

import os
from pathlib import Path

from depo.util.errors import Severity

HOST = "127.0.0.1"
PORT = 8765
MAX_SIZE_BYTES = 2**26
MAX_URL_LEN = 2048
MIN_CODE_LEN = 8
LOG_LEVEL = Severity.WARNING

_XDG_DATA_HOME = "XDG_DATA_HOME"

# SCRYPT crypto params

SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1


def default_store_dir() -> Path:
    """Return XDG_DATA_HOME/depo/store if set, else ./store for containerized deploys"""
    if xdg := os.environ.get(_XDG_DATA_HOME):
        return Path(xdg) / "depo" / "store"
    return Path.cwd() / "store"


def default_db_path() -> Path:
    """Return default database path. XDG_DATA_HOME/depo/depo.db or ./depo.db."""
    if xdg := os.environ.get(_XDG_DATA_HOME):
        return Path(xdg) / "depo" / "depo.db"
    return Path.cwd() / "depo.db"
