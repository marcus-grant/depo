# tests/helpers/test_assertions.py
"""
Tests for assertion helpers.
Author: Marcus Grant
Date: 2026-01-26
License: Apache-2.0
"""

import pytest

from depo.model.enums import ItemKind, Visibility
from tests.factories import make_item
from tests.helpers.assertions import assert_column, assert_item_base_fields


class TestAssertColumn:
    """Tests for assert_column()."""

    def test_pass_for_matching_name_and_type(self, conn):
        """passes for column with matching name and type"""
        conn.execute("CREATE TABLE t (id INTEGER)")
        assert_column(conn, "t", "id", "INTEGER")

    def test_fail_for_nonexistent_column(self, conn):
        """fails for nonexistent column"""
        conn.execute("CREATE TABLE t (id INTEGER)")
        with pytest.raises(AssertionError, match="missing column"):
            assert_column(conn, "t", "missing", "INTEGER")

    def test_fail_for_wrong_type(self, conn):
        """fails for wrong type"""
        conn.execute("CREATE TABLE t (id INTEGER)")
        with pytest.raises(AssertionError, match="type mismatch"):
            assert_column(conn, "t", "id", "TEXT")

    def test_pass_for_notnull_column(self, conn):
        """passes for NOT NULL column when notnull=True"""
        conn.execute("CREATE TABLE t (id INTEGER NOT NULL)")
        assert_column(conn, "t", "id", "INTEGER", notnull=True)

    def test_fail_for_nullable_when_notnull_expected(self, conn):
        """fails for nullable column when notnull=True"""
        conn.execute("CREATE TABLE t (id INTEGER)")
        with pytest.raises(AssertionError, match="notnull mismatch"):
            assert_column(conn, "t", "id", "INTEGER", notnull=True)

    def test_pass_for_matching_default(self, conn):
        """passes for column with matching default value"""
        conn.execute("CREATE TABLE t (id INTEGER DEFAULT 42)")
        assert_column(conn, "t", "id", "INTEGER", default="42")

    def test_fail_for_wrong_default(self, conn):
        """fails for column with wrong default value"""
        conn.execute("CREATE TABLE t (id INTEGER DEFAULT 42)")
        with pytest.raises(AssertionError, match="default mismatch"):
            assert_column(conn, "t", "id", "INTEGER", default="99")

    def test_pass_for_pk_column(self, conn):
        """passes for PRIMARY KEY column when pk=True"""
        conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY)")
        assert_column(conn, "t", "id", "INTEGER", pk=True)

    def test_fail_for_non_pk_when_pk_expected(self, conn):
        """fails for non-PK column when pk=True"""
        conn.execute("CREATE TABLE t (id INTEGER)")
        with pytest.raises(AssertionError, match="pk mismatch"):
            assert_column(conn, "t", "id", "INTEGER", pk=True)


class TestAssertItemBaseFields:
    """Tests for assert_item_base_fields()."""

    def test_pass_for_matching_fields(self):
        """passes when all base fields match."""
        item = make_item(
            code="ABC12345",
            hash_full="ABC1234506789DEFGHKMNPQR",
            kind=ItemKind.TEXT,
            size_b=100,
            uid=1,
            perm=Visibility.PUBLIC,
            upload_at=1234567890,
            origin_at=None,
        )
        assert_item_base_fields(
            item,
            code="ABC12345",
            hash_full="ABC1234506789DEFGHKMNPQR",
            kind=ItemKind.TEXT,
            size_b=100,
            uid=1,
            perm=Visibility.PUBLIC,
            upload_at=1234567890,
            origin_at=None,
        )

    def test_fail_for_wrong_code(self):
        """fails when code doesn't match."""
        item = make_item(code="ABC12345")
        with pytest.raises(AssertionError, match="code"):
            assert_item_base_fields(
                item,
                code="WRONG",
                hash_full=item.hash_full,
                kind=item.kind,
                size_b=item.size_b,
                uid=item.uid,
                perm=item.perm,
                upload_at=item.upload_at,
                origin_at=item.origin_at,
            )

    def test_fail_for_wrong_kind(self):
        """fails when kind doesn't match."""
        item = make_item(kind=ItemKind.TEXT)
        with pytest.raises(AssertionError, match="kind"):
            assert_item_base_fields(
                item,
                code=item.code,
                hash_full=item.hash_full,
                kind=ItemKind.PICTURE,
                size_b=item.size_b,
                uid=item.uid,
                perm=item.perm,
                upload_at=item.upload_at,
                origin_at=item.origin_at,
            )
