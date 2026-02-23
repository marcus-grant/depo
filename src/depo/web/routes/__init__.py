# src/depo/web/routes/__init__.py
"""
Route wiring for depo web layer.
Includes domain routers and registers fixed-path
handlers (health, redirects). Domain handlers live
in their own modules under this package.

Author: Marcus Grant
Created: 2026-02-23
License: Apache-2.0
"""

import dataclasses

from fastapi import APIRouter, Depends, Request
from fastapi.responses import PlainTextResponse, RedirectResponse, Response

import depo.service.selector as selector
from depo.model.formats import mime_for_format
from depo.model.item import LinkItem, PicItem, TextItem
from depo.repo.errors import NotFoundError
from depo.repo.sqlite import SqliteRepository
from depo.storage.protocol import StorageBackend
from depo.web.deps import get_repo, get_storage
from depo.web.negotiate import wants_html
from depo.web.routes.upload import upload_router
from depo.web.templates import get_templates

# Merge routers from domain-specific modules
router = APIRouter()
router.include_router(upload_router)  # Upload routes
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


@router.get("/health")
def health() -> PlainTextResponse:
    """Return plain text health check for liveness probes."""
    return PlainTextResponse(content="ok", status_code=200)


@router.get("/{code}/info")
async def info(
    req: Request,
    code: str,
    repo: SqliteRepository = Depends(get_repo),
    store: StorageBackend = Depends(get_storage),
) -> Response:
    """Dispatcher for item info by content negotiation.
    Delegates to page_info for browser requests,
    api_info for API/CLI requests.
    """
    if wants_html(req):
        return await page_info(req, code, repo, store)
    return await api_info(code, repo)


# TODO: Needs proper JSON/plaintxt serialization later
async def api_info(
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


@router.get("/{code}/raw")
async def raw(
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


async def page_info(
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
async def item(req: Request, code: str) -> Response:
    """Redirect shortcut to canonical route based on client type."""
    if wants_html(req):
        return RedirectResponse(url=f"/{code}/info", status_code=302)
    return RedirectResponse(url=f"/{code}/raw", status_code=302)
