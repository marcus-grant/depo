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

from depo.cli import defaults
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
        data = {"content": "x" * (defaults.MAX_SIZE_BYTES + 1), "format": ""}
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


class TestUnexpectedErrorBoundary:
    """Non-DepoError exceptions hit the app-level boundary, get wrapped
    as UnknownServerError, surface-negotiated, and logged once."""

    def _patch_selector_oserror(self, monkeypatch):
        """Make selector.get_item raise a non-DepoError on any call."""
        from depo.web.routes import shortcode

        def _boom(*_):
            raise OSError("disk gone")

        monkeypatch.setattr(shortcode.selector, "get_item", _boom)

    def test_boundary_browser_returns_500_page(self, t_noreraise, monkeypatch):
        """Browser surface: non-DepoError yields a controlled 500 rendering
        errors/page.html, not FastAPI's default 500."""
        self._patch_selector_oserror(monkeypatch)
        resp = t_noreraise.get("/ABC12345/info", headers={"Accept": "text/html"})
        assert resp.status_code == 500
        assert "<!-- BEGIN: errors/page.html" in resp.text

    def test_boundary_api_returns_500(self, t_noreraise, monkeypatch):
        """API surface: non-DepoError yields a controlled 500 response."""
        self._patch_selector_oserror(monkeypatch)
        resp = t_noreraise.get("/ABC12345/info")
        assert resp.status_code == 500

    def test_boundary_htmx_returns_200_partial(self, t_noreraise, monkeypatch):
        """HTMX surface: non-DepoError yields 200 plus errors/partial.html,
        honoring the HTMX contract that errors ride in the body."""
        self._patch_selector_oserror(monkeypatch)
        resp = t_noreraise.get("/ABC12345/info", headers=HEADER_HTMX)
        assert resp.status_code == 200
        assert "<!-- BEGIN: errors/partial.html" in resp.text

    def test_boundary_logs_once(self, t_noreraise, monkeypatch, caplog):
        """The boundary logs exactly one depo record: the builders log,
        the handler must not log again."""
        import logging

        self._patch_selector_oserror(monkeypatch)
        caplog.set_level(logging.DEBUG, logger="depo")
        t_noreraise.get("/ABC12345/info")
        recs = [r for r in caplog.records if r.name.startswith("depo")]
        assert len(recs) == 1
