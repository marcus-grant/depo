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

from fastapi import APIRouter, Depends, Query, Request, UploadFile
from fastapi.responses import PlainTextResponse, RedirectResponse, Response

import depo.service.selector as selector
from depo.model.enums import ContentFormat
from depo.model.formats import mime_for_format
from depo.model.item import LinkItem, PicItem, TextItem
from depo.repo.errors import NotFoundError
from depo.repo.sqlite import SqliteRepository
from depo.service.orchestrator import IngestOrchestrator
from depo.storage.protocol import StorageBackend
from depo.util.errors import PayloadTooLargeError
from depo.web.deps import get_orchestrator, get_repo, get_storage
from depo.web.negotiate import wants_html
from depo.web.templates import get_templates
from depo.web.upload import ingest_upload, parse_form_upload, upload_response

router = APIRouter()
_templates = get_templates()  # Preload templates for route handlers


def _response_404(req: Request, code: str, e: Exception) -> Response:
    return _templates.TemplateResponse(
        request=req,
        name="errors/404.html",
        status_code=404,
        context={"code": code, "error": str(e)},
    )


def _response_500(req: Request, detail: str) -> Response:
    """Return a 500 response with debug context."""
    return _templates.TemplateResponse(
        request=req,
        name="errors/500.html",
        status_code=500,
        context={
            "message": "Something went wrong",
            "path": req.url.path,
            "method": req.method,
            "detail": detail,
            "issues_url": "https://github.com/marcus-grant/depo/issues",
        },
    )


@router.get("/")
async def root_redirect():
    """Redirect root to canonical upload page."""
    return RedirectResponse(url="/upload", status_code=302)


@router.get("/upload")
async def upload_page(req: Request):
    """Serve the upload form as a full HTML page."""
    return get_templates().TemplateResponse(request=req, name="upload.html")


@router.post("/upload")
async def upload_form(
    req: Request,
    orch: IngestOrchestrator = Depends(get_orchestrator),
):
    """Browser form upload: textarea content + format override."""
    templates = get_templates()
    try:
        params = await parse_form_upload(req)
        result = orch.ingest(**dict(params))  # type: ignore[arg-type]
    except PayloadTooLargeError as e:
        return _templates.TemplateResponse(
            request=req,
            name="partials/error.html",
            context={"error": str(e)},
            status_code=413,
        )
    except (ValueError, ImportError) as e:
        return _templates.TemplateResponse(
            request=req,
            name="partials/error.html",
            context={"error": str(e)},
        )
    return templates.TemplateResponse(
        request=req,
        name="partials/success.html",
        context={"code": result.item.code, "created": result.created},
    )


@router.post("/api/upload", status_code=201)
@router.post("/", status_code=201)
async def upload(
    req: Request,
    orch: IngestOrchestrator = Depends(get_orchestrator),
    url: str | None = None,
    file: UploadFile | None = None,
    fmt: str | None = Query(None, alias="format"),
) -> PlainTextResponse:
    """API upload: multipart, raw body, or URL param."""
    req_fmt_str = fmt or req.headers.get("x-depo-format")
    req_fmt = ContentFormat(req_fmt_str) if req_fmt_str else None
    try:
        result = await ingest_upload(file, url, req, orch, req_fmt=req_fmt)
    except PayloadTooLargeError as e:
        return PlainTextResponse(str(e), status_code=413)
    except ValueError as e:
        return PlainTextResponse(str(e), status_code=400)
    except ImportError as e:
        return PlainTextResponse(str(e), status_code=501)
    return upload_response(result)


@router.get("/health")
def health() -> PlainTextResponse:
    """Return plain text health check for liveness probes."""
    return PlainTextResponse(content="ok", status_code=200)


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


@router.get("/{code}/info")
async def info_page(
    req: Request,
    code: str,
    repo: SqliteRepository = Depends(get_repo),
    store: StorageBackend = Depends(get_storage),
) -> Response:
    """Serve HTML info view, template selected by item kind."""
    try:
        item = selector.get_item(repo, code)
    except NotFoundError as e:
        return _response_404(req, code, e)
    if isinstance(item, LinkItem):
        return _templates.TemplateResponse(
            request=req,
            status_code=200,
            name="info/link.html",
            context={"request": req, "item": item},
        )
    if isinstance(item, TextItem):
        content = selector.get_raw(store, item).read()
        return _templates.TemplateResponse(
            request=req,
            status_code=200,
            name="info/text.html",
            context={"request": req, "item": item, "content": content},
        )
    if isinstance(item, PicItem):
        return _templates.TemplateResponse(
            request=req,
            status_code=200,
            name="info/pic.html",
            context={"request": req, "item": item},
        )
    return _response_500(req, f"Unexpected item type for code {code}")


@router.get("/{code}")
async def shortcut(req: Request, code: str) -> Response:
    """Redirect shortcut to canonical route based on client type."""
    if wants_html(req):
        return RedirectResponse(url=f"/{code}/info", status_code=302)
    return RedirectResponse(url=f"/api/{code}/raw", status_code=302)
