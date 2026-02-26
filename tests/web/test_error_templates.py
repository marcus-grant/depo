# tests/web/test_error_templates.py
"""
Tests for error page templates (404, 500).
Author: Marcus Grant
Created: 2026-02-25
License: Apache-2.0
"""

from tests.factories import render_template


def _404_select(selector: str):
    """Render 404 template w/ stub context, return first CSS match."""
    return render_template("errors/404.html", {"code": "abc123"}).select_one(selector)


_500_MSG = "Something went wrong"
_500_DET = "test error detail"
_500_URL = "https://github.com/marcus-grant/depo/issues"


def _500_select(selector: str):
    """Render 500 template w/ stub context, return first CSS match."""
    return render_template(
        "errors/500.html",
        {
            "message": _500_MSG,
            "path": "/test",
            "method": "GET",
            "detail": _500_DET,
            "issues_url": _500_URL,
        },
    ).select_one(selector)


class TestError404:
    """404 error template."""

    def select(self, selector):
        """Helper alias for selecting from 404 template soup."""
        return _404_select(selector)

    def test_window_error_container(self):
        """Renders inside a .window container."""
        assert self.select("section.window.window--error") is not None

    def test_shortcode_in_error_text(self):
        """Has shortcode in code tag in error message."""
        assert self.select("section.window code.shortcode") is not None
        assert self.select("section.window code.shortcode").text == "ABC123"  # type: ignore

    def test_no_action_or_metadata(self):
        """Nas no action row, metadata, or meta elements (info pages only)."""
        assert self.select("section.window .action-row") is None
        assert self.select("section.window .metadata") is None
        assert self.select("section.window .meta") is None


class TestError500:
    """500 error template."""

    def select(self, selector):
        """Helper alias for selecting from 500 template soup."""
        return _500_select(selector)

    def test_window_error_container(self):
        """Renders inside a .window container."""
        assert self.select("section.window.window--error") is not None

    def test_message_in_error_text(self):
        """Renders message text in .error-text element."""
        assert self.select("section.window--error h2") is not None
        assert self.select("section.window--error h2").text == _500_MSG  # type: ignore

    def test_debug_details(self):
        """Debug details block has summary, path, and method."""
        details = self.select("section.window--error details")
        assert details is not None, "No <details> element found"
        assert details.find("summary") is not None, "No <summary> in details"
        assert "GET" in details.text and "/test" in details.text

    def test_issues_link(self):
        """Issues link present for error reporting."""
        url_selector = f"section.window--error a[href='{_500_URL}']"
        assert self.select(url_selector) is not None
