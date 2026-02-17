# tests/web/test_errors.py
"""
Tests for error handlers.
Author: Marcus Grant
Created: 2026-02-16
License: Apache-2.0
"""

from bs4 import BeautifulSoup
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from tests.factories import HEADER_HTMX


class TestError404Page:
    """404 error page rendering. Makes use of t_client fixture."""

    def test_response(self, t_client):
        """404 page renders with code and base template."""
        resp = t_client.get("/ZZZZZZZZ/info")
        assert resp.status_code == 404
        assert "<!-- BEGIN: base.html" in resp.text
        assert "<!-- BEGIN: errors/404.html" in resp.text
        assert "ZZZZZZZZ" in resp.text


class TestError413Page:
    """413 payload too large error.
    Makes use of t_client fixture & factory HEADER_HTMX to clean up testing."""

    def test_api_oversized_returns_413(self, t_client):
        """API upload exceeding max size returns 413."""
        payload = b"x" * (2**20 + 1)
        resp = t_client.post("/api/upload", files={"file": ("big.txt", payload)})
        assert resp.status_code == 413

    def test_htmx_oversized_returns_413(self, t_client):
        """HTMX upload exceeding max size returns error partial."""
        data = {"content": "x" * (2**20 + 1), "format": ""}
        resp = t_client.post("/upload", data=data, headers=HEADER_HTMX)
        assert resp.status_code == 413
        assert "<!-- BEGIN: partials/error.html" in resp.text


class TestHtmxErrorPartial:
    """HTMX requests receive error partials, not full pages.
    Makes use of t_client fixture & factory HEADER_HTMX to clean up testing."""

    def test_error_partial_no_base_template(self, t_client):
        """HTMX error response is a fragment, not wrapped in base.html."""
        data = {"content": "", "format": ""}
        resp = t_client.post("/upload", data=data, headers=HEADER_HTMX)
        assert "<!-- BEGIN: partials/error.html" in resp.text
        assert "<!-- BEGIN: base.html" not in resp.text

    def test_error_partial_contains_message(self, t_client):
        """HTMX error partial includes the error message."""
        data = {"content": "", "format": ""}
        resp = t_client.post("/upload", data=data, headers=HEADER_HTMX)
        assert "No content provided" in resp.text

    def test_413_partial_no_base_template(self, t_client):
        """HTMX 413 error is a fragment, not wrapped in base.html."""
        data = {"content": "x" * (2**20 + 1), "format": ""}
        resp = t_client.post("/upload", data=data, headers=HEADER_HTMX)
        assert resp.status_code == 413
        assert "<!-- BEGIN: partials/error.html" in resp.text
        assert "<!-- BEGIN: base.html" not in resp.text


class TestError500Page:
    """500 internal server error rendering"""

    def _make_500_client(self) -> TestClient:
        from depo.web.routes import _response_500

        app = FastAPI()

        @app.get("/trigger500")
        def _trigger(request: Request):
            return _response_500(request, "test error detail")

        _ = _trigger
        return TestClient(app)

    def test_response(self):
        """500 page renders with debug context and issues link."""
        resp = self._make_500_client().get("/trigger500")
        assert resp.status_code == 500
        soup = BeautifulSoup(resp.text, "html.parser")
        assert "<!-- BEGIN: base.html" in resp.text
        assert "<!-- BEGIN: errors/500.html" in resp.text
        assert "Something went wrong" in resp.text
        assert "test error detail" in resp.text
        href = "https://github.com/marcus-grant/depo/issues"
        assert soup.find("a", href=(href is not None))

    def test_debug_info_present(self):
        """Debug info contains path and method."""
        resp = self._make_500_client().get("/trigger500")
        soup = BeautifulSoup(resp.text, "html.parser")
        details = soup.find("details")
        assert details is not None
        assert "/trigger500" in details.text
        assert "GET" in details.text
