# tests/web/test_static.py
"""
Tests for static file serving.
Verifies bundled frontend assets are accessible.
Author: Marcus Grant
Created: 2026-02-12
License: Apache-2.0
"""


class TestStaticFiles:
    """Static assets are served correctly."""

    def test_htmx_served(self, t_client):
        """HTMX JS bundle is accessible."""
        resp = t_client.get("/static/js/htmx.min.js")
        assert resp.status_code == 200
        assert "javascript" in resp.headers["content-type"]

    def test_pico_served(self, t_client):
        """Pico CSS bundle is accessible."""
        resp = t_client.get("/static/css/pico.min.css")
        assert resp.status_code == 200
        assert "css" in resp.headers["content-type"]

    def test_missing_static_404(self, t_client):
        """Non-existent static file returns 404."""
        resp = t_client.get("/static/nope.js")
        assert resp.status_code == 404
