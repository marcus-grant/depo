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

from depo.model.item import LinkItem, PicItem, TextItem
from depo.model.user import User
from depo.repo.sqlite import SqliteRepository, init_db
from depo.service.orchestrator import IngestOrchestrator
from depo.storage.filesystem import FilesystemStorage
from depo.util.password import hash_password
from tests.factories import (
    gen_image,
    make_client,
    make_ingest_service,
    make_user_client,
)
from tests.factories.db import (
    insert_link_item,
    insert_pic_item,
    insert_text_item,
    insert_user,
)


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


OrchEnv = tuple[IngestOrchestrator, SqliteRepository, FilesystemStorage]


@pytest.fixture
def t_orch_env(
    t_repo, t_store
) -> tuple[IngestOrchestrator, SqliteRepository, FilesystemStorage]:
    """Orchestrator wired to t_repo and t_store.

    Depends on t_repo, t_store. Returns
    (orchestrator, repo, store) for ingest integration
    tests that need to inspect side effects.
    """
    service = make_ingest_service()
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
    client = make_client(tmp_path)
    assert client is not None
    return client


@pytest.fixture
def t_user(tmp_path) -> TestClient:
    """TestClient with a seeded user and an active session.
    The authenticated counterpart to t_client. Flavor headers
    (browser, htmx) are applied per request, not baked into the
    client.
    """
    return make_user_client(tmp_path)


@pytest.fixture
def t_browser(tmp_path) -> TestClient:
    """Bare TestClient with Accept: text/html and empty database and storage.
    App is fully wired (DB initialized, store directory created)
    but contains no items. Use for browser-context tests where the
    test creates its own content. Wraps the same app as make_client
    with default browser headers.
    Depends on pytest builtin fixture: tmp_path for isolated filesystem.
    """
    client = make_client(tmp_path)
    return TestClient(client.app, headers={"Accept": "text/html"})


@pytest.fixture
def t_htmx(tmp_path) -> TestClient:
    """Bare TestClient with HX-Request header and empty database and storage.
    App is fully wired (DB initialized, store directory created)
    but contains no items. Use for HTMX partial response tests
    where the test creates its own content.
    Depends on pytest builtin fixture: tmp_path for isolated filesystem.
    """
    client = make_client(tmp_path)
    return TestClient(client.app, headers={"HX-Request": "true"})


@pytest.fixture
def t_noreraise(tmp_path) -> TestClient:
    """TestClient that surfaces the app's 500 instead of re-raising.

    Mirrors t_client but with raise_server_exceptions=False, so the
    app-level boundary handler's response is observable rather than
    propagated as an exception. Select surface per-request via Accept
    or HX-Request headers.
    Depends on pytest builtin fixture: tmp_path for isolated filesystem.
    """
    client = make_client(tmp_path)
    return TestClient(client.app, raise_server_exceptions=False)


@dataclass(frozen=True)
class SeededApp:
    """TestClient bundled with pre-populated items.

    Contains one of each item kind (text, pic, link) seeded
    via repo and store directly. No upload round-trip.
    Use for GET/info/raw tests where content is a precondition.
    Access item fields (code, hash_full, etc.) for assertions.
    """

    client: TestClient
    browser: TestClient
    htmx: TestClient
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
    head_html, head_htmx = {"Accept": "text/html"}, {"HX-Request": "true"}
    client = make_client(tmp_path)
    browser = TestClient(client.app, headers=head_html)
    htmx = TestClient(client.app, headers={**head_html, **head_htmx})
    app = cast(FastAPI, client.app)
    conn = app.state.repo._conn
    store: FilesystemStorage = app.state.store

    txt_data = b"# Hello, World!\n**This** is a test `TextItem`."
    pic_data = gen_image("jpeg", 320, 240)
    link_url = "https://example.com"

    item_txt = insert_text_item(conn, size_b=len(txt_data))
    item_pic = insert_pic_item(conn, size_b=len(pic_data))
    item_link = insert_link_item(conn, size_b=len(link_url.encode()))

    store.put(code=item_txt.code, format=item_txt.format, source_bytes=txt_data)
    store.put(code=item_pic.code, format=item_pic.format, source_bytes=pic_data)
    return SeededApp(client, browser, htmx, item_txt, item_pic, item_link)


@dataclass
class AuthedApp:
    """TestClient bundled with a seeded user and known plaintext password.
    Use for login/logout tests where a real user credential is a precondition."""

    client: TestClient
    user: User
    password: str


@pytest.fixture
def t_authed(tmp_path) -> AuthedApp:
    """TestClient with a single user seeded with a real scrypt hash."""
    client, pw = make_client(tmp_path), "test-password"
    user = insert_user(
        conn=cast(FastAPI, client.app).state.repo._conn,
        email="guy@example.com",
        pw_hash=hash_password(pw, n=2, r=1, p=1),
    )
    return AuthedApp(client=client, user=user, password=pw)


@pytest.fixture
def t_logged_in(t_authed: AuthedApp) -> TestClient:
    """TestClient with an active session for a seeded user.
    Composes t_authed, then performs a real login so the client
    carries a valid session cookie. Use for tests exercising
    auth-gated routes as an authenticated user.
    """
    data = {"email": t_authed.user.email, "password": t_authed.password}
    t_authed.client.post("/login", data=data)
    return t_authed.client
