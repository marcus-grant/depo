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
from fastapi.responses import HTMLResponse, PlainTextResponse

from depo.model.enums import ContentFormat
from depo.service.orchestrator import IngestOrchestrator, PersistResult
from depo.util.errors import PayloadTooLargeError
from depo.web.deps import get_orchestrator
from depo.web.templates import get_templates, is_htmx

upload_router = APIRouter()
_templates = get_templates()  # Preload templates for route handlers


@upload_router.get("/upload")
async def page_upload(req: Request):
    """Serve the upload form as a full HTML page."""
    return get_templates().TemplateResponse(request=req, name="upload.html")


@upload_router.post("/upload", status_code=201)
@upload_router.post("/", status_code=201)  # Alias for convenience
async def upload(
    req: Request,
    orch: IngestOrchestrator = Depends(get_orchestrator),
    url: str | None = None,
    file: UploadFile | None = None,
    fmt: str | None = Query(None, alias="format"),
) -> Response:
    """Dispatcher for uploads by content negotiation.
    Delegates to hx_upload for HTMX requests, api_upload for API requests."""
    if is_htmx(req):
        return await hx_upload(req, orch)
    return await api_upload(req, orch=orch, url=url, file=file, fmt=fmt)


async def hx_upload(
    req: Request,
    orch: IngestOrchestrator = Depends(get_orchestrator),
) -> HTMLResponse:
    """Browser form upload: textarea content + format override."""
    templates = get_templates()
    try:
        params = await _parse_form_upload(req)
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


async def api_upload(
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
        result = await _ingest_upload(file, url, req, orch, req_fmt=req_fmt)
    except PayloadTooLargeError as e:
        return PlainTextResponse(str(e), status_code=413)
    except ValueError as e:
        return PlainTextResponse(str(e), status_code=400)
    except ImportError as e:
        return PlainTextResponse(str(e), status_code=501)
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
        body = await request.body()
        return UploadRawBodyParams(
            payload_bytes=body,
            declared_mime=str(request.headers.get("content-type")),
        )
    if file is not None:
        return UploadMultipartParams(
            payload_bytes=(await file.read()),
            filename=(str(file.filename)),
            declared_mime=(str(file.content_type)),
        )
    if url is not None:
        kwargs = {"payload_bytes": url.encode("utf-8"), "declared_mime": None}
        return UploadRawBodyParams(**kwargs)
    raise ValueError(
        "parse_upload called with no input: file, url, and request are all None. "
        "This is a routing bug — at least one must be provided."
    )


async def _parse_form_upload(
    req: Request,
) -> UploadFormParams:
    """Extract orchestrator.ingest kwargs from browser form submission."""
    form = await req.form()
    content = str(form.get("content", "")).strip()
    fmt = str(form.get("format", ""))
    if not content:
        raise ValueError("No content provided.")
    return UploadFormParams(
        payload_bytes=content.encode("utf-8"),
        declared_mime="text/plain",
        requested_format=ContentFormat(fmt) if fmt else None,
    )


def _upload_response(result: PersistResult) -> PlainTextResponse:
    """Build HTTP response from a PersistResult."""
    return PlainTextResponse(
        content=result.item.code,
        status_code=201 if result.created else 200,
        headers={
            "content-type": "text/plain",
            "X-Depo-Code": result.item.code,
            "X-Depo-Kind": str(result.item.kind),
            "X-Depo-Created": "true" if result.created else "false",
        },
    )


async def _ingest_upload(
    file: UploadFile | None,
    url: str | None,
    req: Request | None,
    orch: IngestOrchestrator,
    req_fmt: ContentFormat | None = None,
) -> PersistResult:
    """Parse request and ingest with IngestOrchestrator given.
    Raises ValueError/ImportError on failure."""
    req = None if file is not None or url is not None else req
    params = await _parse_upload(file=file, url=url, request=req)
    return orch.ingest(**dict(params), requested_format=req_fmt)  # type: ignore[arg-type]
