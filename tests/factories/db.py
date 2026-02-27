# tests/factories/db.py
"""
Database seed helpers for integration tests.

Raw SQL inserts that bypass the repo layer to
establish known DB state.

Author: Marcus Grant
Created: 2026-02-06
License: Apache-2.0
"""

import sqlite3

from depo.model.item import LinkItem, PicItem, TextItem
from tests.factories.models import make_link_item, make_pic_item, make_text_item


def insert_text_item(conn: sqlite3.Connection, **overrides) -> TextItem:
    """Insert a TextItem via raw SQL and return the domain object."""
    item = make_text_item(**overrides)
    conn.execute(
        "INSERT INTO items"
        "(hash_full, code, kind, size_b, uid, perm, upload_at, origin_at)"
        "VALUES (?, ?, 'txt', ?, ?, ?, ?, ?)",
        (
            item.hash_full,
            item.code,
            item.size_b,
            item.uid,
            item.perm,
            item.upload_at,
            item.origin_at,
        ),
    )
    conn.execute(
        "INSERT INTO text_items (hash_full, format) VALUES (?, ?)",
        (item.hash_full, item.format),
    )
    return item


def insert_pic_item(conn: sqlite3.Connection, **overrides) -> PicItem:
    """Insert a PicItem via raw SQL and return the domain object."""
    item = make_pic_item(**overrides)
    conn.execute(
        "INSERT INTO items"
        "(hash_full, code, kind, size_b, uid, perm, upload_at, origin_at)"
        "VALUES (?, ?, 'pic', ?, ?, ?, ?, ?)",
        (
            item.hash_full,
            item.code,
            item.size_b,
            item.uid,
            item.perm,
            item.upload_at,
            item.origin_at,
        ),
    )
    conn.execute(
        "INSERT INTO pic_items (hash_full, format, width, height) VALUES (?, ?, ?, ?)",
        (item.hash_full, item.format, item.width, item.height),
    )
    return item


def insert_link_item(conn: sqlite3.Connection, **overrides) -> LinkItem:
    """Insert a LinkItem via raw SQL and return the domain object."""
    item = make_link_item(**overrides)
    conn.execute(
        "INSERT INTO items"
        "(hash_full, code, kind, size_b, uid, perm, upload_at, origin_at)"
        "VALUES (?, ?, 'url', ?, ?, ?, ?, ?)",
        (
            item.hash_full,
            item.code,
            item.size_b,
            item.uid,
            item.perm,
            item.upload_at,
            item.origin_at,
        ),
    )
    conn.execute(
        "INSERT INTO link_items (hash_full, url) VALUES (?, ?)",
        (item.hash_full, item.url),
    )
    return item


def seed_all_types(conn: sqlite3.Connection) -> tuple[TextItem, PicItem, LinkItem]:
    """Insert one TextItem, PicItem, LinkItem with distinct hashes/codes."""
    return (insert_text_item(conn), insert_pic_item(conn), insert_link_item(conn))
