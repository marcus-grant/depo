# src/depo/repo/sqlite.py
"""
SQLite implementation of item repository.
Author: Marcus Grant
Date: 2026-01-26
License: Apache-2.0
"""

import sqlite3
from importlib import resources

from depo.model.enums import ContentFormat, ItemKind, Visibility
from depo.model.item import LinkItem, PicItem, TextItem


def init_db(conn: sqlite3.Connection) -> None:
    """
    Apply schema to connection. Idempotent.

    Args:
        conn: SQLite connection to initialize.
    """
    schema = resources.files("depo.repo").joinpath("schema.sql").read_text()
    conn.executescript(schema)


def _row_to_text_item(row: sqlite3.Row) -> TextItem:
    """Map joined items + text_items row to TextItem."""
    return TextItem(
        code=row["code"],
        hash_full=row["hash_full"],
        kind=ItemKind(row["kind"]),
        size_b=row["size_b"],
        uid=row["uid"],
        upload_at=row["upload_at"],
        origin_at=row["origin_at"],
        perm=Visibility(row["perm"]),
        format=ContentFormat(row["format"]),
    )


def _row_to_pic_item(row: sqlite3.Row) -> PicItem:
    """Map joined items + pic_items row to PicItem."""
    return PicItem(
        code=row["code"],
        hash_full=row["hash_full"],
        kind=ItemKind(row["kind"]),
        size_b=row["size_b"],
        uid=row["uid"],
        upload_at=row["upload_at"],
        origin_at=row["origin_at"],
        perm=Visibility(row["perm"]),
        format=ContentFormat(row["format"]),
        width=row["width"],
        height=row["height"],
    )


def _row_to_link_item(row: sqlite3.Row) -> LinkItem:
    """Map joined items + link_items row to LinkItem."""
    return LinkItem(
        code=row["code"],
        hash_full=row["hash_full"],
        kind=ItemKind(row["kind"]),
        size_b=row["size_b"],
        uid=row["uid"],
        upload_at=row["upload_at"],
        origin_at=row["origin_at"],
        perm=Visibility(row["perm"]),
        url=row["url"],
    )


class SqliteRepository:
    """SQLite implementation of item repository."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        """
        Initialize repository with database connection.

        Args:
            conn: SQLite connection (schema must be initialized).
        """
        self._conn = conn
        self._conn.row_factory = sqlite3.Row

    # NOTE: its specs are checked in all branches by testing the getter methods
    def _fetch_full_item(self, i_row: sqlite3.Row) -> TextItem | PicItem | LinkItem:
        """
        Fetch subtype data and return full joined item given base items row.

        Args:
            i_row: Row from items table query.

        Returns:
            Fully populated item subclass.

        Raises:
            ValueError: If item has unknown kind (indicates data corruption).
        """
        # Discriminate based on items.kind
        # Then feed each kinds' row_to_*_item helper with a join query
        # Each ItemKind has its own join query
        kind = ItemKind(i_row["kind"])
        if kind == ItemKind.TEXT:
            return _row_to_text_item(
                self._conn.execute(
                    "SELECT i.*, t.format FROM items i "
                    "JOIN text_items t ON i.hash_full = t.hash_full "
                    "WHERE i.hash_full = ?",
                    (i_row["hash_full"],),
                ).fetchone()
            )
        if kind == ItemKind.PICTURE:
            return _row_to_pic_item(
                self._conn.execute(
                    "SELECT i.*, p.format, p.width, p.height FROM items i "
                    "JOIN pic_items p ON i.hash_full = p.hash_full "
                    "WHERE i.hash_full = ?",
                    (i_row["hash_full"],),
                ).fetchone()
            )
        if kind == ItemKind.LINK:
            return _row_to_link_item(
                self._conn.execute(
                    "SELECT i.*, l.url FROM items i "
                    "JOIN link_items l ON i.hash_full = l.hash_full "
                    "WHERE i.hash_full = ?",
                    (i_row["hash_full"],),
                ).fetchone()
            )

        raise ValueError(f"Unknown item kind: {kind}")

    def get_by_code(self, code: str) -> TextItem | PicItem | LinkItem | None:
        """
        Lookup item by exact code.

        Assumes input is already canonicalized via canonicalize_code().
        Returns None if not found.

        Args:
            code: Canonicalized shortcode.

        Returns:
            Item subclass instance or None.

        Raises:
            ValueError: If item has unknown kind (indicates data corruption).
        """
        # First query parent items table for the code
        i_row = self._conn.execute(
            "SELECT * FROM items WHERE code = ?", (code,)
        ).fetchone()

        # Check for not being present
        if i_row is None:
            return None

        return self._fetch_full_item(i_row)

    def get_by_full_hash(self, hash_full: str) -> TextItem | PicItem | LinkItem | None:
        """
        Dedupe lookup by content hash.

        Args:
            hash_full: Full content hash.

        Returns:
            Item subclass instance or None if not found.

        Raises:
            ValueError: If item has unknown kind (indicates data corruption).
        """
        # First query items table for the hash_full
        i_row = self._conn.execute(
            "SELECT * FROM items WHERE hash_full = ?", (hash_full,)
        ).fetchone()

        # Check for not being present
        if i_row is None:
            return None

        return self._fetch_full_item(i_row)

    def resolve_code(self, hash_full: str, min_len: int) -> str:
        """
        Find shortest unique code prefix.

        Starts at min_len, extends until no collision with existing codes.

        Args:
            hash_full: Full content hash (24 chars).
            min_len: Minimum code length to start with.

        Returns:
            Unique code string (min_len to 24 chars).
        """
        # Start with the minimum length as prefix
        prefix = hash_full[:min_len]
        existing = {  # Gather all codes matching the prefix
            row[0]
            for row in self._conn.execute(
                "SELECT code FROM items WHERE code LIKE ?", (prefix + "%",)
            ).fetchall()
        }  # Go through matching codes of minimum prefix length upwards
        for length in range(min_len, 25):
            candidate = hash_full[:length]  # Increase candidate length
            if candidate not in existing:  # Check if in existing codes
                return candidate  # If not, this is our new unique code
        return hash_full  # Fallback to full hash as code (extremely unlikely)
