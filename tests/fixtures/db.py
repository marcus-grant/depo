# tests/fixtures/db.py
"""
Database fixtures for repository testing.
Author: Marcus Grant
Date: 2026-01-26
License: Apache-2.0
"""

import pytest


@pytest.fixture
def test_db():
    """In-memory SQLite database with schema initialized."""
    # TODO: Implement schema creation in PR 2 (repo read path)
    raise NotImplementedError("test_db fixture not yet implemented")
