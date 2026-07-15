# tests/factories/__init__.py
"""
Test factories.

Reusable builders for test objects. Submodules hold
specialized factories (models, payloads, db). Common
helpers live here directly.

Author: Marcus Grant
Created: 2026-02-05
License: Apache-2.0
"""

from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

from bs4 import BeautifulSoup as BSoup
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from depo.cli import defaults
from depo.cli.config import DepoConfig
from depo.model.enums import ContentFormat, ItemKind, Visibility
from depo.model.item import LinkItem, PicItem, TextItem
from depo.service.ingest import IngestService
from depo.service.orchestrator import PersistResult
from depo.util.password import hash_password
from depo.web.app import app_factory
from depo.web.templates import get_templates

from .db import insert_user
from .models import (
    make_item,
    make_link_item,
    make_pic_item,
    make_text_item,
    make_write_plan,
)
from .payloads import gen_image

# TODO: Reorganize this mess of factories

__all__ = [
    "HEADER_BROWSER",
    "HEADER_HTMX",
    "gen_image",
    "make_client",
    "make_user_client",
    "make_config",
    "make_item",
    "make_link_item",
    "make_persist_result",
    "make_pic_item",
    "make_probe_client",
    "make_request",
    "make_text_item",
    "make_write_plan",
]

HEADER_BROWSER = {"Accept": "text/html"}
HEADER_HTMX = {**HEADER_BROWSER, "HX-Request": "true"}


def make_config(p: Path, **overrides: Any) -> DepoConfig:
    """Build a DepoConfig with db and store paths under p.
    Typically called with pytest's tmp_path fixture.
    Creates paths at p/data/depo.db and p/store but does
    not initialize the database or create directories.
    Keyword overrides replace any default field on the returned config.
    Used internally by make_client.
    """
    base = {
        "db_path": p / "data" / "depo.db",
        "store_root": p / "store",
        "session_secret": "test-session-secret",
    }
    return DepoConfig(**{**base, **overrides})


def make_ingest_service(**overrides: int) -> IngestService:
    """Build an IngestService with default limits, overridable per test."""
    params: dict[str, int] = {
        "min_code_len": defaults.MIN_CODE_LEN,
        "max_size_bytes": defaults.MAX_SIZE_BYTES,
        "max_url_len": defaults.MAX_URL_LEN,
    }
    params.update(overrides)
    return IngestService(**params)


def make_client(p: Path, **overrides) -> TestClient:
    """Build a full-stack TestClient rooted at p.
    Wraps make_config and app_factory. Config overrides are
    forwarded to make_config. The app initializes its own DB
    and storage from the config paths. Use for integration
    tests against real routes. Prefer the t_client fixture
    unless you need a custom path or config.
    """
    return TestClient(app_factory(make_config(p, **overrides)))


def make_user_client(p: Path, **overrides) -> TestClient:
    """Build a full-stack TestClient with a seeded user and active session.
    The authenticated counterpart to make_client. Config overrides are
    forwarded to make_config. Flavor headers (browser, htmx) are applied
    per request, not baked into the client.
    """
    client = make_client(p, **overrides)
    pw, conn = "test-password", cast(FastAPI, client.app).state.repo._conn
    pw_hash, email = hash_password(pw, n=2, r=1, p=1), "guy@example.com"
    insert_user(conn, email=email, pw_hash=pw_hash)
    client.post("/login", data={"email": email, "password": pw})
    return client


def make_probe_client(probe_fn: Callable[[Request], Any]) -> TestClient:
    """Build a minimal app with a single GET /probe route.

    No database, storage, or config. probe_fn receives the
    Request and its return value becomes the JSON response.
    Use for testing middleware behavior (content negotiation,
    HTMX detection) in isolation from the full app.
    """
    app = FastAPI()

    @app.get("/probe")
    def _probe(request: Request):
        return probe_fn(request)

    _ = _probe  # satisfy linters

    return TestClient(app)


def make_full_probe_client(path: Path, probe_fn: Callable[..., Any]) -> TestClient:
    """Build a full-stack app with a single GET /test/probe route.
    Wraps app_factory and make_config, so the probe runs behind
    the real middleware stack and registered exception handlers.
    Use for testing wired app behavior (session, auth boundary)
    that make_probe_client's bare app cannot exercise.
    """
    app = app_factory(make_config(path))
    app.add_api_route("/test/probe", probe_fn, methods=["GET"])
    return TestClient(app)


def make_persist_result(
    *,
    item: TextItem | PicItem | LinkItem | None = None,
    created: bool = True,
) -> PersistResult:
    """Build a PersistResult for route-level unit tests.

    No database or storage involved. Supplies a default
    TextItem when item is None. Use for testing handlers
    that receive orchestrator output without running the
    full ingest pipeline.
    """
    if item is None:
        item = TextItem(
            hash_full="0123456789ABCDEFGHJKMNPQ",
            code="01234567",
            kind=ItemKind.TEXT,
            size_b=99,
            uid=0,
            perm=Visibility.PUBLIC,
            upload_at=123456789,
            origin_at=None,
            format=ContentFormat.PLAINTEXT,
        )
    return PersistResult(item=item, created=created)


def make_request(path: str = "/test", method: str = "GET") -> Request:
    """Build a minimal Starlette Request stub for template rendering tests."""
    scope = {
        "type": "http",
        "method": method,
        "path": path,
        "query_string": b"",
        "headers": [],
    }
    return Request(scope)


def render_template(name: str, ctx: dict | None = None) -> "BSoup":
    """Render a Jinja2 template by name with context, return parsed soup."""

    html = get_templates().env.get_template(name).render(**(ctx or {}))
    return BSoup(html, "html.parser")
