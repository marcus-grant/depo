# tests/web/test_errors.py
"""
Tests for error surface integration via route calls.
Author: Marcus Grant
Created: 2026-02-16
Revised: [2026-05-05]
License: Apache-2.0
"""

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from tests.factories import HEADER_HTMX


class TestFullPageError:
    """Full-page error rendering via browser route calls."""

    def _make_500_client(self) -> TestClient:
        """Build a minimal FastAPI test client with a route that triggers
        a browser_error response with UnknownServerError. Used to test
        full-page 500 error rendering without depending on shortcode routes."""
        from depo.util.errors import UnknownServerError
        from depo.web.error import browser_error

        app = FastAPI()

        @app.get("/trigger500")
        def _trigger(req: Request):
            _ = _trigger  # For LSP, FastAPI expects response handlers
            return browser_error(req, UnknownServerError())

        return TestClient(app)

    def _500_response(self):
        """Build a browser_error response with
        UnknownServerError via minimal FastAPI app."""
        return self._make_500_client().get("/trigger500")

    def test_404_status(self, t_browser: TestClient):
        """Unknown shortcode should return 404 status."""
        assert t_browser.get("/N0EX1ST/info").status_code == 404

    def test_404_renders_page_template(self, t_browser: TestClient):
        """404 response uses errors/page.html and includes error message."""
        resp = t_browser.get("/N0EX1ST/info")
        assert "<!-- BEGIN: errors/page.html" in resp.text
        assert "N0EX1ST" in resp.text

    def test_500_status(self):
        """UnknownServerError should return 500 status."""
        assert self._500_response().status_code == 500

    def test_500_renders_page_template(self):
        """500 response uses errors/page.html & renders debug block w/ path."""
        assert "<!-- BEGIN: errors/page.html" in self._500_response().text
        assert "<summary>Debug info" in self._500_response().text
        assert "/trigger500" in self._500_response().text


class TestHtmxErrorPartial:
    """HTMX requests receive error partials via route calls."""

    def _empty_resp(self, c: TestClient):
        """POST empty upload with HTMX headers, return response."""
        data = {"content": "", "format": ""}
        return c.post("/upload", data=data, headers=HEADER_HTMX)

    def _oversize_resp(self, c: TestClient):
        """POST oversized upload with HTMX headers, return response."""
        from depo.service.ingest import DEFAULT_MAX_SIZE_BYTES

        data = {"content": "x" * (DEFAULT_MAX_SIZE_BYTES + 1), "format": ""}
        return c.post("/upload", data=data, headers=HEADER_HTMX)

    def test_empty_upload_returns_partial(self, t_client: TestClient):
        """Empty upload returns error partial not wrapped in base template."""
        assert "<!-- BEGIN: errors/partial.html" in self._empty_resp(t_client).text
        assert "<!-- BEGIN: base.html" not in self._empty_resp(t_client).text

    def test_empty_upload_error_message(self, t_client: TestClient):
        """Empty upload error partial includes error message."""
        from depo.util.errors import PayloadEmptyError

        assert PayloadEmptyError.message in self._empty_resp(t_client).text

    def test_oversized_upload_returns_partial(self, t_client: TestClient):
        """Oversized upload returns error partial not wrapped in base template."""
        resp = self._oversize_resp(t_client)
        expected_words = ["too large", "too big", "exceeds", "exceed", "oversized"]
        assert any(w in resp.text.lower() for w in expected_words)
        assert "<!-- BEGIN: errors/partial.html" in resp.text
        assert "<!-- BEGIN: base.html" not in resp.text

    def test_htmx_error_returns_200(self, t_client: TestClient):
        """HTMX error responses always return 200 status."""
        assert self._empty_resp(t_client).status_code == 200
        assert self._oversize_resp(t_client).status_code == 200
