# src/depo/web/routes.py
"""
Route handlers for depo API.

All routes registered on an APIRouter, included
by the app factory.

Author: Marcus Grant
Created: 2026-02-09
License: Apache-2.0
"""

from fastapi import APIRouter, Depends, Request, UploadFile
from fastapi.responses import PlainTextResponse

from depo.service.orchestrator import IngestOrchestrator
from depo.web.deps import get_orchestrator
from depo.web.upload import execute_upload

router = APIRouter()


@router.get("/health")
def health() -> PlainTextResponse:
    """Return plain text health check for liveness probes."""
    return PlainTextResponse(content="ok", status_code=200)


@router.post("/api/upload", status_code=201)
async def upload(
    req: Request,
    orch: IngestOrchestrator = Depends(get_orchestrator),  # noqa: B008
    url: str | None = None,
    file: UploadFile | None = None,
) -> PlainTextResponse:
    """Accept content via multipart, raw body, or URL param."""
    if file is not None:
        return await execute_upload(file, url, None, orch)
    if url is not None:
        return await execute_upload(None, url, None, orch)
    return await execute_upload(None, None, req, orch)
