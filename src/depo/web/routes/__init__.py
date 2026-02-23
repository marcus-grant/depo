# src/depo/web/routes/__init__.py
"""
Route wiring for depo web layer.
Includes domain routers and registers fixed-path
handlers (health, redirects). Domain handlers live
in their own modules under this package.

Author: Marcus Grant
Created: 2026-02-23
License: Apache-2.0
"""

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse, RedirectResponse

from depo.web.routes.shortcode import shortcode_router
from depo.web.routes.upload import upload, upload_router

# Initialize the main router and merge domain routes AT END OF MODULE ONLY!!!
router = APIRouter()


@router.get("/")
async def root_redirect():
    """Redirect root to canonical upload page."""
    return RedirectResponse(url="/upload", status_code=302)


router.post("/", status_code=201)(upload)  # Alias for convenience


@router.get("/health")
def health() -> PlainTextResponse:
    """Return plain text health check for liveness probes."""
    return PlainTextResponse(content="ok", status_code=200)


# Merge routers from domain-specific modules
router.include_router(upload_router)  # Upload routes
router.include_router(shortcode_router)  # Shortcode routes (WILDCARDS MUST BE LAST!)
