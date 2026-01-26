# tests/repo/test_sqlite.py
"""
Tests for SqliteRepository.
Author: Marcus Grant
Date: 2026-01-26
License: Apache-2.0
"""

import sqlite3

import pytest

from depo.repo.sqlite import init_db


class TestInitDb:
    """Tests for init_db()."""

    def test_creates_items_table_and_cols(self, test_db: sqlite3.Connection):
        """Creates items table with expected columns"""
        ...

    # Creates text_items table with expected columns
    # Creates pic_items table with expected columns
    # Creates link_items table with expected columns
    # Creates expected indexes (idx_items_uid, idx_items_kind, idx_items_upload)
    # Is idempotent (calling twice doesn't raise)
