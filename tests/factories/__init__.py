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
    """Build a DepoConfig with paths under p."""
    return DepoConfig(db_path=p / "data" / "depo.db", store_root=p / "store")


def make_client(p: Path) -> TestClient:
    """Build a TestClient from a DepoConfig pointing at tmp_path."""
    return TestClient(app_factory(make_config(p)))


def make_probe_client(probe_fn: Callable[[Request], Any]) -> TestClient:
    """Build a minimal test app with a single GET /probe route.
    probe_fn receives the Request, its return value becomes the response.
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
    """Build a PersistResult with sensible defaults."""
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
