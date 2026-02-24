# tests/web/test_templates.py
"""
Tests for template rendering utilities.
Author: Marcus Grant
Created: 2026-02-12
License: Apache-2.0
"""

import jinja2
import pytest
from bs4 import BeautifulSoup as BSoup
from bs4 import Comment

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


def _assert_a_in(el, href, txt, msg=None):
    msg = f"{msg + ':' if msg else ''} expected <a href='{href}'>{txt}</a>"
    assert el.find("a", href=href, string=lambda s: s and txt in s.lower()), msg


class TestBaseTemplate:
    """Base layout template renders correctly."""

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
        html = self._render("TESTBLOCK123")
        soup = BSoup(html, "html.parser")
        # Marker should appear outside any HTML comment
        assert "TESTBLOCK123" in html
        for comment in soup.find_all(string=lambda s: isinstance(s, Comment)):
            assert "TESTBLOCK123" not in comment

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

    def test_navbar(self):
        """Nav partial renders with markers and contains wordmark."""
        html = self._render()
        nav = BSoup(html, "html.parser").find("nav")
        assert nav is not None, "No <nav> block found"
        assert "<!-- BEGIN: partials/nav.html -->" in html
        assert "<!-- END: partials/nav.html -->" in html
        assert nav.find("a", href="/", string=lambda s: s and "depo" in s.lower())  # type: ignore
        _assert_a_in(nav, "/", "depo", "No 'depo' link to '/")

    def test_footer(self):
        html = self._render()
        foot = BSoup(html, "html.parser").find("footer")
        assert foot is not None, "No <footer> block found"
        assert "<!-- BEGIN: partials/foot.html -->" in html
        assert "<!-- END: partials/foot.html -->" in html
        author = "https://github.com/marcus-grant"
        depo = f"{author}/depo"
        _assert_a_in(foot, author, "marcus grant", "No link to author")
        _assert_a_in(foot, depo, "depo", "No link to repo")
        _assert_a_in(foot, f"{depo}/issues", "issues", "No link to issues")
