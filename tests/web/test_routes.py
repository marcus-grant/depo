# tests/web/test_routes.py
"""
Tests for top-level route wiring.
Covers root redirect, health probe, and route aliases
registered in the routes package init.
Author: Marcus Grant
Created: 2026-02-23
License: Apache-2.0
"""


class TestRouteRegistration:
    """Fixed-path routes are not swallowed by /{code} wildcard."""

    def test_health_not_captured_by_wildcard(self, t_client):
        """GET /health returns 200 OK, not a shortcode lookup."""
        resp = t_client.get("/health")
        assert resp.status_code == 200
        assert resp.text == "ok"

    def test_upload_not_captured_by_wildcard(self, t_client):
        """GET /upload returns upload page, not a shortcode lookup."""
        resp = t_client.get("/upload")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]

    def test_root_not_captured_by_wildcard(self, t_client):
        """GET / redirects to /upload, not a shortcode lookup."""
        resp = t_client.get("/", follow_redirects=False)
        assert resp.status_code == 302
        assert resp.headers["location"] == "/upload"

    def test_wildcard_does_not_shadow_fixed_routes(self, t_client):
        """Every fixed-path GET route resolves without hitting /{code}."""
        app = t_client.app
        fixed_gets = [
            r.path
            for r in app.routes
            if hasattr(r, "methods") and "GET" in r.methods and "{" not in r.path
        ]
        for path in fixed_gets:
            resp = t_client.get(path, follow_redirects=False)
            assert resp.status_code != 404, f"{path} shadowed by wildcard"


class TestRootRedirect:
    """GET / redirects to /upload.

    # Returns redirect status
    # Redirects to /upload
    """

    def test_redirects_to_upload_302(self, t_client):
        """GET / redirects with 302 to /upload"""
        resp = t_client.get(url="/", follow_redirects=False)
        assert resp.status_code == 302
        assert resp.headers.get("location") == "/upload"
