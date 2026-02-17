# tests/web/test_negotiate_routes.py
"""
Tests for shortcut route negotiation.
Author: Marcus Grant
Created: 2026-02-16
License: Apache-2.0
"""

import pytest

from tests.factories.web import make_client


class TestShortcutRoute:
    """GET /{code} redirects based on client type"""

    @pytest.mark.parametrize(
        "accept_head, expected",
        [
            ("text/html", "/f00bar/info"),
            ("*/*", "/api/f00bar/raw"),
            ("some/format", "/api/f00bar/raw"),
            ("", "/api/f00bar/raw"),
        ],
    )
    def test_different_client_redirects(self, accept_head, expected, tmp_path):
        kwargs = {"headers": {"Accept": accept_head}, "follow_redirects": False}
        resp = make_client(tmp_path).get("/f00bar", **kwargs)
        assert resp.status_code == 302
        assert resp.headers["location"] == expected

    def test_unknown_code_redirects(self, tmp_path):
        """Unknown code still redirects (validation happens at canonical route)."""
        kwargs = {"headers": {"Accept": "text/html"}, "follow_redirects": False}
        resp = make_client(tmp_path).get("/N0EX1ST", **kwargs)
        assert resp.status_code == 302
        assert resp.headers["location"] == "/N0EX1ST/info"
        kwargs = {"headers": {"Accept": "*/*"}, "follow_redirects": False}
        resp = make_client(tmp_path).get("/N0EX1ST", **kwargs)
        assert resp.status_code == 302
        assert resp.headers["location"] == "/api/N0EX1ST/raw"
