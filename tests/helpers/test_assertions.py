# tests/helpers/test_assertions.py
"""
Tests for assertion helpers.
Author: Marcus Grant
Date: 2026-01-26
License: Apache-2.0
"""

import pytest

from tests.helpers.assertions import assert_column


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

    # fails for nonexistent column
    # fails for wrong type
    # passes for NOT NULL column when notnull=True
    # fails for nullable column when notnull=True
    # passes for column with matching default value
    # fails for column with wrong default value
    # passes for PRIMARY KEY column when pk=True
    # fails for non-PK column when pk=True
