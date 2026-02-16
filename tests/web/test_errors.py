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

from tests.factories.web import make_client


class TestError404Page:
    """404 error page rendering"""

    def test_response(self, tmp_path):
        """404 page renders with code and base template."""
        client = make_client(tmp_path)
        resp = client.get("/ZZZZZZZZ/info")
        assert resp.status_code == 404
        assert "<!-- BEGIN: base.html" in resp.text
        assert "<!-- BEGIN: errors/404.html" in resp.text
        assert "ZZZZZZZZ" in resp.text


class TestError413Page:
    """413 payload too large error"""

    def test_api_oversized_returns_413(self, tmp_path):
        """API upload exceeding max size returns 413."""
        client = make_client(tmp_path)
        payload = b"x" * (2**20 + 1)
        resp = client.post("/api/upload", files={"file": ("big.txt", payload)})
        assert resp.status_code == 413

    def test_htmx_oversized_returns_413(self, tmp_path):
        """HTMX upload exceeding max size returns error partial."""
        client = make_client(tmp_path)
        content = "x" * (2**20 + 1)
        resp = client.post(
            "/upload",
            data={"content": content, "format": ""},
            headers={"HX-Request": "true"},
        )
        assert resp.status_code == 413
        assert "<!-- BEGIN: partials/error.html" in resp.text


class TestHtmxErrorPartial:
    """HTMX requests receive error partials, not full pages"""

    def test_error_partial_no_base_template(self, tmp_path):
        """HTMX error response is a fragment, not wrapped in base.html."""
        client = make_client(tmp_path)
        resp = client.post(
            "/upload",
            data={"content": "", "format": ""},
            headers={"HX-Request": "true"},
        )
        assert "<!-- BEGIN: partials/error.html" in resp.text
        assert "<!-- BEGIN: base.html" not in resp.text

    def test_error_partial_contains_message(self, tmp_path):
        """HTMX error partial includes the error message."""
        client = make_client(tmp_path)
        resp = client.post(
            "/upload",
            data={"content": "", "format": ""},
            headers={"HX-Request": "true"},
        )
        assert "No content provided" in resp.text

    def test_413_partial_no_base_template(self, tmp_path):
        """HTMX 413 error is a fragment, not wrapped in base.html."""
        client = make_client(tmp_path)
        content = "x" * (2**20 + 1)
        resp = client.post(
            "/upload",
            data={"content": content, "format": ""},
            headers={"HX-Request": "true"},
        )
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
