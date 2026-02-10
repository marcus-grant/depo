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


