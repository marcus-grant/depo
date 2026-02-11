# src/depo/web/routes.py
"""
Route handlers for depo API.

All routes registered on an APIRouter, included
by the app factory.

Author: Marcus Grant
Created: 2026-02-09
License: Apache-2.0
"""

import dataclasses

from fastapi import APIRouter, Depends, Request, UploadFile
from fastapi.responses import PlainTextResponse, RedirectResponse, Response

import depo.service.selector as selector
from depo.model.formats import mime_for_format
from depo.model.item import LinkItem, PicItem, TextItem
from depo.repo.errors import NotFoundError
from depo.repo.sqlite import SqliteRepository
from depo.service.orchestrator import IngestOrchestrator
from depo.storage.protocol import StorageBackend
from depo.web.deps import get_orchestrator, get_repo, get_storage
from depo.web.upload import execute_upload

router = APIRouter()


@router.get("/health")
def health() -> PlainTextResponse:
    """Return plain text health check for liveness probes."""
    return PlainTextResponse(content="ok", status_code=200)


@router.post("/api/upload", status_code=201)
@router.post("/upload", status_code=201)
@router.post("/", status_code=201)
async def upload(
    req: Request,
    orch: IngestOrchestrator = Depends(get_orchestrator),
    url: str | None = None,
    file: UploadFile | None = None,
) -> PlainTextResponse:
    """Accept content via multipart, raw body, or URL param."""
    if file is not None:
        return await execute_upload(file, url, None, orch)
    if url is not None:
        return await execute_upload(None, url, None, orch)
    return await execute_upload(None, None, req, orch)


@router.get("/api/{code}/info")
async def get_info(  # TODO: This needs proper JSON serialization later
    code: str,
    repo: SqliteRepository = Depends(get_repo),
) -> PlainTextResponse:
    """Return item metadata for the given code."""
    try:
        item = selector.get_item(repo, code)
    except NotFoundError as e:
        return PlainTextResponse(content=str(e), status_code=404)
    lines = [f"{f.name}={getattr(item, f.name)}" for f in dataclasses.fields(item)]
    body = "\n".join(lines)
    return PlainTextResponse(content=body)


@router.get("/api/{code}/raw")
async def get_raw(
    code: str,
    repo: SqliteRepository = Depends(get_repo),
    store: StorageBackend = Depends(get_storage),
) -> Response:
    """Return raw content for the given code."""
    try:
        item = selector.get_item(repo, code)
    except NotFoundError as e:
        return PlainTextResponse(content=str(e), status_code=404)
    if isinstance(item, LinkItem):
        return RedirectResponse(item.url, status_code=307)
    data = selector.get_raw(store, item)
    if isinstance(item, TextItem):
        return Response(content=data.read(), media_type="text/plain; charset=utf-8")
    if isinstance(item, PicItem):
        return Response(content=data.read(), media_type=mime_for_format(item.format))
    return PlainTextResponse("Unexpected item type", status_code=500)
