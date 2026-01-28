# tests/conftest.py
"""Pytest configuration and fixture loading."""

import sqlite3

import pytest

pytest_plugins = [
    "tests.fixtures.db",
]


@pytest.fixture
def conn():
    """Raw in-memory SQLite connection (no schema)."""
    c = sqlite3.connect(":memory:")
    yield c
    c.close()
