# tests/helpers/assertions.py
"""
Assertion helpers for common testing patterns.
Author: Marcus Grant
Date: 2026-01-26
License: Apache-2.0
"""

import sqlite3
from dataclasses import MISSING, fields
from typing import Any


def assert_field(cls: type, name: str, typ: type, required: bool, default: Any) -> None:
    """
    Assert a dataclass field has the expected specification.

    Args:
        cls: The dataclass class to inspect.
        name: Expected field name.
        typ: Expected field type annotation.
        required: If True, field must have no default value.
        default: Expected default value (ignored if required is True).

    Raises:
        AssertionError: If any expectation is not met.

    Example:
        @pytest.mark.parametrize(("name", "typ", "required", "default"), [
            ("code", str, True, None),
            ("size_b", int, True, None),
            ("perm", Visibility, False, Visibility.PUBLIC),
        ])
        def test_fields(self, name, typ, required, default):
            assert_field(Item, name, typ, required, default)
    """
    field_map = {f.name: f for f in fields(cls)}
    assert name in field_map, f"missing field: {name}"
    f = field_map[name]
    assert f.type == typ, f"{name} type mismatch: expected {typ}, got {f.type}"
    if required:
        assert f.default is MISSING, f"{name} should be required"
    else:
        msg = f"{name} default mismatch: expected {default}, got {f.default}"
        assert f.default == default, msg


### Database Assertions ###
def assert_column(
    conn: sqlite3.Connection,
    table: str,
    name: str,
    typ: str,
    *,
    notnull: bool = False,
    default: Any = None,
    pk: bool = False,
) -> None:
    """
    Assert a SQLite table column has expected properties.

    Args:
        conn: SQLite connection.
        table: Table name.
        name: Column name.
        typ: Expected type (TEXT, INTEGER, etc.).
        notnull: If True, column must be NOT NULL.
        default: Expected default value (None if no default).
        pk: If True, column must be PRIMARY KEY.

    Raises:
        AssertionError: If any expectation is not met.
    """
    cursor = conn.execute(f"PRAGMA table_info({table})")
    columns = {row[1]: row for row in cursor.fetchall()}
    # row: (cid, name, type, notnull, dflt_value, pk)

    assert name in columns, f"missing column: {name}"
    row = columns[name]

    assert row[2] == typ, f"{name} type mismatch: expected {typ}, got {row[2]}"
    assert row[3] == int(notnull), (
        f"{name} notnull mismatch: expected {notnull}, got {bool(row[3])}"
    )
    assert row[4] == default, (
        f"{name} default mismatch: expected {default}, got {row[4]}"
    )
    assert row[5] == int(pk), f"{name} pk mismatch: expected {pk}, got {bool(row[5])}"
