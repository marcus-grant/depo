# tests/repo/test_sqlite.py
"""
Tests for SqliteRepository.
Author: Marcus Grant
Date: 2026-01-26
License: Apache-2.0
"""

import sqlite3

import pytest
from tests.helpers import assert_column, assert_item_base_fields

from depo.model.enums import ContentFormat, ItemKind, Visibility
from depo.repo.sqlite import (
    _row_to_link_item,
    _row_to_pic_item,
    _row_to_text_item,
    init_db,
)


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


class TestRowMappers:
    """Tests for row mapper functions."""

    def test_row_to_text_item(self, test_db):
        """Maps all fields from joined row to TextItem."""
        test_db.execute(
            "INSERT INTO items"
            " (hash_full, code, kind, size_b, uid, perm, upload_at, origin_at)"
            " VALUES ('ABC1234506789DEFGHKMNPQR', 'ABC12345', 'txt', 100, 1, 'pub',"
            " 1234567890, NULL)"
        )
        test_db.execute(
            "INSERT INTO text_items (hash_full, format)"
            " VALUES ('ABC1234506789DEFGHKMNPQR', 'txt')"
        )
        test_db.row_factory = sqlite3.Row
        row = test_db.execute(
            "SELECT i.*, t.format FROM items i"
            " JOIN text_items t ON i.hash_full = t.hash_full"
            " WHERE i.code = 'ABC12345'"
        ).fetchone()

        result = _row_to_text_item(row)

        assert_item_base_fields(
            result,
            code="ABC12345",
            hash_full="ABC1234506789DEFGHKMNPQR",
            kind=ItemKind.TEXT,
            size_b=100,
            uid=1,
            perm=Visibility.PUBLIC,
            upload_at=1234567890,
            origin_at=None,
        )
        assert result.format == ContentFormat.PLAINTEXT

    def test_row_to_pic_item(self, test_db):
        """Maps all fields from joined row to PicItem."""
        test_db.execute(
            "INSERT INTO items"
            " (hash_full, code, kind, size_b, uid, perm, upload_at, origin_at)"
            " VALUES ('ABC1234506789DEFGHKMNPQR', 'ABC12345', 'pic', 100, 1, 'pub',"
            " 1234567890, NULL)"
        )
        test_db.execute(
            "INSERT INTO pic_items (hash_full, format, width, height)"
            " VALUES ('ABC1234506789DEFGHKMNPQR', 'png', 320, 240)"
        )
        test_db.row_factory = sqlite3.Row
        row = test_db.execute(
            "SELECT i.*, p.format, p.width, p.height FROM items i"
            " JOIN pic_items p ON i.hash_full = p.hash_full"
            " WHERE i.code = 'ABC12345'"
        ).fetchone()

        result = _row_to_pic_item(row)

        assert_item_base_fields(
            result,
            code="ABC12345",
            hash_full="ABC1234506789DEFGHKMNPQR",
            kind=ItemKind.PICTURE,
            size_b=100,
            uid=1,
            perm=Visibility.PUBLIC,
            upload_at=1234567890,
            origin_at=None,
        )
        assert result.format == ContentFormat.PNG
        assert result.width == 320
        assert result.height == 240

    def test_row_to_link_item(self, test_db):
        """Maps all fields from joined row to LinkItem."""
        test_db.execute(
            "INSERT INTO items"
            " (hash_full, code, kind, size_b, uid, perm, upload_at, origin_at)"
            " VALUES ('ABC1234506789DEFGHKMNPQR', 'ABC12345', 'url', 100, 1, 'pub',"
            " 1234567890, NULL)"
        )
        test_db.execute(
            "INSERT INTO link_items (hash_full, url)"
            " VALUES ('ABC1234506789DEFGHKMNPQR', 'https://www.example.com')"
        )
        test_db.row_factory = sqlite3.Row
        row = test_db.execute(
            "SELECT i.*, l.url FROM items i"
            " JOIN link_items l ON i.hash_full = l.hash_full"
            " WHERE i.code = 'ABC12345'"
        ).fetchone()

        result = _row_to_link_item(row)

        assert_item_base_fields(
            result,
            code="ABC12345",
            hash_full="ABC1234506789DEFGHKMNPQR",
            kind=ItemKind.LINK,
            size_b=100,
            uid=1,
            perm=Visibility.PUBLIC,
            upload_at=1234567890,
            origin_at=None,
        )
        assert result.url == "https://www.example.com"
