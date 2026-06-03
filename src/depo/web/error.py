# src/depo/web/error.py
"""
Web layer error response builders.
Author: Marcus Grant
Created: 2026-03-12
License: Apache-2.0
"""

import logging

from fastapi import Request
from starlette.responses import PlainTextResponse, Response

from depo.util.errors import DepoError
from depo.web.templates import get_templates as _get

_ISSUES_URL = "https://github.com/marcus-grant/depo/issues"


def log_error(e: DepoError) -> None:
    """Emit one record on the module logger at the error's severity."""
    logging.getLogger(__name__).log(e.severity, e.message, exc_info=e.exception)


def api_error(err: DepoError) -> PlainTextResponse:
    """Return a PlainTextResponse for API clients."""
    log_error(err)
    return PlainTextResponse(str(err), status_code=err.status)


def browser_error(req: Request, err: DepoError) -> Response:
    """Return a full-page error TemplateResponse for browser clients."""
    log_error(err)
    return _get().TemplateResponse(
        request=req,
        name="errors/page.html",
        status_code=err.status,
        context={"error": err, "issues_url": _ISSUES_URL},
    )


def htmx_error(req: Request, err: DepoError, role: str = "alert") -> Response:
    """Return an HTMX partial TemplateResponse, always at HTTP 200."""
    log_error(err)
    return _get().TemplateResponse(
        request=req,
        name="errors/partial.html",
        status_code=200,
        context={"error": err, "role": role},
    )
