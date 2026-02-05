# tests/repo/test_sqlite.py
"""
Tests for SqliteRepository.
Author: Marcus Grant
Date: 2026-01-26
License: Apache-2.0
"""

import sqlite3

import pytest
from tests.factories.models import make_write_plan
from tests.helpers import assert_column, assert_item_base_fields

from depo.model.enums import ContentFormat, ItemKind, Visibility
from depo.model.item import LinkItem, PicItem, TextItem
from depo.repo.errors import CodeCollisionError
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
    def test_items_table_columns(self, t_db, name, typ, notnull, default, pk):
        """items table has correct column definitions."""
        assert_column(t_db, "items", name, typ, notnull=notnull, default=default, pk=pk)

    @pytest.mark.parametrize(
        ("name", "typ", "notnull", "default", "pk"),
        [
            ("hash_full", "TEXT", False, None, True),
            ("format", "TEXT", True, None, False),
        ],
    )
    def test_text_items_table_columns(self, t_db, name, typ, notnull, default, pk):
        """text_items table has correct column definitions."""
        args = (t_db, "text_items", name, typ)
        assert_column(*args, notnull=notnull, default=default, pk=pk)

    @pytest.mark.parametrize(
        ("name", "typ", "notnull", "default", "pk"),
        [
            ("hash_full", "TEXT", False, None, True),
            ("format", "TEXT", True, None, False),
            ("width", "INTEGER", True, None, False),
            ("height", "INTEGER", True, None, False),
        ],
    )
    def test_pic_items_table_columns(self, t_db, name, typ, notnull, default, pk):
        """pic_items table has correct column definitions."""
        args = (t_db, "pic_items", name, typ)
        assert_column(*args, notnull=notnull, default=default, pk=pk)

    @pytest.mark.parametrize(
        ("name", "typ", "notnull", "default", "pk"),
        [
            ("hash_full", "TEXT", False, None, True),
            ("url", "TEXT", True, None, False),
        ],
    )
    def test_link_items_table_columns(self, t_db, name, typ, notnull, default, pk):
        """link_items table has correct column definitions."""
        args = (t_db, "link_items", name, typ)
        assert_column(*args, notnull=notnull, default=default, pk=pk)

    @pytest.mark.parametrize(
        "index_name",
        [
            "idx_items_uid",
            "idx_items_kind",
            "idx_items_upload",
        ],
    )
    def test_creates_indexes(self, t_db, index_name):
        """init_db creates expected indexes."""
        q = "SELECT name FROM sqlite_master WHERE type='index' AND name=?"
        msg = f"missing index: {index_name}"
        assert t_db.execute(q, (index_name,)).fetchone() is not None, msg

    def test_idempotent(self, t_conn):
        """Calling init_db twice doesn't raise."""
        init_db(t_conn)
        _insert_text_item(t_conn)
        init_db(t_conn)  # Should not raise
        row = t_conn.execute("SELECT * FROM items").fetchone()
        assert row is not None

    def test_foreign_keys_enabled(self, t_db):
        """FK constraints are enabled after init."""
        assert t_db.execute("PRAGMA foreign_keys").fetchone()[0] == 1


class TestRowMappers:
    """Tests for row mapper functions."""

    def test_row_to_text_item(self, t_db):
        """Maps all fields from joined row to TextItem."""
        # Assemble row factory & test row in items and text_items
        _insert_text_item(t_db)
        t_db.row_factory = sqlite3.Row
        row = t_db.execute(
            "SELECT i.*, t.format FROM items i"
            " JOIN text_items t ON i.hash_full = t.hash_full"
            " WHERE i.code = 'ABCD1234'"
        ).fetchone()

        # Act on row mapper
        result = _row_to_text_item(row)

        # Assert Item fields
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
        )  # Assert TextItem specific fields
        assert result.format == ContentFormat.PLAINTEXT

    def test_row_to_pic_item(self, t_db):
        """Maps all fields from joined row to PicItem."""
        _insert_pic_item(t_db)  # Assemble
        t_db.row_factory = sqlite3.Row
        row = t_db.execute(
            "SELECT i.*, p.format, p.width, p.height FROM items i"
            " JOIN pic_items p ON i.hash_full = p.hash_full"
            " WHERE i.code = 'ABCD1234'"
        ).fetchone()

        result = _row_to_pic_item(row)  # Act

        assert_item_base_fields(  # Assert
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

    def test_row_to_link_item(self, t_db):
        """Maps all fields from joined row to LinkItem."""
        _insert_link_item(t_db)
        t_db.row_factory = sqlite3.Row
        row = t_db.execute(
            "SELECT i.*, l.url FROM items i"
            " JOIN link_items l ON i.hash_full = l.hash_full"
            " WHERE i.code = 'ABCD1234'"
        ).fetchone()  # Assemble

        result = _row_to_link_item(row)  # Act

        assert_item_base_fields(  # Assert
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

    def test_none_for_code_not_exist(self, t_repo):
        """Returns None for 'Item.code' that doesn't exist"""
        assert t_repo.get_by_code("N0TF0VND") is None

    def test_text_item_for_text_item_code(self, t_repo):
        """Returns correct TextItem for its 'code' column"""
        _insert_text_item(t_repo._conn)  # Assemble text_item record
        result = t_repo.get_by_code("ABCD1234")  # Act with get
        assert isinstance(result, TextItem)  # Assert it's a TextItem
        assert result.code == "ABCD1234"  # Assert it's the same code

    def test_pic_item_for_pic_item_code(self, t_repo):
        """Returns correct PicItem for its 'code' column"""
        _insert_pic_item(t_repo._conn)  # Assemble
        result = t_repo.get_by_code("ABCD1234")  # Act
        assert isinstance(result, PicItem)  # Assert
        assert result.code == "ABCD1234"

    def test_link_item_for_link_item_code(self, t_repo):
        """Returns correct LinkItem for its 'code' column"""
        _insert_link_item(t_repo._conn)  # Assemble
        result = t_repo.get_by_code("ABCD1234")  # Act
        assert isinstance(result, LinkItem)  # Assert
        assert result.code == "ABCD1234"


class TestGetByFullHash:
    """Tests for SqliteRepository.get_by_full_hash()."""

    def test_none_for_hash_not_exist(self, t_repo):
        """Returns None for nonexistent hash_full"""
        repo = SqliteRepository(t_repo._conn)
        assert repo.get_by_full_hash("0123456789ABCDEFGHJKMNPQ") is None

    def test_text_item_for_item_hash(self, t_repo):
        """Returns correct TextItem for its 'hash_full' PK"""
        _insert_text_item(t_repo._conn)
        result = t_repo.get_by_full_hash("ABC1234506789DEFGHKMNPQR")
        assert isinstance(result, TextItem)
        assert result.hash_full == "ABC1234506789DEFGHKMNPQR"

    def test_pic_item_for_item_hash(self, t_repo):
        """Returns correct PicItem for its 'hash_full' PK"""
        _insert_pic_item(t_repo._conn)
        result = t_repo.get_by_full_hash("ABC1234506789DEFGHKMNPQR")
        assert isinstance(result, PicItem)
        assert result.hash_full == "ABC1234506789DEFGHKMNPQR"

    def test_link_item_for_item_hash(self, t_repo):
        """Returns correct LinkItem for its 'hash_full' PK"""
        _insert_link_item(t_repo._conn)
        result = t_repo.get_by_full_hash("ABC1234506789DEFGHKMNPQR")
        assert isinstance(result, LinkItem)
        assert result.hash_full == "ABC1234506789DEFGHKMNPQR"


class TestResolveCode:
    """Tests for SqliteRepository.resolve_code()."""

    def test_min_len_prefix_when_no_collisions(self, t_repo):
        """Returns min_len prefix when no collisions exist."""
        assert t_repo.resolve_code("01234567890ABCDEFGHJKMNP", min_len=8) == "01234567"

    def test_prefix_when_collision_exists(self, t_repo):
        """Extends prefix code length by 1 when 1 colliding prefix exists."""
        prefix, min_len = "01234567", 8
        hash1, hash2 = f"{prefix}00000000XXXXXXXX", f"{prefix}890ABCDEFGHJKMNP"
        _insert_text_item(t_repo._conn, hash_full=hash1, code=prefix)
        assert t_repo.resolve_code(hash2, min_len=min_len) == prefix + hash2[min_len]

    def test_extends_code_many_times_for_many_collisions(self, t_repo):
        """Returns longer code when shorter prefixes collide"""
        # Insert items with codes that collide with target's prefixes
        target_hash = "01234567890ABCDEFGHJKMNP"
        for i in range(8, 24):
            hash_uniq = f"XXXXXXXXXXXXXXXXXXXXXX{i:02d}"  # unique hash per item
            code_colide = target_hash[:i]  # Coliding code is one longer than previous
            _insert_link_item(t_repo._conn, hash_full=hash_uniq, code=code_colide)
        # All prefixes taken, should return full hash
        assert t_repo.resolve_code(target_hash, 8) == target_hash


class TestInsert:
    """Tests for SqliteRepository.insert()."""

    def test_inserts_text_item(self, t_repo):
        """Inserts TextItem and returns it"""
        plan = make_write_plan(format="md")  # Assemble WritePlan to Insert with
        result = t_repo.insert(plan, uid=69, perm=Visibility.PRIVATE)  # Act
        assert isinstance(result, TextItem)  # Assert correct results
        assert result.code == plan.hash_full[: plan.code_min_len]
        assert result.size_b == plan.size_b
        assert result.upload_at == plan.upload_at
        assert result.uid == 69
        assert result.perm == Visibility.PRIVATE
        assert result.format == ContentFormat.MARKDOWN
        assert result == t_repo.get_by_full_hash(plan.hash_full)

    def test_inserts_pic_item(self, t_repo):
        """Inserts PicItem and returns it"""
        plan = make_write_plan(  # Assemble
            kind=ItemKind.PICTURE,
            format="jpg",
            width=800,
            height=600,
        )
        result = t_repo.insert(plan)  # Act
        assert isinstance(result, PicItem)  # Assert
        assert result.code == plan.hash_full[: plan.code_min_len]
        assert result.size_b == plan.size_b
        assert result.upload_at == plan.upload_at
        assert result.origin_at == plan.origin_at
        assert result.uid == 0
        assert result.perm == Visibility.PUBLIC
        assert result.format == ContentFormat.JPEG
        assert result.width == 800
        assert result.height == 600
        assert result == t_repo.get_by_full_hash(plan.hash_full)

    def test_inserts_link_item(self, t_repo):
        """Inserts LinkItem and returns it"""
        kwargs = {"kind": ItemKind.LINK, "link_url": "https://depo.example.com"}
        plan = make_write_plan(**kwargs)
        result = t_repo.insert(plan, uid=42, perm=Visibility.UNLISTED)
        assert isinstance(result, LinkItem)
        assert result.code == plan.hash_full[: plan.code_min_len]
        assert result.size_b == plan.size_b
        assert result.upload_at == plan.upload_at
        assert result.uid == 42
        assert result.perm == Visibility.UNLISTED
        assert result.url == "https://depo.example.com"
        assert result == t_repo.get_by_full_hash(plan.hash_full)

    def test_raises_code_collision_error_on_duplicate_hash(self, t_repo):
        """Raises CodeCollisionError when same content inserted twice (dedupe leak)"""
        plan1 = make_write_plan(code_min_len=8, kind="url", link_url="http://a.com")
        plan2 = make_write_plan(code_min_len=8, kind="url", link_url="http://a.com")
        t_repo.insert(plan1)
        with pytest.raises(CodeCollisionError):
            t_repo.insert(plan2)

    def test_resolve_prevents_code_collision(self, t_repo):
        """resolve_code extends to avoid collision"""
        prefix = "ABCD1234"
        _insert_link_item(t_repo._conn, hash_full=("X" * 24), code=prefix)
        plan = make_write_plan(
            hash_full=f"{prefix}XXXXXXXXXXXXXXXX",  # Same 8-char prefix
            code_min_len=8,
            kind=ItemKind.LINK,
            link_url="http://test.com",
        )  # Extends to 9 chars, no collision vvv
        assert t_repo.insert(plan).code == prefix + "X"


class TestDelete:
    """Tests for SqliteRepository.delete()."""

    def test_delete_cascades_to_subtype(self, t_repo):
        """Deleting item removes row from items and correct subtype table."""
        con, hash_suffix = t_repo._conn, "0123456789ABCDEFGHJKMNP"  # 23 char suffix
        _insert_text_item(con, hash_full=f"T{hash_suffix}", code="TXTC0DE1")
        _insert_pic_item(con, hash_full=f"P{hash_suffix}", code="PICC0DE1")
        _insert_link_item(con, hash_full=f"L{hash_suffix}", code="URLC0DE1")

        def count(t):
            return con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]

        def assert_counts(n_items, n_text, n_pic, n_link):
            # Assert items & subtype tables have expected counts
            assert count("items") == n_items
            assert count("text_items") == n_text
            assert count("pic_items") == n_pic
            assert count("link_items") == n_link

        assert_counts(3, 1, 1, 1)  # Starting counts before deletions
        t_repo.delete("T0123456789ABCDEFGHJKMNP")
        assert_counts(2, 0, 1, 1)  # One less item, one less text item
        t_repo.delete("P0123456789ABCDEFGHJKMNP")
        assert_counts(1, 0, 0, 1)  # One less item, one less pic item
        t_repo.delete("L0123456789ABCDEFGHJKMNP")
        assert_counts(0, 0, 0, 0)  # Nothing left

    def test_delete_nonexistent_is_noop(self, t_repo):
        """Deleting nonexistent hash doesn't raise."""
        t_repo.delete("DOESNOTEXIST12345678")
