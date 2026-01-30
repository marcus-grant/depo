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
from depo.model.item import LinkItem, PicItem, TextItem
from depo.repo.sqlite import (
    SqliteRepository,
    _row_to_link_item,
    _row_to_pic_item,
    _row_to_text_item,
    init_db,
)


# Test helpers for populating the database
def _insert_text_item(
    conn,
    hash_full="ABC1234506789DEFGHKMNPQR",
    code="ABCD1234",
    size_b=99,
    uid=0,
    perm="pub",
    upload_at=123456789,
    origin_at=None,
    format="txt",
):
    conn.execute(
        "INSERT INTO items"
        "(hash_full, code, kind, size_b, uid, perm, upload_at, origin_at)"
        "VALUES (?, ?, 'txt', ?, ?, ?, ?, ?)",
        (hash_full, code, size_b, uid, perm, upload_at, origin_at),
    )
    conn.execute(
        "INSERT INTO text_items (hash_full, format) VALUES (?, ?)",
        (hash_full, format),
    )


def _insert_pic_item(
    conn,
    hash_full="ABC1234506789DEFGHKMNPQR",
    code="ABCD1234",
    size_b=99,
    uid=0,
    perm="pub",
    upload_at=123456789,
    origin_at=None,
    format="png",
    width=320,
    height=240,
):
    conn.execute(
        "INSERT INTO items"
        "(hash_full, code, kind, size_b, uid, perm, upload_at, origin_at)"
        "VALUES (?, ?, 'pic', ?, ?, ?, ?, ?)",
        (hash_full, code, size_b, uid, perm, upload_at, origin_at),
    )
    conn.execute(
        "INSERT INTO pic_items (hash_full, format, width, height) VALUES (?, ?, ?, ?)",
        (hash_full, format, width, height),
    )


def _insert_link_item(
    conn,
    hash_full="ABC1234506789DEFGHKMNPQR",
    code="ABCD1234",
    size_b=99,
    uid=0,
    perm="pub",
    upload_at=123456789,
    origin_at=None,
    url="https://example.com",
):
    conn.execute(
        "INSERT INTO items"
        "(hash_full, code, kind, size_b, uid, perm, upload_at, origin_at)"
        "VALUES (?, ?, 'url', ?, ?, ?, ?, ?)",
        (hash_full, code, size_b, uid, perm, upload_at, origin_at),
    )
    conn.execute(
        "INSERT INTO link_items (hash_full, url) VALUES (?, ?)",
        (hash_full, url),
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
        _insert_text_item(conn)
        init_db(conn)  # Should not raise
        row = conn.execute("SELECT * FROM items").fetchone()
        assert row is not None


class TestRowMappers:
    """Tests for row mapper functions."""

    def test_row_to_text_item(self, test_db):
        """Maps all fields from joined row to TextItem."""
        test_db.row_factory = sqlite3.Row
        _insert_text_item(test_db)
        row = test_db.execute(
            "SELECT i.*, t.format FROM items i"
            " JOIN text_items t ON i.hash_full = t.hash_full"
            " WHERE i.code = 'ABCD1234'"
        ).fetchone()

        result = _row_to_text_item(row)

        assert_item_base_fields(
            result,
            code="ABCD1234",
            hash_full="ABC1234506789DEFGHKMNPQR",
            kind=ItemKind.TEXT,
            size_b=99,
            uid=0,
            perm=Visibility.PUBLIC,
            upload_at=123456789,
            origin_at=None,
        )
        assert result.format == ContentFormat.PLAINTEXT

    def test_row_to_pic_item(self, test_db):
        """Maps all fields from joined row to PicItem."""
        _insert_pic_item(test_db)
        test_db.row_factory = sqlite3.Row
        row = test_db.execute(
            "SELECT i.*, p.format, p.width, p.height FROM items i"
            " JOIN pic_items p ON i.hash_full = p.hash_full"
            " WHERE i.code = 'ABCD1234'"
        ).fetchone()

        result = _row_to_pic_item(row)

        assert_item_base_fields(
            result,
            code="ABCD1234",
            hash_full="ABC1234506789DEFGHKMNPQR",
            kind=ItemKind.PICTURE,
            size_b=99,
            uid=0,
            perm=Visibility.PUBLIC,
            upload_at=123456789,
            origin_at=None,
        )
        assert result.format == ContentFormat.PNG
        assert result.width == 320
        assert result.height == 240

    def test_row_to_link_item(self, test_db):
        """Maps all fields from joined row to LinkItem."""
        _insert_link_item(test_db)
        test_db.row_factory = sqlite3.Row
        row = test_db.execute(
            "SELECT i.*, l.url FROM items i"
            " JOIN link_items l ON i.hash_full = l.hash_full"
            " WHERE i.code = 'ABCD1234'"
        ).fetchone()

        result = _row_to_link_item(row)

        assert_item_base_fields(
            result,
            code="ABCD1234",
            hash_full="ABC1234506789DEFGHKMNPQR",
            kind=ItemKind.LINK,
            size_b=99,
            uid=0,
            perm=Visibility.PUBLIC,
            upload_at=123456789,
            origin_at=None,
        )
        assert result.url == "https://example.com"


class TestGetByCode:
    """Tests for SqliteRepository.get_by_code()."""

    def test_none_for_code_not_exist(self, test_db):
        """Returns None for 'Item.code' that doesn't exist"""
        repo = SqliteRepository(test_db)
        assert repo.get_by_code("N0TF0VND") is None

    def test_text_item_for_text_item_code(self, test_db):
        """Returns correct TextItem for its 'code' column"""
        _insert_text_item(test_db)
        repo = SqliteRepository(test_db)
        result = repo.get_by_code("ABCD1234")
        assert isinstance(result, TextItem)
        assert result.code == "ABCD1234"

    def test_pic_item_for_pic_item_code(self, test_db):
        """Returns correct PicItem for its 'code' column"""
        _insert_pic_item(test_db)
        repo = SqliteRepository(test_db)
        result = repo.get_by_code("ABCD1234")
        assert isinstance(result, PicItem)
        assert result.code == "ABCD1234"

    def test_link_item_for_link_item_code(self, test_db):
        """Returns correct LinkItem for its 'code' column"""
        _insert_link_item(test_db)
        repo = SqliteRepository(test_db)
        result = repo.get_by_code("ABCD1234")
        assert isinstance(result, LinkItem)
        assert result.code == "ABCD1234"


class TestGetByFullHash:
    """Tests for SqliteRepository.get_by_full_hash()."""

    def test_none_for_hash_not_exist(self, test_db):
        """Returns None for nonexistent hash_full"""
        repo = SqliteRepository(test_db)
        assert repo.get_by_full_hash("0123456789ABCDEFGHJKMNPQ") is None

    def test_text_item_for_item_hash(self, test_db):
        """Returns correct TextItem for its 'hash_full' PK"""
        _insert_text_item(test_db)
        repo = SqliteRepository(test_db)
        result = repo.get_by_full_hash("ABC1234506789DEFGHKMNPQR")
        assert isinstance(result, TextItem)
        assert result.hash_full == "ABC1234506789DEFGHKMNPQR"

    def test_pic_item_for_item_hash(self, test_db):
        """Returns correct PicItem for its 'hash_full' PK"""
        _insert_pic_item(test_db)
        repo = SqliteRepository(test_db)
        result = repo.get_by_full_hash("ABC1234506789DEFGHKMNPQR")
        assert isinstance(result, PicItem)
        assert result.hash_full == "ABC1234506789DEFGHKMNPQR"

    def test_link_item_for_item_hash(self, test_db):
        """Returns correct LinkItem for its 'hash_full' PK"""
        _insert_link_item(test_db)
        repo = SqliteRepository(test_db)
        result = repo.get_by_full_hash("ABC1234506789DEFGHKMNPQR")
        assert isinstance(result, LinkItem)
        assert result.hash_full == "ABC1234506789DEFGHKMNPQR"


class TestResolveCode:
    """Tests for SqliteRepository.resolve_code()."""

    def test_min_len_prefix_when_no_collisions(self, test_db):
        """Returns min_len prefix when no collisions exist."""
        repo, hash_full = SqliteRepository(test_db), "01234567890ABCDEFGHJKMNP"
        assert repo.resolve_code(hash_full, min_len=8) == "01234567"

    def test_prefix_when_collision_exists(self, test_db):
        """Extends prefix when collision exists."""
        repo = SqliteRepository(test_db)
        _insert_text_item(
            test_db, hash_full="0123456700000000XXXXXXXX", code="01234567"
        )
        target_hash = "01234567890ABCDEFGHJKMNP"
        assert repo.resolve_code(target_hash, min_len=8) == "012345678"

    def test_extends_code_many_times_for_many_collisions(self, test_db):
        """Returns longer code when shorter prefixes collide"""
        repo = SqliteRepository(test_db)
        target_hash = "01234567890ABCDEFGHJKMNP"

        # Insert items with codes that collide with target's prefixes
        for i in range(8, 24):
            colliding_code = target_hash[:i]
            different_hash = f"XXXXXXXXXXXXXXXXXXXXXX{i:02d}"  # unique hash per item
            _insert_link_item(test_db, hash_full=different_hash, code=colliding_code)

        # All prefixes taken, should return full hash
        assert repo.resolve_code(target_hash, 8) == target_hash
