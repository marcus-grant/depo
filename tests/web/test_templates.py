# tests/web/test_templates.py
"""
Tests for template rendering utilities.
Author: Marcus Grant
Created: 2026-02-12
License: Apache-2.0
"""

import jinja2
import pytest
from bs4 import BeautifulSoup, Comment

from depo.web.templates import get_templates, is_htmx
from tests.factories import make_probe_client


class TestIsHtmx:
    """HTMX request detection via HX-Request header.

    Uses a minimal test app with a single route that
    returns the result of is_htmx() as plain text.
    """

    def test_true_when_header_present(self):
        client = make_probe_client(lambda r: {"htmx": is_htmx(r)})
        resp = client.get("/probe", headers={"HX-Request": "true"})
        assert resp.json()["htmx"] is True

    def test_false_when_header_absent(self):
        client = make_probe_client(lambda r: {"htmx": is_htmx(r)})
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


class TestBaseTemplate:
    """Base layout template renders correctly.

    # Content block renders outside HTML comments
    # Template markers (BEGIN/END) present
    # Static asset references present (pico, htmx, depo.css)
    """

    def _render(self, block_content: str = "") -> str:
        """Render base.html with a test string in the content block."""
        env = get_templates().env
        template = env.from_string(
            '{% extends "base.html" %}{% block content %}'
            + block_content
            + "{% endblock %}"
        )
        return template.render()

    def test_content_not_inside_comment(self):
        """Content block renders as real HTML, not inside a comment."""
        marker = "TESTBLOCK123"
        html = self._render(marker)
        soup = BeautifulSoup(html, "html.parser")
        # Marker should appear outside any HTML comment
        assert marker in html
        for comment in soup.find_all(string=lambda s: isinstance(s, Comment)):
            assert marker not in comment

    def test_template_markers_present(self):
        """BEGIN and END markers present."""
        html = self._render()
        assert "<!-- BEGIN: base.html -->" in html
        assert "<!-- END: base.html -->" in html

    def test_static_asset_references(self):
        """References to bundled CSS and JS present."""
        html = self._render()
        assert "pico.min.css" in html
        assert "depo.css" in html
        assert "htmx.min.js" in html
