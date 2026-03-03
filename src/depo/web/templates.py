# src/depo/web/templates.py
"""
Template rendering utilities.
Jinja2 setup and HTMX-aware response helpers.
Author: Marcus Grant
Created: 2026-02-12
License: Apache-2.0
"""

from pathlib import Path

from starlette.requests import Request
from starlette.templating import Jinja2Templates

from depo.model.formats import extension_for_format


def is_htmx(request: Request) -> bool:
    """Check if request originated from HTMX (HX-Request header)."""
    return request.headers.get("HX-Request") == "true"


def get_templates() -> Jinja2Templates:
    """Build Jinja2Templates instance pointing at the templates directory."""
    templates = Jinja2Templates(directory=Path(__file__).parent.parent / "templates")
    templates.env.filters["ext"] = extension_for_format
    return templates
