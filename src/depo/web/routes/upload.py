# src/depo/web/routes/upload.py
"""
Upload route handlers and request helpers.
Owns upload router with content negotiation between
HTMX and API upload paths. Helpers parse multipart,
form, and raw body requests into orchestrator kwargs.

Author: Marcus Grant
Created: 2026-02-23
License: Apache-2.0
"""

from typing import TypedDict

from fastapi import APIRouter, Depends, Query, Request, Response, UploadFile
from fastapi.responses import PlainTextResponse, RedirectResponse
from starlette.datastructures import UploadFile as StarletteUploadFile

from depo.model.enums import ContentFormat
from depo.model.formats import format_for_extension
from depo.model.item import LinkItem
from depo.service.orchestrator import IngestOrchestrator, PersistResult
from depo.util import errors
from depo.web.deps import get_orchestrator, require_auth
from depo.web.error import api_error, browser_error, htmx_error
from depo.web.templates import get_templates, is_htmx

upload_router = APIRouter()


@upload_router.get("/upload")
async def page_upload(req: Request, _uid: int = Depends(require_auth)) -> Response:
    """Serve the upload form as a full HTML page."""
    _ = _uid  # Shut up LSPs that don't recognize FastAPI dependency injection
    return get_templates().TemplateResponse(request=req, name="upload/page.html")


@upload_router.post("/upload", status_code=201)
async def upload(
    req: Request,
    orch: IngestOrchestrator = Depends(get_orchestrator),
    uid: int = Depends(require_auth),
    url: str | None = None,
    file: UploadFile | None = None,
    fmt: str | None = Query(None, alias="format"),
) -> Response:
    """Dispatcher for uploads by content negotiation.
    Delegates to hx_upload for HTMX requests, api_upload for API requests."""
    url_encoded_head = "application/x-www-form-urlencoded"
    if is_htmx(req):
        return await hx_upload(req, uid, orch)
    if req.headers.get("content-type", "").startswith(url_encoded_head):
        try:
            params = await _parse_form_upload(req)
            result = orch.ingest(**dict(params), uid=uid)  # type: ignore
        except errors.DepoError as e:
            return browser_error(req, e)
        return RedirectResponse(f"/{result.item.code}/info", status_code=303)
    return await api_upload(req, uid, orch=orch, url=url, file=file, fmt=fmt)


async def hx_upload(
    request: Request,
    uid: int,
    orch: IngestOrchestrator = Depends(get_orchestrator),
) -> Response:
    """Browser form upload: textarea content + format override."""
    try:
        params = await _parse_form_upload(request)
        result = orch.ingest(**dict(params), uid=uid)  # type: ignore[arg-type]
        return get_templates().TemplateResponse(
            request=request,
            name="partials/success.html",
            status_code=200,
            context={"code": result.item.code, "created": result.created},
        )
    except errors.DepoError as e:
        return htmx_error(request, e)


async def api_upload(
    req: Request,
    uid: int,
    orch: IngestOrchestrator = Depends(get_orchestrator),
    url: str | None = None,
    file: UploadFile | None = None,
    fmt: str | None = Query(None, alias="format"),
) -> PlainTextResponse:
    """API upload: multipart, raw body, or URL param."""
    try:
        req_fmt_str = fmt or req.headers.get("x-depo-format")
        if req_fmt_str:
            req_fmt = format_for_extension(req_fmt_str)
            if req_fmt is None:
                raise errors.UnsupportedFormatError(req_fmt_str)
        else:
            req_fmt = None
        result = await _ingest_upload(file, url, req, orch, uid, req_fmt=req_fmt)
    except errors.DepoError as e:
        return api_error(e)
    return _upload_response(result)


class UploadMultipartParams(TypedDict):
    """Upload params from multipart file submission."""

    payload_bytes: bytes
    filename: str
    declared_mime: str


class UploadRawBodyParams(TypedDict):
    """Upload params from raw request body."""

    payload_bytes: bytes
    declared_mime: str | None


class UploadFormParams(TypedDict):
    """Upload params from browser form submission."""

    payload_bytes: bytes
    declared_mime: str
    filename: str | None
    requested_format: ContentFormat | None


# NOTE: Have a subset of UploadParamas for each upload situation and union them
UploadParams = UploadMultipartParams | UploadRawBodyParams | UploadFormParams


async def _parse_upload(
    file: UploadFile | None,
    url: str | None,
    request: Request | None,
) -> UploadParams:
    """Extract orchestrator.ingest kwargs from an HTTP request."""
    if request is not None:  # The URL endpoint has path/query meta to use
        body, mime = await request.body(), str(request.headers.get("content-type"))
        return UploadRawBodyParams(payload_bytes=body, declared_mime=mime)
    if file is not None:
        p, f, m = await file.read(), str(file.filename), str(file.content_type)
        kwargs = {"payload_bytes": p, "filename": f, "declared_mime": m}
        return UploadMultipartParams(**kwargs)
    if url is not None:
        kwargs = {"payload_bytes": url.encode("utf-8"), "declared_mime": None}
        return UploadRawBodyParams(**kwargs)
    raise errors.PayloadSourceError(sources=["file", "url", "request"])


async def _parse_form_upload(
    req: Request,
) -> UploadFormParams:
    """Extract orchestrator.ingest kwargs from browser form submission."""
    form = await req.form()
    content = str(form.get("content", "")).strip()
    file = form.get("file")
    fmt = str(form.get("format", ""))
    if fmt:
        _resolved = format_for_extension(fmt)
        if _resolved is None:
            raise errors.UnsupportedFormatError(fmt)
        requested_format: ContentFormat | None = _resolved
    else:
        requested_format = None
    if isinstance(file, StarletteUploadFile) and (data := await file.read()):
        return UploadFormParams(
            payload_bytes=data,
            declared_mime=file.content_type or "application/octet-stream",
            filename=file.filename,
            requested_format=requested_format,
        )
    if not content:
        raise errors.PayloadEmptyError
    return UploadFormParams(
        payload_bytes=content.encode("utf-8"),
        declared_mime="text/plain",
        filename=None,
        requested_format=requested_format,
    )


def _upload_response(result: PersistResult) -> PlainTextResponse:
    """Build HTTP response from a PersistResult."""
    # TODO: LinkItem lacks format field, special-cased here
    #       Investigate adding format to base Item or LinkItem (error handling PR)
    fmt = "url" if isinstance(result.item, LinkItem) else result.item.format.value
    return PlainTextResponse(
        content=result.item.code,
        status_code=201 if result.created else 200,
        headers={
            "content-type": "text/plain",
            "X-Depo-Code": result.item.code,
            "X-Depo-Kind": str(result.item.kind),
            "X-Depo-Format": fmt,
            "X-Depo-Created": "true" if result.created else "false",
        },
    )


async def _ingest_upload(
    file: UploadFile | None,
    url: str | None,
    req: Request | None,
    orch: IngestOrchestrator,
    uid: int,
    req_fmt: ContentFormat | None = None,
) -> PersistResult:
    """Parse request and ingest with IngestOrchestrator given.
    Raises some subclass of DepoError on failure."""
    req = None if file is not None or url is not None else req
    params = await _parse_upload(file=file, url=url, request=req)
    return orch.ingest(**dict(params), requested_format=req_fmt, uid=uid)  # type: ignore[arg-type]
