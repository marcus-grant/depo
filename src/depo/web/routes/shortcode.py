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
from depo.repo.sqlite import SqliteRepository
from depo.storage.protocol import StorageBackend
from depo.util.errors import (
    DepoError,
    ExtensionMismatchError,
    LinkRawNotSupportedError,
    UnknownServerError,
)
from depo.web.deps import get_repo, get_storage
from depo.web.error import api_error, browser_error
from depo.web.negotiate import wants_html
from depo.web.templates import get_templates, is_htmx

shortcode_router = APIRouter()  # Initialize router


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


@shortcode_router.get("/{code}.{ext}")
async def raw_ext(
    code: str,
    ext: str,
    repo: SqliteRepository = Depends(get_repo),
    store: StorageBackend = Depends(get_storage),
) -> Response:
    """Return raw content for the given code. Extension must match item format."""
    try:
        item = selector.get_item(repo, code)
        if isinstance(item, LinkItem):
            raise LinkRawNotSupportedError(code)
        if (expect := extension_for_format(item.format)) != ext:
            raise ExtensionMismatchError(code, expect, ext)
        return _serve_item_content(item, store)
    except DepoError as e:
        return api_error(e)


@shortcode_router.get("/{code}")
async def item(req: Request, code: str) -> Response:
    """Redirect shortcut to canonical route based on client type."""
    if is_htmx(req) or wants_html(req):
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
    if is_htmx(req) or wants_html(req):
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
    except DepoError as e:
        return api_error(e)
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
        ctx: dict = {"request": req, "item": item}
        if isinstance(item, LinkItem):
            name = "info/link.html"
        elif isinstance(item, TextItem):
            name = "info/text.html"
            ctx["content"] = selector.get_raw(store, item).read()
        elif isinstance(item, PicItem):
            name = "info/pic.html"
        else:
            raise UnknownServerError(context={"code": code})
        return get_templates().TemplateResponse(
            request=req, name=name, status_code=200, context=ctx
        )
    except DepoError as e:
        return browser_error(req, e)


@shortcode_router.get("/{code}/raw")
async def raw(
    code: str,
    repo: SqliteRepository = Depends(get_repo),
    store: StorageBackend = Depends(get_storage),
) -> Response:
    """Return raw content for the given code."""
    try:
        item = selector.get_item(repo, code)
    except DepoError as e:
        return api_error(e)
    if isinstance(item, LinkItem):
        return RedirectResponse(item.url, status_code=307)
    return _serve_item_content(item, store)
