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
