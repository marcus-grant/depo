-- src/depo/repo/schema.sql
-- SQLite schema for depo item storage.
-- Author: Marcus Grant
-- Date: 2026-01-26
-- License: Apache-2.0

CREATE TABLE IF NOT EXISTS items (
    hash_full   TEXT PRIMARY KEY,
    code        TEXT UNIQUE NOT NULL,
    kind        TEXT NOT NULL,
    size_b      INTEGER NOT NULL,
    uid         INTEGER NOT NULL DEFAULT 0,
    perm        TEXT NOT NULL DEFAULT 'pub',
    upload_at   INTEGER NOT NULL,
    origin_at   INTEGER
);

CREATE TABLE IF NOT EXISTS text_items (
    hash_full   TEXT PRIMARY KEY REFERENCES items(hash_full),
    format      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS pic_items (
    hash_full   TEXT PRIMARY KEY REFERENCES items(hash_full),
    format      TEXT NOT NULL,
    width       INTEGER NOT NULL,
    height      INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS link_items (
    hash_full   TEXT PRIMARY KEY REFERENCES items(hash_full),
    url         TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_items_uid ON items(uid);
CREATE INDEX IF NOT EXISTS idx_items_kind ON items(kind);
CREATE INDEX IF NOT EXISTS idx_items_upload ON items(upload_at);
