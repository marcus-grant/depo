# tests/web/test_upload_htmx.py
"""
Tests for HTMX upload flow.
Author: Marcus Grant
Created: 2026-02-13
License: Apache-2.0
"""

from bs4 import BeautifulSoup

from tests.factories import HEADER_HTMX


class TestHtmxUploadSuccess:
    """POST /upload with HX-Request returns success partial.
    Makes use of t_client fixture and module constant _HEADER_HX.
    """

    def test_success_returns_shortcode(self, t_client):
        """Success partial contains a non-empty shortcode element."""
        data = {"content": "hello world", "format": ""}
        resp = t_client.post("/upload", data=data, headers=HEADER_HTMX)
        assert resp.status_code == 200
        soup = BeautifulSoup(resp.text, "html.parser")
        code_el = soup.find("code", class_="shortcode")
        assert code_el is not None
        assert len(code_el.text.strip()) > 0

    def test_success_contains_info_link(self, t_client):
        """Success partial links to the info page for the uploaded item."""
        data = {"content": "hello world", "format": ""}
        resp = t_client.post("/upload", data=data, headers=HEADER_HTMX)
        soup = BeautifulSoup(resp.text, "html.parser")
        code = soup.find("code", class_="shortcode").text.strip()  # type: ignore
        link = soup.find("a", href=f"/{code}/info")
        assert link is not None

    def test_success_is_fragment(self, t_client):
        """Success partial is not wrapped in base template."""
        data = {"content": "hello world", "format": ""}
        resp = t_client.post("/upload", data=data, headers=HEADER_HTMX)
        assert "<!-- BEGIN: base.html -->" not in resp.text
        assert "<!-- BEGIN: partials/success.html" in resp.text


class TestHtmxUploadError:
    """POST /upload with HX-Request returns error partial on failure."""

    def test_empty_content_returns_error(self, t_client):
        """Empty content submission renders an error div."""
        data = {"content": "", "format": ""}
        resp = t_client.post("/upload", data=data, headers=HEADER_HTMX)
        assert resp.status_code == 200
        soup = BeautifulSoup(resp.text, "html.parser")
        error = soup.find("div", class_="upload-error")
        assert error is not None

    def test_error_contains_message(self, t_client):
        """Error partial includes a descriptive error message."""
        data = {"content": "", "format": ""}
        resp = t_client.post("/upload", data=data, headers=HEADER_HTMX)
        assert "No content provided" in resp.text

    def test_error_is_fragment(self, t_client):
        """Error partial is not wrapped in base template."""
        data = {"content": "", "format": ""}
        resp = t_client.post("/upload", data=data, headers=HEADER_HTMX)
        assert "<!-- BEGIN: base.html -->" not in resp.text
        assert "<!-- BEGIN: partials/error.html" in resp.text
