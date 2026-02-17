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
from typing import Any

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from depo.cli.config import DepoConfig
from depo.model.enums import ContentFormat, ItemKind, Visibility
from depo.model.item import LinkItem, PicItem, TextItem
from depo.service.orchestrator import PersistResult
from depo.web.app import app_factory

from .models import (
    make_item,
    make_link_item,
    make_pic_item,
    make_text_item,
    make_write_plan,
)
from .payloads import gen_image

__all__ = [
    "gen_image",
    "make_client",
    "make_config",
    "make_item",
    "make_link_item",
    "make_persist_result",
    "make_pic_item",
    "make_probe_client",
    "make_text_item",
    "make_write_plan",
]


def make_config(p: Path) -> DepoConfig:
    """Build a DepoConfig with db and store paths under p.

    Typically called with pytest's tmp_path fixture.
    Creates paths at p/data/depo.db and p/store but does
    not initialize the database or create directories.
    Used internally by make_client.
    """
    return DepoConfig(db_path=p / "data" / "depo.db", store_root=p / "store")


def make_client(p: Path) -> TestClient:
    """Build a full-stack TestClient rooted at p.

    Wraps make_config and app_factory. The app initializes
    its own DB and storage from the config paths. Use for
    integration tests against real routes. Prefer the
    t_client fixture unless you need a custom path.
    """
    return TestClient(app_factory(make_config(p)))


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
