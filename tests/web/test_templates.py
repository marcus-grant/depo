# tests/web/test_templates.py
"""
Tests for template rendering utilities.
Author: Marcus Grant
Created: 2026-02-12
License: Apache-2.0
"""

import jinja2
import pytest
from fastapi import FastAPI, Request
from starlette.testclient import TestClient

from depo.web.templates import get_templates, is_htmx


class TestIsHtmx:
    """HTMX request detection via HX-Request header.

    Uses a minimal test app with a single route that
    returns the result of is_htmx() as plain text.
    """

    def _make_app(self) -> TestClient:
        app = FastAPI()

        @app.get("/probe")
        def probe(request: Request):
            return {"htmx": is_htmx(request)}

        return TestClient(app)

    def test_true_when_header_present(self):
        client = self._make_app()
        resp = client.get("/probe", headers={"HX-Request": "true"})
        assert resp.json()["htmx"] is True

    def test_false_when_header_absent(self):
        client = self._make_app()
        resp = client.get("/probe")
        assert resp.json()["htmx"] is False


class TestGetTemplates:
    """Jinja2Templates instance configuration."""

    def test_can_locate_base_template(self):
        """Returned instance can locate base.html and known templates"""
        templates = get_templates()
        assert templates.get_template("base.html")  # Shouldn't raise TemplateNotFound

    def test_missing_template_raises(self):
        """Unknown template name raises TemplateNotFound."""
        templates = get_templates()
        with pytest.raises(jinja2.TemplateNotFound):
            templates.get_template("nope.html")
