# src/depo/web/routes/shortcode.py
"""
Shortcode route handlers.
Owns shortcode router with content negotiation for item
dispatch, info views, and raw content retrieval.
Wildcard routes, must be registered last.
Author: Marcus Grant
Created: 2026-02-23
License: Apache-2.0
"""

import dataclasses

from fastapi import APIRouter, Depends, Request
from fastapi.responses import PlainTextResponse, RedirectResponse, Response

import depo.service.selector as selector
from depo.model.formats import extension_for_format, mime_for_format
from depo.model.item import LinkItem, PicItem, TextItem
from depo.repo.errors import NotFoundError
from depo.repo.sqlite import SqliteRepository
from depo.storage.protocol import StorageBackend
from depo.web.deps import get_repo, get_storage
from depo.web.negotiate import wants_html
from depo.web.templates import get_templates

shortcode_router = APIRouter()  # Initialize router
_templates = get_templates()  # Alias templates


# TODO: Extract to shared error response module (error handling PR)
#       Centralize with custom exceptions and standard response builders
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


def _get_item_or_404(
    code: str, repo: SqliteRepository
) -> LinkItem | TextItem | PicItem | Response:
    """Item lookup helper that returns a 404 response on NotFoundError.
    Otherwise it returns the found item (LinkItem, TextItem, or PicItem)."""
    try:
        item = selector.get_item(repo, code)
    except NotFoundError as e:
        return PlainTextResponse(content=str(e), status_code=404)
    return item


def _serve_item_content(item: TextItem | PicItem, store: StorageBackend) -> Response:
    """Builds a raw content response for a TextItem or PicItem.
    Args:
        item: The item (TextItem or PicItem) to build the response for.
        store: The storage backend to fetch the raw data from.
    Returns: Response object with raw content & appropriate MIME type"""
    data = selector.get_raw(store, item)
    if isinstance(item, TextItem):
        return Response(content=data.read(), media_type="text/plain; charset=utf-8")
    if isinstance(item, PicItem):
        mime = mime_for_format(item.format)
        return Response(content=data.read(), media_type=mime)
    return PlainTextResponse("Unexpected item type", status_code=500)  # pyright: ignore


@shortcode_router.get("/{code}.{ext}")
async def raw_ext(
    code: str,
    ext: str,
    repo: SqliteRepository = Depends(get_repo),
    store: StorageBackend = Depends(get_storage),
) -> Response:
    """Return raw content for the given code. Extension must match item format."""
    result = _get_item_or_404(code, repo)
    if isinstance(result, Response):
        return result
    if isinstance(result, LinkItem):
        return PlainTextResponse("Links do not support raw content.", status_code=404)
    if (expect := extension_for_format(result.format)) != ext:
        msg = f"Extension mismatch: expected .{expect}"
        return PlainTextResponse(msg, status_code=404)
    return _serve_item_content(result, store)


@shortcode_router.get("/{code}")
async def item(req: Request, code: str) -> Response:
    """Redirect shortcut to canonical route based on client type."""
    if wants_html(req):
        return RedirectResponse(url=f"/{code}/info", status_code=302)
    return RedirectResponse(url=f"/{code}/raw", status_code=302)


@shortcode_router.get("/{code}/info")
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

    ctx: dict = {"request": req, "item": item}

    if isinstance(item, LinkItem):
        name = "info/link.html"
    elif isinstance(item, TextItem):
        name = "info/text.html"
        ctx["content"] = selector.get_raw(store, item).read()
    elif isinstance(item, PicItem):
        name = "info/pic.html"
    else:
        return _response_500(req, f"Unexpected item type for code {code}")
    kwargs = {"request": req, "name": name, "status_code": 200, "context": ctx}
    return _templates.TemplateResponse(**kwargs)


@shortcode_router.get("/{code}/raw")
async def raw(
    code: str,
    repo: SqliteRepository = Depends(get_repo),
    store: StorageBackend = Depends(get_storage),
) -> Response:
    """Return raw content for the given code."""
    result = _get_item_or_404(code, repo)
    if isinstance(result, Response):
        return result
    if isinstance(result, LinkItem):
        return RedirectResponse(result.url, status_code=307)
    return _serve_item_content(result, store)
