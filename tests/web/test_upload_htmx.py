# tests/web/test_upload_htmx.py
"""
Tests for HTMX upload flow.
Author: Marcus Grant
Created: 2026-02-13
License: Apache-2.0
"""

from bs4 import BeautifulSoup

from tests.factories import make_client


class TestHtmxUploadSuccess:
    """POST /upload with HX-Request returns success partial"""

    def test_success_returns_shortcode(self, tmp_path):
        client = make_client(tmp_path)
        resp = client.post(
            "/upload",
            data={"content": "hello world", "format": ""},
            headers={"HX-Request": "true"},
        )
        assert resp.status_code == 200
        soup = BeautifulSoup(resp.text, "html.parser")
        code_el = soup.find("code", class_="shortcode")
        assert code_el is not None
        assert len(code_el.text.strip()) > 0

    def test_success_contains_info_link(self, tmp_path):
        client = make_client(tmp_path)
        resp = client.post(
            "/upload",
            data={"content": "hello world", "format": ""},
            headers={"HX-Request": "true"},
        )
        soup = BeautifulSoup(resp.text, "html.parser")
        code = soup.find("code", class_="shortcode").text.strip()  # type: ignore
        link = soup.find("a", href=f"/{code}/info")
        assert link is not None

    def test_success_is_fragment(self, tmp_path):
        client = make_client(tmp_path)
        resp = client.post(
            "/upload",
            data={"content": "hello world", "format": ""},
            headers={"HX-Request": "true"},
        )
        assert "<!-- BEGIN: base.html -->" not in resp.text
        assert "<!-- BEGIN: partials/success.html" in resp.text


class TestHtmxUploadError:
    """POST /upload with HX-Request returns error partial on failure."""

    def test_empty_content_returns_error(self, tmp_path):
        client = make_client(tmp_path)
        resp = client.post(
            "/upload",
            data={"content": "", "format": ""},
            headers={"HX-Request": "true"},
        )
        assert resp.status_code == 200
        soup = BeautifulSoup(resp.text, "html.parser")
        error = soup.find("div", class_="upload-error")
        assert error is not None

    def test_error_contains_message(self, tmp_path):
        client = make_client(tmp_path)
        resp = client.post(
            "/upload",
            data={"content": "", "format": ""},
            headers={"HX-Request": "true"},
        )
        assert "No content provided" in resp.text

    def test_error_is_fragment(self, tmp_path):
        client = make_client(tmp_path)
        resp = client.post(
            "/upload",
            data={"content": "", "format": ""},
            headers={"HX-Request": "true"},
        )
        assert "<!-- BEGIN: base.html -->" not in resp.text
        assert "<!-- BEGIN: partials/error.html" in resp.text
