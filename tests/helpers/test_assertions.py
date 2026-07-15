# tests/helpers/test_assertions.py
"""
Tests for assertion helpers.
Author: Marcus Grant
Date: 2026-01-26
License: Apache-2.0
"""

from dataclasses import dataclass, field
from typing import cast

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tests.helpers import assertions


class TestAssertColumn:
    """Tests for assert_column()."""

    def test_pass_for_matching_name_and_type(self, t_conn):
        """passes for column with matching name and type"""
        t_conn.execute("CREATE TABLE t (id INTEGER)")
        assertions.assert_column(t_conn, "t", "id", "INTEGER")

    def test_fail_for_nonexistent_column(self, t_conn):
        """fails for nonexistent column"""
        t_conn.execute("CREATE TABLE t (id INTEGER)")
        with pytest.raises(AssertionError, match="missing column"):
            assertions.assert_column(t_conn, "t", "missing", "INTEGER")

    def test_fail_for_wrong_type(self, t_conn):
        """fails for wrong type"""
        t_conn.execute("CREATE TABLE t (id INTEGER)")
        with pytest.raises(AssertionError, match="type mismatch"):
            assertions.assert_column(t_conn, "t", "id", "TEXT")

    def test_pass_for_notnull_column(self, t_conn):
        """passes for NOT NULL column when notnull=True"""
        t_conn.execute("CREATE TABLE t (id INTEGER NOT NULL)")
        assertions.assert_column(t_conn, "t", "id", "INTEGER", notnull=True)

    def test_fail_for_nullable_when_notnull_expected(self, t_conn):
        """fails for nullable column when notnull=True"""
        t_conn.execute("CREATE TABLE t (id INTEGER)")
        with pytest.raises(AssertionError, match="notnull mismatch"):
            assertions.assert_column(t_conn, "t", "id", "INTEGER", notnull=True)

    def test_pass_for_matching_default(self, t_conn):
        """passes for column with matching default value"""
        t_conn.execute("CREATE TABLE t (id INTEGER DEFAULT 42)")
        assertions.assert_column(t_conn, "t", "id", "INTEGER", default="42")

    def test_fail_for_wrong_default(self, t_conn):
        """fails for column with wrong default value"""
        t_conn.execute("CREATE TABLE t (id INTEGER DEFAULT 42)")
        with pytest.raises(AssertionError, match="default mismatch"):
            assertions.assert_column(t_conn, "t", "id", "INTEGER", default="99")

    def test_pass_for_pk_column(self, t_conn):
        """passes for PRIMARY KEY column when pk=True"""
        t_conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY)")
        assertions.assert_column(t_conn, "t", "id", "INTEGER", pk=True)

    def test_fail_for_non_pk_when_pk_expected(self, t_conn):
        """fails for non-PK column when pk=True"""
        t_conn.execute("CREATE TABLE t (id INTEGER)")
        with pytest.raises(AssertionError, match="pk mismatch"):
            assertions.assert_column(t_conn, "t", "id", "INTEGER", pk=True)


@dataclass
class _SampleDClass:
    """Minimal dataclass for testing assert_field."""

    req: str
    opt: int = 42
    fac: list = field(default_factory=list)


class TestAssertField:
    """Tests for assert_field() helper."""

    def test_required_field_passes(self):
        assertions.assert_field(_SampleDClass, "req", str, True, None)

    def test_required_field_fails_when_has_default(self):
        with pytest.raises(AssertionError, match="should be required"):
            assertions.assert_field(_SampleDClass, "opt", int, True, None)

    def test_default_field_passes(self):
        assertions.assert_field(_SampleDClass, "opt", int, False, 42)

    def test_default_field_wrong_value(self):
        with pytest.raises(AssertionError, match="default mismatch"):
            assertions.assert_field(_SampleDClass, "opt", int, False, 99)

    def test_factory_field_passes(self):
        assertions.assert_field(_SampleDClass, "fac", list, False, [], factory=True)

    def test_factory_field_wrong_value(self):
        with pytest.raises(AssertionError, match="factory default mismatch"):
            args = (_SampleDClass, "fac", list, False, [1, 2])
            assertions.assert_field(*args, factory=True)

    def test_factory_flag_on_non_factory_fails(self):
        with pytest.raises(AssertionError, match="should use default_factory"):
            assertions.assert_field(_SampleDClass, "opt", int, False, 42, factory=True)

    def test_missing_field(self):
        with pytest.raises(AssertionError, match="missing field"):
            assertions.assert_field(_SampleDClass, "nope", str, True, None)

    def test_wrong_type(self):
        with pytest.raises(AssertionError, match="type mismatch"):
            assertions.assert_field(_SampleDClass, "req", int, True, None)


class TestAssertNoPersistence:
    """Tests for assert_no_persistence()."""

    def test_pass_when_empty(self, t_client: TestClient):
        """passes when no items row and no stored object exist"""
        assertions.assert_no_persistence(cast(FastAPI, t_client.app))

    def test_fail_when_item_persisted(self, t_client: TestClient):
        """fails when an items row exists"""
        q = "INSERT INTO items (hash_full, code, kind, size_b, upload_at) "
        q += "VALUES ('h', 'abc', 'text', 1, 0)"
        app = cast(FastAPI, t_client.app)
        app.state.repo._conn.execute(q)
        with pytest.raises(AssertionError):
            assertions.assert_no_persistence(app)

    def test_fail_when_object_stored(self, t_client: TestClient):
        """fails when a file exists in the store root"""
        app = cast(FastAPI, t_client.app)
        (app.state.store._root / "abc.txt").write_text("x")
        with pytest.raises(AssertionError):
            assertions.assert_no_persistence(app)
