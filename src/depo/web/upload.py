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


async def parse_upload(
    file: UploadFile | None,
    url: str | None,
    request: Request,
) -> dict:
    """Extract orchestrator.ingest kwargs from an HTTP request."""
    raise NotImplementedError


def upload_response(result: PersistResult) -> PlainTextResponse:
    """Build HTTP response from a PersistResult."""
    raise NotImplementedError
