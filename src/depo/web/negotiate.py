# src/depo/web/negotiate.py
"""
Content negotiation utilities.
Determines client type from Accept header to dispatch
shortcut routes to the correct canonical endpoint.
Author: Marcus Grant
Created: 2026-02-12
License: Apache-2.0
"""

from starlette.requests import Request


def wants_html(request: Request) -> bool:
    """Does the client prefer an HTML response (browser vs API/CLI)?"""
    if "text/html" in request.headers.get("Accept", ""):
        return True
    return False
