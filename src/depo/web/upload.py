# src/depo/web/upload.py
"""
Upload request parsing and response building.

Extracts orchestrator kwargs from HTTP requests and
maps ingest results to HTTP responses.

Author: Marcus Grant
Created: 2026-02-10
License: Apache-2.0
"""

import re
from typing import TypedDict

from fastapi import Request, UploadFile
from fastapi.responses import PlainTextResponse

from depo.service.orchestrator import PersistResult

# TODO: This belongs in the right place in ingestion pipeline, probably classify
# Don't forget to move its test class TestLooksLikeUrl as well
# TODO: This remains after migration, regex is a brittle way of text validating a URL

_URL_RE = re.compile(
    r"^https?://[^\s<>{}\[\]]+\.[^\s<>{}\[\]]{1,8}([/?#][^\s<>{}\[\]]*)?$"
)


def _looks_like_url(data: bytes) -> bool:
    """Naive URL detection. TODO: Move to ingestion pipeline."""
    try:
        text = data.decode("utf-8").strip()
    except UnicodeDecodeError:
        return False
    return bool(_URL_RE.match(text))


class UploadMultipartParams(TypedDict):
    """Upload params from multipart file submission."""

    payload_bytes: bytes
    filename: str
    declared_mime: str


class UploadUrlParams(TypedDict):
    """Upload params from URL query parameter or detected link."""

    link_url: str


class UploadRawBodyParams(TypedDict):
    """Upload params from raw request body."""

    payload_bytes: bytes
    declared_mime: str


# NOTE: Have a subset of UploadParamas for each upload situation and union them
UploadParams = UploadMultipartParams | UploadUrlParams | UploadRawBodyParams


async def parse_upload(
    file: UploadFile | None,
    url: str | None,
    request: Request | None,
) -> UploadParams:
    """Extract orchestrator.ingest kwargs from an HTTP request."""
    if request is not None:
        body = await request.body()
        if _looks_like_url(body):
            return UploadUrlParams(link_url=body.decode("utf-8").strip())
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
        return UploadUrlParams(link_url=url)
    raise ValueError(
        "parse_upload called with no input: file, url, and request are all None. "
        "This is a routing bug — at least one must be provided."
    )


def upload_response(result: PersistResult) -> PlainTextResponse:
    """Build HTTP response from a PersistResult."""
    raise NotImplementedError
