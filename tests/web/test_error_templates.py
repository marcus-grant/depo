# tests/web/test_error_templates.py
"""
Tests for error page and partial templates.
Author: Marcus Grant
Created: 2026-05-05
License: Apache-2.0
"""

from depo.util.errors import NotFoundError, PayloadTooLargeError, UnknownServerError
from tests.factories import make_request, render_template

_ISSUES_URL = "https://github.com/marcus-grant/depo/issues"


class TestErrorPartialTemplate:
    """Tests for errors/partial.html - HTMX error partial renders."""

    def _render(self, error, role="alert"):
        return render_template("errors/partial.html", {"error": error, "role": role})

    def test_renders_error_message(self):
        """Renders error.message in the partial body."""
        e = PayloadTooLargeError(size=257, max_size=256)
        assert e.message in self._render(e).text

    def test_base_error_class(self):
        """Container always has base error class."""
        e = PayloadTooLargeError(size=257, max_size=256)
        assert self._render(e).find("div", class_="error") is not None

    def test_default_role_css_class(self):
        """Default role 'alert' applied as CSS mod class."""
        e = PayloadTooLargeError(size=257, max_size=256)
        div = self._render(e).find("div")
        assert div is not None
        classes = list(div.get("class") or [])
        assert "error--alert" in classes
        assert len([c for c in classes if c.startswith("error--")]) == 1

    def test_role_aria_attribute(self):
        """Role applied as ARIA role attribute on container."""
        e = PayloadTooLargeError(size=257, max_size=256)
        assert self._render(e).find("div", attrs={"role": "alert"}) is not None

    def test_custom_role(self):
        """Custom role applied as CSS modifier and ARIA attribute."""
        e = PayloadTooLargeError(size=257, max_size=256)
        soup = self._render(e, role="status")
        div = soup.find("div")
        assert div is not None
        classes = list(div.get("class") or [])
        assert "error--status" in classes
        assert len([c for c in classes if c.startswith("error--")]) == 1
        assert soup.find("div", attrs={"role": "status"}) is not None


class TestErrorPageTemplate:
    """Tests for errors/page.html - full page error renders."""

    def _render(self, error, request=None):
        req = request or make_request()
        ctx = {"error": error, "request": req, "issues_url": _ISSUES_URL}
        return render_template("errors/page.html", ctx)

    def test_window_error_container(self):
        """Renders inside a section.window.window--error container."""
        e = NotFoundError(id="abc123")
        soup = self._render(e)
        assert soup.find("section", class_="window--error") is not None

    def test_message_in_h2(self):
        """Renders error.message in h2."""
        e = NotFoundError(id="abc123")
        soup = self._render(e)
        h2 = soup.find("h2")
        assert h2 is not None
        assert e.message in h2.text

    def test_no_debug_block_for_4xx(self):
        """No debug details block rendered for 4xx errors."""
        e = NotFoundError(id="abc123")
        assert self._render(e).find("details") is None

    def test_debug_block_for_5xx(self):
        """Debug details block rendered for 5xx errors."""
        e = UnknownServerError()
        assert self._render(e).find("details") is not None

    def test_debug_block_contains_path_and_method(self):
        """Debug block contains request path and method."""
        e = UnknownServerError()
        req = make_request(path="/test/path", method="POST")
        details = self._render(e, request=req).find("details")
        assert details is not None
        assert "/test/path" in details.text
        assert "POST" in details.text

    def test_issues_link_for_5xx(self):
        """Issues link present inside error section for 5xx errors."""
        e = UnknownServerError()
        section = self._render(e).find("section", class_="window--error")
        assert section is not None
        assert section.find("a", href=_ISSUES_URL) is not None

    def test_no_action_or_metadata(self):
        """No action row, metadata, or meta elements rendered."""
        e = NotFoundError(id="abc123")
        section = self._render(e).find("section", class_="window--error")
        assert section is not None
        assert section.find(class_="action-row") is None
        assert section.find(class_="metadata") is None
        assert section.find(class_="meta") is None
