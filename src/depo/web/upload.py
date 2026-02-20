# src/depo/web/upload.py
"""
Upload request parsing and response building.

Extracts orchestrator kwargs from HTTP requests and
maps ingest results to HTTP responses.

Author: Marcus Grant
Created: 2026-02-10
License: Apache-2.0
"""

from typing import TypedDict

from fastapi import Request, UploadFile
from fastapi.responses import PlainTextResponse

from depo.model.enums import ContentFormat
from depo.service.orchestrator import IngestOrchestrator, PersistResult


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


async def parse_upload(
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


async def parse_form_upload(
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


def upload_response(result: PersistResult) -> PlainTextResponse:
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


async def ingest_upload(
    file: UploadFile | None,
    url: str | None,
    req: Request | None,
    orch: IngestOrchestrator,
    req_fmt: ContentFormat | None = None,
) -> PersistResult:
    """Parse request and ingest with IngestOrchestrator given.
    Raises ValueError/ImportError on failure."""
    req = None if file is not None or url is not None else req
    params = await parse_upload(file=file, url=url, request=req)
    return orch.ingest(**dict(params), requested_format=req_fmt)  # type: ignore[arg-type]
