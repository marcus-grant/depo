# src/depo/web/routes.py
"""
Route handlers for depo API.

All routes registered on an APIRouter, included
by the app factory.

Author: Marcus Grant
Created: 2026-02-09
License: Apache-2.0
"""

import re

from fastapi import APIRouter, Depends, Request, UploadFile
from fastapi.responses import PlainTextResponse

from depo.service.orchestrator import IngestOrchestrator
from depo.web.deps import get_orchestrator

router = APIRouter()


@router.get("/health")
def health() -> PlainTextResponse:
    """Return plain text health check for liveness probes."""
    return PlainTextResponse(content="ok", status_code=200)


# TODO: This belongs in the right place in ingestion pipeline, probably classify
# Don't forget to move its test class TestLooksLikeUrl as well

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
