# src/depo/web/error.py
"""
Web layer error response builders.
Author: Marcus Grant
Created: 2026-03-12
License: Apache-2.0
"""

from fastapi import Request
from starlette.responses import PlainTextResponse, Response

from depo.util.errors import DepoError
from depo.web.templates import get_templates as _get

_ISSUES_URL = "https://github.com/marcus-grant/depo/issues"


def browser_error(req: Request, e: DepoError) -> Response:
    """Return a full-page error TemplateResponse for browser clients."""
    return _get().TemplateResponse(
        request=req,
        name="errors/page.html",
        status_code=e.status,
        context={"error": e, "issues_url": _ISSUES_URL},
    )


def api_error(e: DepoError) -> PlainTextResponse:
    """Return a PlainTextResponse for API clients."""
    return PlainTextResponse(str(e), status_code=e.status)


def htmx_error(e: DepoError, role: str = "alert") -> dict:
    """Return kwargs dict for HTMX partial TemplateResponse error renders."""
    return {"name": "errors/partial.html", "context": {"error": e, "role": role}}
