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

from depo.model.enums import ContentFormat, Visibility
from depo.model.item import ItemKind, LinkItem, PicItem, TextItem


def insert_text_item(
    conn: sqlite3.Connection,
    hash_full: str = "ABC1234506789DEFGHKMNPQR",
    code: str = "ABCD1234",
    size_b: int = 99,
    uid: int = 0,
    perm: Visibility = Visibility.PUBLIC,
    upload_at: int = 123456789,
    origin_at: int | None = None,
    format: ContentFormat = ContentFormat.PLAINTEXT,
) -> TextItem:
    """Insert a TextItem via raw SQL and return the domain object."""
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
    return TextItem(
        hash_full=hash_full,
        code=code,
        kind=ItemKind.TEXT,
        size_b=size_b,
        uid=uid,
        perm=perm,
        upload_at=upload_at,
        origin_at=origin_at,
        format=format,
    )


def insert_pic_item(
    conn: sqlite3.Connection,
    hash_full: str = "ABC1234506789DEFGHKMNPQR",
    code: str = "ABCD1234",
    size_b: int = 99,
    uid: int = 0,
    perm: Visibility = Visibility.PUBLIC,
    upload_at: int = 123456789,
    origin_at: int | None = None,
    format: ContentFormat = ContentFormat.JPEG,
    width: int = 320,
    height: int = 240,
) -> PicItem:
    """Insert a PicItem via raw SQL and return the domain object."""
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
    return PicItem(
        hash_full=hash_full,
        code=code,
        kind=ItemKind.PICTURE,
        size_b=size_b,
        uid=uid,
        perm=perm,
        upload_at=upload_at,
        origin_at=origin_at,
        format=format,
        width=width,
        height=height,
    )


def insert_link_item(
    conn: sqlite3.Connection,
    hash_full: str = "ABC1234506789DEFGHKMNPQR",
    code: str = "ABCD1234",
    size_b: int = 99,
    uid: int = 0,
    perm: Visibility = Visibility.PUBLIC,
    upload_at: int = 123456789,
    origin_at: int | None = None,
    url: str = "https://example.com",
) -> LinkItem:
    """Insert a LinkItem via raw SQL and return the domain object."""

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
    return LinkItem(
        hash_full=hash_full,
        code=code,
        kind=ItemKind.LINK,
        size_b=size_b,
        uid=uid,
        perm=perm,
        upload_at=upload_at,
        origin_at=origin_at,
        url=url,
    )


def seed_all_types(conn: sqlite3.Connection) -> tuple[TextItem, PicItem, LinkItem]:
    """
    Insert one TextItem, PicItem, LinkItem with distinct hashes/codes.

    Returns:
        (TextItem, PicItem, LinkItem) tuple of inserted items.
        Note: hash_full and code values are derived from:
        {T, P, L} + first chars of crockford alphabet for easy verification.
    """
    hash_suffix = "0123456789ABCDEFGHJKMNP"  # Use first 23 of crockford alphabet
    txt_prefix, pic_prefix, link_prefix = "T", "P", "L"
    txt_hash, txt_code = txt_prefix + hash_suffix, txt_prefix + hash_suffix[:8]
    pic_hash, pic_code = pic_prefix + hash_suffix, pic_prefix + hash_suffix[:8]
    link_hash, link_code = link_prefix + hash_suffix, link_prefix + hash_suffix[:8]
    txt_item = insert_text_item(conn, hash_full=txt_hash, code=txt_code)
    pic_item = insert_pic_item(conn, hash_full=pic_hash, code=pic_code)
    link_item = insert_link_item(conn, hash_full=link_hash, code=link_code)
    return (txt_item, pic_item, link_item)
