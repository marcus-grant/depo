# tests/fixtures/db.py
"""
Database fixtures for repository testing.
Author: Marcus Grant
Date: 2026-01-26
License: Apache-2.0
"""

import sqlite3
from collections.abc import Generator

import pytest

from depo.repo.sqlite import init_db


@pytest.fixture
def test_db() -> Generator[sqlite3.Connection, None, None]:
    """In-memory SQLite database with schema initialized."""
    conn = sqlite3.connect(":memory:")
    init_db(conn)
    yield conn
    conn.close()
