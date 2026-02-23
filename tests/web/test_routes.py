# tests/web/test_routes.py
"""
Tests for top-level route wiring.
Covers root redirect, health probe, and route aliases
registered in the routes package init.
Author: Marcus Grant
Created: 2026-02-23
License: Apache-2.0
"""


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
