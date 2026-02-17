# tests/fixtures/__init__.py
"""
Centralized test fixtures.

Prefix: t_ for first-party test fixtures.

Author: Marcus Grant
Date: 2026-02-05
License: Apache-2.0
"""

import sqlite3
from collections.abc import Generator
from dataclasses import dataclass
from typing import cast

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from depo.model.enums import ContentFormat
from depo.model.item import LinkItem, PicItem, TextItem
from depo.repo.sqlite import SqliteRepository, init_db
from depo.service.ingest import IngestService
from depo.service.orchestrator import IngestOrchestrator
from depo.storage.filesystem import FilesystemStorage
from tests.factories import gen_image, make_client
from tests.factories.db import insert_link_item, insert_pic_item, insert_text_item


@pytest.fixture
def t_conn() -> Generator[sqlite3.Connection, None, None]:
    """Raw in-memory SQLite connection, no schema.

    No dependencies. Use for testing init_db itself
    or schema-independent SQL.
    """
    c = sqlite3.connect(":memory:")
    yield c
    c.close()


@pytest.fixture
def t_db() -> Generator[sqlite3.Connection, None, None]:
    """In-memory SQLite with schema initialized.

    No dependencies. Use for direct SQL inserts
    or as a base for t_repo.
    """
    c = sqlite3.connect(":memory:")
    init_db(c)
    yield c
    c.close()


@pytest.fixture
def t_repo(t_db) -> SqliteRepository:
    """SqliteRepository over in-memory DB.

    Depends on t_db. Use for repo method tests
    without web or storage layers.
    """
    return SqliteRepository(t_db)


@pytest.fixture
def t_store(tmp_path) -> FilesystemStorage:
    """FilesystemStorage at a tmp_path subdirectory.

    Depends on tmp_path.
    Use for storage tests without DB or web layers.
    """
    return FilesystemStorage(root=tmp_path / "depo-test-store")


@pytest.fixture
def t_orch_env(
    t_repo, t_store
) -> tuple[IngestOrchestrator, SqliteRepository, FilesystemStorage]:
    """Orchestrator wired to t_repo and t_store.

    Depends on t_repo, t_store. Returns
    (orchestrator, repo, store) for ingest integration
    tests that need to inspect side effects.
    """
    service = IngestService()
    orch = IngestOrchestrator(service, t_repo, t_store)
    return (orch, t_repo, t_store)


# --- Web fixtures ---


@pytest.fixture
def t_client(tmp_path) -> TestClient:
    """Bare TestClient with empty database and storage.

    App is fully wired (DB initialized, store directory created)
    but contains no items. Use for upload/POST tests where the
    test creates its own content. Backed by make_client.
    Depends on pytest builtin fixture: tmp_path for isolated filesystem.
    """
    client = make_client(tmp_path)  # creates DB and store dirs at tmp_path
    assert client is not None
    return client


@dataclass(frozen=True)
class SeededApp:
    """TestClient bundled with pre-populated items.

    Contains one of each item kind (text, pic, link) seeded
    via repo and store directly. No upload round-trip.
    Use for GET/info/raw tests where content is a precondition.
    Access item fields (code, hash_full, etc.) for assertions.
    """

    client: TestClient
    txt: TextItem
    pic: PicItem
    link: LinkItem


@pytest.fixture
def t_seeded(tmp_path) -> SeededApp:
    """TestClient with one text, pic, and link item pre-populated.

    Depends on tmp_path. Seeds via client.app.state.repo
    and client.app.state.store using db insert helpers
    and store.write. No upload round-trip. Use for
    GET/info/raw tests where content is a precondition.
    """
    client = make_client(tmp_path)
    app = cast(FastAPI, client.app)
    conn = app.state.repo._conn
    store: FilesystemStorage = app.state.store

    txt_data = b"# Hello, World!\n**This** is a test `TextItem`."
    pic_data = gen_image("jpeg", 320, 240)
    link_url = "http://example.com"

    hash_sfx = "0123456789ABCDEFGHJKMNP"
    item_txt = insert_text_item(
        conn,
        hash_full="T" + hash_sfx,
        code="T" + hash_sfx[:7],
        size_b=len(txt_data),
        format=ContentFormat.MARKDOWN,
    )
    item_pic = insert_pic_item(
        conn,
        hash_full="P" + hash_sfx,
        code="P" + hash_sfx[:7],
        size_b=len(pic_data),
        width=320,
        height=240,
    )
    item_link = insert_link_item(
        conn,
        hash_full="L" + hash_sfx,
        code="L" + hash_sfx[:7],
        size_b=len(link_url.encode()),
        url=link_url,
    )

    store.put(code=item_txt.code, format=item_txt.format, source_bytes=txt_data)
    store.put(code=item_pic.code, format=item_pic.format, source_bytes=pic_data)

    return SeededApp(client=client, txt=item_txt, pic=item_pic, link=item_link)


__all__ = [
    "SeededApp",
    "t_client",
    "t_conn",
    "t_db",
    "t_orch_env",
    "t_repo",
    "t_seeded",
    "t_store",
]
