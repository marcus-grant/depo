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

from depo.util.errors import AuthRequiredError, DepoError, UnknownServerError
from depo.web.negotiate import wants_html
from depo.web.templates import get_templates as _get
from depo.web.templates import is_htmx

_ISSUES_URL = "https://github.com/marcus-grant/depo/issues"


def log_error(e: DepoError) -> None:
    """Emit one record on the module logger at the error's severity."""
    logging.getLogger(__name__).log(e.severity, e.message, exc_info=e.exception)


def unhandled(request: Request, exc: Exception) -> Response:
    """App-level boundary for non-DepoError exceptions.

    Wraps the exception as UnknownServerError and delegates to the
    surface-appropriate builder. Does not log: the builders log.
    """
    err = UnknownServerError(exc)
    if is_htmx(request):
        return htmx_error(request, err)
    if wants_html(request):
        return browser_error(request, err)
    return api_error(err)


def auth_required(request: Request, exc: Exception) -> Response:
    """Surface-appropriate response for an AuthRequiredError reaching the boundary.
    Dispatches to the htmx, browser, or api builder by request type,
    passing the error through at its own 401 status rather than wrapping
    it as UnknownServerError.
    """
    assert isinstance(exc, AuthRequiredError)
    if is_htmx(request):
        return htmx_error(request, exc)
    if wants_html(request):
        return browser_error(request, exc)
    return api_error(exc)


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
