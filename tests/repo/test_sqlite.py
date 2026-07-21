# tests/repo/test_sqlite.py
"""
Tests for SqliteRepository.
Author: Marcus Grant
Date: 2026-01-26
Revisions: [2026-06-16]
License: Apache-2.0
"""

import re
import sqlite3
from pathlib import Path

import pytest
from packaging.version import InvalidVersion

from depo.model.enums import ContentFormat, ItemKind, Visibility
from depo.model.item import LinkItem, PicItem, TextItem
from depo.model.user import User
from depo.repo.schema import SCHEMA_VERSION
from depo.repo.sqlite import (
    SqliteRepository,
    _migration_version,
    _row_to_link_item,
    _row_to_pic_item,
    _row_to_text_item,
    init_db,
    list_migrations,
    pending_migrations,
)
from depo.util import errors
from tests.factories.db import (
    insert_link_item,
    insert_pic_item,
    insert_text_item,
    insert_user,
)
from tests.factories.models import make_user, make_write_plan
from tests.helpers import assert_column


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
        insert_text_item(t_conn)
        init_db(t_conn)  # Should not raise
        row = t_conn.execute("SELECT * FROM items").fetchone()
        assert row is not None

    def test_foreign_keys_enabled(self, t_db):
        """FK constraints are enabled after init."""
        assert t_db.execute("PRAGMA foreign_keys").fetchone()[0] == 1

    def test_wal_journal_mode(self, tmp_path):
        """WAL journal mode is active after init."""
        with sqlite3.connect(tmp_path / "test.db") as cn:
            init_db(cn)
            assert cn.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"

    def test_busy_timeout_set(self, t_db):
        """Busy timeout is non-zero after init."""
        assert t_db.execute("PRAGMA busy_timeout").fetchone()[0] > 0

    def test_superuser_row_seeded(self, t_db):
        """Superuser row with id=0 exists in users after init."""
        q = "SELECT * FROM users WHERE id = 0;"
        assert t_db.execute(q).fetchone() is not None

    def test_items_uid_fk_enforced(self, t_db):
        """items.uid foreign key rejects unknown uid."""
        q = "INSERT INTO items (hash_full, code, kind, size_b, uid, upload_at) "
        q += "VALUES ('AAAABBBBCCCCDDDDEEEEFFFGG', 'AAAAB', 'txt', 100, 9999, 0)"
        with pytest.raises(sqlite3.IntegrityError):
            t_db.execute(q)

    def test_init_db_safe_after_open_transaction(self, t_conn):
        """init_db succeeds when called with an open implicit transaction."""
        init_db(t_conn)
        q = "INSERT INTO users (id, email, name, pw_hash, created_at) "
        q += "VALUES (1, 'a@b.com', 'Test', 'x', 0)"
        t_conn.execute(q)
        init_db(t_conn)

    def test_creates_repo_meta_table(self, t_conn):
        """init_db creates the repo_meta table."""
        init_db(t_conn)
        q = "SELECT name FROM sqlite_master WHERE type=? AND name=?"
        assert t_conn.execute(q, ("table", "repo_meta")).fetchone() is not None

    @pytest.mark.parametrize(
        "name, typ, notnull, default, pk",
        [
            ("key", "TEXT", True, None, True),
            ("value", "TEXT", True, None, False),
        ],
    )
    def test_repo_meta_table_columns(self, t_db, name, typ, notnull, default, pk):
        """repo_meta has the expected columns."""
        kwargs = {"notnull": notnull, "default": default, "pk": pk}
        assert_column(t_db, "repo_meta", name, typ, **kwargs)

    def test_stamps_schema_version(self, t_db):
        """init_db stamps SCHEMA_VERSION into repo_meta."""
        q = "SELECT value FROM repo_meta WHERE key='schema_version'"
        assert t_db.execute(q).fetchone()[0] == SCHEMA_VERSION


class TestPendingMigrations:
    """Tests for pending_migrations()."""

    def test_empty_when_none_newer(self):
        """No migrations newer than stated yields empty."""
        assert pending_migrations(stated="1.7.1", available=["1.7.0", "1.0.0"]) == []

    def test_returns_newer_ordered(self):
        """Versions newer than stated returned ascending."""
        expected = ["1.7.2", "2.0.0"]
        avail = ["1.6.9", *expected]
        assert pending_migrations(stated="1.7.1", available=avail) == expected

    def test_excludes_stated_itself(self):
        """The stated version is not itself pending."""
        stated, expected = "1.7.1", ["1.7.2"]
        available = [stated, *expected]
        assert pending_migrations(stated=stated, available=available) == expected

    def test_orders_by_semver_not_lexically(self):
        """Ordering is numeric per segment, not string."""
        avail, expect = ["1.1.10", "1.1.2"], ["1.1.2", "1.1.10"]
        assert pending_migrations(stated="1.1.1", available=avail) == expect

    @pytest.mark.parametrize("bad", ["abc", "", "1.2.x", "v.e.r", "1.2", "1.2.3.4"])
    def test_raises_on_invalid_version(self, bad):
        """Unparseable or non-3-part version strings raise, naming the value."""
        with pytest.raises(InvalidVersion, match=re.escape(repr(bad))):
            pending_migrations("1.0.0", available=[bad, "2.0.0"])
        with pytest.raises(InvalidVersion, match=re.escape(repr(bad))):
            pending_migrations(bad, available=["3.0.0"])


class TestMigrationVersion:
    """Tests for _migration_version()."""

    def test_parses_well_formed_filename(self):
        """A well-formed migration filename yields its dotted version."""
        path = Path("test/migration-01-02-03.sql")
        assert _migration_version(path) == "1.2.3"

    def test_raises_on_non_migration_filename(self):
        """A filename without the migration- prefix raises."""
        with pytest.raises(InvalidVersion):
            assert _migration_version(Path("test/_schema.sql"))

    def test_raises_on_non_numeric_segments(self):
        """Non-numeric version segments raise."""
        # e.g. Path("migration-a-b-c.sql")
        with pytest.raises(InvalidVersion):
            _migration_version(Path("migration-a-b-c.sql"))

    def test_raises_on_wrong_segment_count(self):
        """A filename without exactly three version segments raises."""
        with pytest.raises(InvalidVersion):
            _migration_version(Path("migration-1-2.sql"))

    def test_raises_on_wrong_prefix(self):
        """A three-segment name without the migration- prefix raises."""
        with pytest.raises(InvalidVersion):
            _migration_version(Path("foobar-1-2-3.sql"))


class TestListMigrations:
    """Tests for list_migrations()."""

    def _write_schema_files(self, root: Path, paths: list[str]):
        for p in paths:
            (root / p).write_text(f"test path: {p}")

    def test_empty_when_no_migration_files(self, tmp_path):
        """A directory with no migration files yields empty."""
        assert list_migrations(tmp_path) == []

    def test_lists_versions_ascending(self, tmp_path):
        """Migration files are listed as versions, ascending."""
        files = [
            "migration-01-2-10.sql",
            "migration-1-02-2.sql",
            "migration-2-0-00.sql",
        ]
        self._write_schema_files(tmp_path, files)
        assert list_migrations(tmp_path) == ["1.2.2", "1.2.10", "2.0.0"]

    def test_ignores_non_migration_files(self, tmp_path):
        """Non-migration files in the directory are not listed."""
        files = ["migration-01-02-03.sql", "foobar-00-00-01.sql"]
        self._write_schema_files(tmp_path, files)
        assert list_migrations(tmp_path) == ["1.2.3"]

    def test_raises_on_malformed_migration_file(self, tmp_path):
        """A migration-globbed file with a bad version raises."""
        self._write_schema_files(tmp_path, ["migration-x-y-z.sql"])
        with pytest.raises(InvalidVersion):
            list_migrations(tmp_path)


class TestRowMappers:
    """Tests for row mapper functions."""

    def test_row_to_text_item(self, t_db):
        """Maps all fields from joined row to TextItem."""
        expected = insert_text_item(t_db)
        t_db.row_factory = sqlite3.Row
        row = t_db.execute(
            "SELECT i.*, t.format FROM items i"
            " JOIN text_items t ON i.hash_full = t.hash_full"
            f" WHERE i.code = '{expected.code}'"
        ).fetchone()
        result = _row_to_text_item(row)
        assert result == expected

    def test_row_to_pic_item(self, t_db):
        """Maps all fields from joined row to PicItem."""
        expected = insert_pic_item(t_db)
        t_db.row_factory = sqlite3.Row
        row = t_db.execute(
            "SELECT i.*, p.format, p.width, p.height FROM items i"
            " JOIN pic_items p ON i.hash_full = p.hash_full"
            f" WHERE i.code = '{expected.code}'"
        ).fetchone()
        result = _row_to_pic_item(row)
        assert result == expected

    def test_row_to_link_item(self, t_db):
        """Maps all fields from joined row to LinkItem."""
        expected = insert_link_item(t_db)
        t_db.row_factory = sqlite3.Row
        row = t_db.execute(
            "SELECT i.*, l.url FROM items i"
            " JOIN link_items l ON i.hash_full = l.hash_full"
            f" WHERE i.code = '{expected.code}'"
        ).fetchone()
        result = _row_to_link_item(row)
        assert result == expected


class TestGetByCode:
    """Tests for SqliteRepository.get_by_code()."""

    def test_none_for_code_not_exist(self, t_repo):
        """Returns None for 'Item.code' that doesn't exist"""
        assert t_repo.get_by_code("N0TF0VND") is None

    def test_text_item_for_text_item_code(self, t_repo):
        """Returns correct TextItem for its 'code' column"""
        insert_text_item(t_repo._conn)  # Assemble text_item record
        result = t_repo.get_by_code("T0123456")  # Act with get
        assert isinstance(result, TextItem)  # Assert it's a TextItem
        assert result.code == "T0123456"  # Assert it's the same code

    def test_pic_item_for_pic_item_code(self, t_repo):
        """Returns correct PicItem for its 'code' column"""
        insert_pic_item(t_repo._conn)  # Assemble
        result = t_repo.get_by_code("P0123456")  # Act
        assert isinstance(result, PicItem)  # Assert
        assert result.code == "P0123456"

    def test_link_item_for_link_item_code(self, t_repo):
        """Returns correct LinkItem for its 'code' column"""
        insert_link_item(t_repo._conn)  # Assemble
        result = t_repo.get_by_code("L0123456")  # Act
        assert isinstance(result, LinkItem)  # Assert
        assert result.code == "L0123456"


class TestGetByFullHash:
    """Tests for SqliteRepository.get_by_full_hash()."""

    def test_none_for_hash_not_exist(self, t_repo):
        """Returns None for nonexistent hash_full"""
        repo = SqliteRepository(t_repo._conn)
        assert repo.get_by_full_hash("0123456789ABCDEFGHJKMNPQ") is None

    def test_text_item_for_item_hash(self, t_repo):
        """Returns correct TextItem for its 'hash_full' PK"""
        insert_text_item(t_repo._conn)
        result = t_repo.get_by_full_hash("T0123456789ABCDEFGHJKMNP")
        assert isinstance(result, TextItem)
        assert result.hash_full == "T0123456789ABCDEFGHJKMNP"

    def test_pic_item_for_item_hash(self, t_repo):
        """Returns correct PicItem for its 'hash_full' PK"""
        insert_pic_item(t_repo._conn)
        result = t_repo.get_by_full_hash("P0123456789ABCDEFGHJKMNP")
        assert isinstance(result, PicItem)
        assert result.hash_full == "P0123456789ABCDEFGHJKMNP"

    def test_link_item_for_item_hash(self, t_repo):
        """Returns correct LinkItem for its 'hash_full' PK"""
        insert_link_item(t_repo._conn)
        result = t_repo.get_by_full_hash("L0123456789ABCDEFGHJKMNP")
        assert isinstance(result, LinkItem)
        assert result.hash_full == "L0123456789ABCDEFGHJKMNP"


class TestResolveCode:
    """Tests for SqliteRepository.resolve_code()."""

    def test_min_len_prefix_when_no_collisions(self, t_repo):
        """Returns min_len prefix when no collisions exist."""
        assert t_repo.resolve_code("01234567890ABCDEFGHJKMNP", min_len=8) == "01234567"

    def test_prefix_when_collision_exists(self, t_repo):
        """Extends prefix code length by 1 when 1 colliding prefix exists."""
        prefix, min_len = "01234567", 8
        hash1, hash2 = f"{prefix}00000000XXXXXXXX", f"{prefix}890ABCDEFGHJKMNP"
        insert_text_item(t_repo._conn, hash_full=hash1, code=prefix)
        assert t_repo.resolve_code(hash2, min_len=min_len) == prefix + hash2[min_len]

    def test_extends_code_many_times_for_many_collisions(self, t_repo):
        """Returns longer code when shorter prefixes collide"""
        # Insert items with codes that collide with target's prefixes
        target_hash = "01234567890ABCDEFGHJKMNP"
        for i in range(8, 24):
            hash_uniq = f"XXXXXXXXXXXXXXXXXXXXXX{i:02d}"  # unique hash per item
            code_colide = target_hash[:i]  # Coliding code is one longer than previous
            insert_link_item(t_repo._conn, hash_full=hash_uniq, code=code_colide)
        # All prefixes taken, should return full hash
        assert t_repo.resolve_code(target_hash, 8) == target_hash


class TestInsert:
    """Tests for SqliteRepository.insert()."""

    def test_inserts_text_item(self, t_repo, t_db):
        """Inserts TextItem and returns it"""
        insert_user(t_db, id=69)
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

    def test_inserts_link_item(self, t_repo, t_db):
        """Inserts LinkItem and returns it"""
        insert_user(t_db, id=42)
        kwargs = {"kind": ItemKind.LINK, "payload_bytes": b"http://a.eu"}
        plan = make_write_plan(**kwargs)
        result = t_repo.insert(plan, uid=42, perm=Visibility.UNLISTED)
        assert isinstance(result, LinkItem)
        assert result.code == plan.hash_full[: plan.code_min_len]
        assert result.size_b == plan.size_b
        assert result.upload_at == plan.upload_at
        assert result.uid == 42
        assert result.perm == Visibility.UNLISTED
        assert result.url == "http://a.eu"
        assert result == t_repo.get_by_full_hash(plan.hash_full)

    def test_raises_code_collision_error_on_duplicate_hash(self, t_repo):
        """Raises CodeCollisionError when same content inserted twice (dedupe leak)"""
        kwargs = {"code_min_len": 8, "kind": "url", "payload_bytes": b"http://a.eu"}
        plan1 = make_write_plan(**kwargs)
        plan2 = make_write_plan(**kwargs)
        t_repo.insert(plan1)
        with pytest.raises(errors.CodeCollisionError) as exc_info:
            t_repo.insert(plan2)
        e = exc_info.value
        assert plan2.hash_full in str(e)
        assert plan1.hash_full[: plan1.code_min_len] in str(e)

    def test_resolve_prevents_code_collision(self, t_repo):
        """resolve_code extends to avoid collision"""
        prefix = "ABCD1234"
        insert_link_item(t_repo._conn, hash_full=("X" * 24), code=prefix)
        plan = make_write_plan(
            hash_full=f"{prefix}XXXXXXXXXXXXXXXX",  # Same 8-char prefix
            code_min_len=8,
            kind=ItemKind.LINK,
            payload_bytes=b"http://test.com",
        )  # Extends to 9 chars, no collision vvv
        assert t_repo.insert(plan).code == prefix + "X"


class TestDelete:
    """Tests for SqliteRepository.delete()."""

    def test_delete_cascades_to_subtype(self, t_repo):
        """Deleting item removes row from items and correct subtype table."""
        con, hash_suffix = t_repo._conn, "0123456789ABCDEFGHJKMNP"  # 23 char suffix
        insert_text_item(con, hash_full=f"T{hash_suffix}", code="TXTC0DE1")
        insert_pic_item(con, hash_full=f"P{hash_suffix}", code="PICC0DE1")
        insert_link_item(con, hash_full=f"L{hash_suffix}", code="URLC0DE1")

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


class TestUserCrud:
    """Tests for SqliteRepository user CRUD methods."""

    def _seeded_user(self, t_repo, **overrides) -> User:
        """Insert and return a user with overridable defaults."""
        user = make_user(id=1, **overrides)
        return t_repo.insert_user(user)

    def test_insert_returns_user(self, t_repo):
        """insert_user returns a User equal to the inserted one."""
        user = make_user(id=1)
        result = t_repo.insert_user(user)
        assert result == user

    def test_get_user_by_id(self, t_repo):
        """get_user returns the correct User by id."""
        user = self._seeded_user(t_repo)
        result = t_repo.get_user(1)
        assert result == user

    def test_get_user_by_email(self, t_repo):
        """get_user_by_email returns the correct User by email."""
        user = self._seeded_user(t_repo, email="me@myself.com")
        result = t_repo.get_user_by_email("me@myself.com")
        assert result == user

    def test_get_user_by_email_not_found(self, t_repo):
        """get_user_by_email raises NotFoundError when email absent."""
        with pytest.raises(errors.NotFoundError):
            t_repo.get_user_by_email("not@exist.net")

    def test_unique_email_violation(self, t_repo):
        """Inserting duplicate email raises an integrity error."""
        u1, u2 = make_user(id=1, name="Alice"), make_user(id=2, name="Bob")
        t_repo.insert_user(u1)
        with pytest.raises(errors.UniqueViolationError) as exc_info:
            t_repo.insert_user(u2)
        assert exc_info.value.domain == "User"
        assert exc_info.value.field == "email"
        assert exc_info.value.value == "guy@example.com"

    def test_unique_name_violation(self, t_repo):
        """Inserting duplicate name raises an integrity error."""
        u1, u2 = make_user(id=1, email="a@t.se"), make_user(id=2, email="b@t.se")
        t_repo.insert_user(u1)
        with pytest.raises(errors.UniqueViolationError) as exc_info:
            t_repo.insert_user(u2)
        assert exc_info.value.domain == "User"
        assert exc_info.value.field == "name"
        assert exc_info.value.value == "GuyMann"

    def test_get_user_not_found(self, t_repo):
        """get_user raises NotFoundError when uid absent."""
        with pytest.raises(errors.NotFoundError) as exc_info:
            t_repo.get_user(9999)
        assert exc_info.value.id == "9999"
        assert exc_info.value.resource == "User"

    def test_update_pw_hash(self, t_repo):
        """update_user_pw_hash changes the stored pw_hash for an existing user."""
        self._seeded_user(t_repo)
        t_repo.update_user_pw_hash(1, "new_hash_foobar")
        assert t_repo.get_user(1).pw_hash == "new_hash_foobar"

    def test_update_pw_hash_not_found(self, t_repo):
        """update_user_pw_hash raises NotFoundError for unknown uid."""
        with pytest.raises(errors.NotFoundError) as exc_info:
            t_repo.update_user_pw_hash(9999, "irrelevant_hash")
        assert exc_info.value.id == "9999"
        assert exc_info.value.resource == "User"


class TestUserPersistence:
    """End-to-end gating test for user persistence round-trip."""

    def test_user_round_trips_by_id_and_email(self, t_repo):
        """Insert a User and fetch it by both id and email."""
        user = make_user(id=1, email="marcus@test.se")
        t_repo.insert_user(user)
        u_by_id = t_repo.get_user(1)
        u_by_mail = t_repo.get_user_by_email("marcus@test.se")
        assert u_by_id == user
        assert u_by_mail == user
