# tests/web/test_static.py
"""
Tests for static file serving.
Verifies bundled frontend assets are accessible.
Author: Marcus Grant
Created: 2026-02-12
License: Apache-2.0
"""

from tests.factories.web import make_client


class TestStaticFiles:
    """Static assets are served correctly."""

    def test_htmx_served(self, tmp_path):
        """HTMX JS bundle is accessible."""
        resp = make_client(tmp_path).get("/static/js/htmx.min.js")
        assert resp.status_code == 200
        assert "javascript" in resp.headers["content-type"]

    def test_pico_served(self, tmp_path):
        """Pico CSS bundle is accessible."""
        resp = make_client(tmp_path).get("/static/css/pico.min.css")
        assert resp.status_code == 200
        assert "css" in resp.headers["content-type"]

    def test_missing_static_404(self, tmp_path):
        """Non-existent static file returns 404."""
        resp = make_client(tmp_path).get("/static/nope.js")
        assert resp.status_code == 404
