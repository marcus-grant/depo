# tests/repo/test_sqlite.py
"""
Tests for SqliteRepository.
Author: Marcus Grant
Date: 2026-01-26
License: Apache-2.0
"""

import pytest
from tests.helpers.assertions import assert_column

from depo.repo.sqlite import init_db


class TestInitDb:
    """Tests for init_db()."""

    @pytest.mark.parametrize(
        "name, typ, notnull, default, pk",
        [
            ("hash_full", "TEXT", False, None, True),
            ("code", "TEXT", True, None, False),
            ("kind", "TEXT", True, None, False),
            ("size_b", "INTEGER", True, None, False),
            ("uid", "INTEGER", True, "0", False),
            ("perm", "TEXT", True, "'pub'", False),
            ("upload_at", "INTEGER", True, None, False),
            ("origin_at", "INTEGER", False, None, False),
        ],
    )
    def test_items_table_columns(self, test_db, name, typ, notnull, default, pk):
        """items table has correct column definitions."""
        assert_column(
            test_db, "items", name, typ, notnull=notnull, default=default, pk=pk
        )

    @pytest.mark.parametrize(
        ("name", "typ", "notnull", "default", "pk"),
        [
            ("hash_full", "TEXT", False, None, True),
            ("format", "TEXT", True, None, False),
        ],
    )
    def test_text_items_table_columns(self, test_db, name, typ, notnull, default, pk):
        """text_items table has correct column definitions."""
        assert_column(
            test_db, "text_items", name, typ, notnull=notnull, default=default, pk=pk
        )

    @pytest.mark.parametrize(
        ("name", "typ", "notnull", "default", "pk"),
        [
            ("hash_full", "TEXT", False, None, True),
            ("format", "TEXT", True, None, False),
            ("width", "INTEGER", True, None, False),
            ("height", "INTEGER", True, None, False),
        ],
    )
    def test_pic_items_table_columns(self, test_db, name, typ, notnull, default, pk):
        """pic_items table has correct column definitions."""
        assert_column(
            test_db, "pic_items", name, typ, notnull=notnull, default=default, pk=pk
        )

    @pytest.mark.parametrize(
        ("name", "typ", "notnull", "default", "pk"),
        [
            ("hash_full", "TEXT", False, None, True),
            ("url", "TEXT", True, None, False),
        ],
    )
    def test_link_items_table_columns(self, test_db, name, typ, notnull, default, pk):
        """link_items table has correct column definitions."""
        assert_column(
            test_db, "link_items", name, typ, notnull=notnull, default=default, pk=pk
        )

    @pytest.mark.parametrize(
        "index_name",
        [
            "idx_items_uid",
            "idx_items_kind",
            "idx_items_upload",
        ],
    )
    def test_creates_indexes(self, test_db, index_name):
        """init_db creates expected indexes."""
        cursor = test_db.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name=?",
            (index_name,),
        )
        assert cursor.fetchone() is not None, f"missing index: {index_name}"

    def test_idempotent(self, conn):
        """Calling init_db twice doesn't raise."""
        init_db(conn)
        init_db(conn)  # Should not raise
