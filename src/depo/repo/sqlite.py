# src/depo/repo/sqlite.py
"""
SQLite implementation of item repository.
Author: Marcus Grant
Date: 2026-01-26
License: Apache-2.0
"""

import sqlite3
from importlib import resources


def init_db(conn: sqlite3.Connection) -> None:
    """
    Apply schema to connection. Idempotent.

    Args:
        conn: SQLite connection to initialize.
    """
    schema = resources.files("depo.repo").joinpath("schema.sql").read_text()
    conn.executescript(schema)
