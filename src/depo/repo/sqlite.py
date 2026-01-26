# src/depo/repo/sqlite.py
"""
SQLite implementation of item repository.
Author: Marcus Grant
Date: 2026-01-26
License: Apache-2.0
"""

from importlib import resources
import sqlite3


def init_db(conn: sqlite3.Connection) -> None:
    """
    Apply schema to connection. Idempotent.

    Args:
        conn: SQLite connection to initialize.
    """
    raise NotImplementedError
