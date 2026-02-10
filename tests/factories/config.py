# tests/factories/config.py
"""
DepoConfig test factory.

Builds DepoConfig instances with tmp_path-based
paths for test isolation.

Author: Marcus Grant
Created: 2026-02-09
License: Apache-2.0
"""

from pathlib import Path

from depo.cli.config import DepoConfig


def make_config(p: Path) -> DepoConfig:
    """Build a DepoConfig with paths under p."""
    return DepoConfig(db_path=p / "data" / "depo.db", store_root=p / "store")
