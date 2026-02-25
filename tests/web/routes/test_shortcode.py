# tests/web/routes/test_shortcode.py
"""
Tests for shortcode route handlers.
Covers GET /{code} dispatch, GET /{code}/info negotiation,
GET /{code}/raw responses, and info page rendering for
all item types.
Author: Marcus Grant
Created: 2026-02-23
License: Apache-2.0
"""

import pytest


class TestItem:
    """Tests for GET /{code} dispatcher."""

    def test_api_client_redirects_to_raw(self, t_seeded):
        """Non-HTML request redirects to /{code}/raw."""
        resp = t_seeded.client.get(f"/{t_seeded.txt.code}", follow_redirects=False)
        assert resp.status_code == 302
        assert resp.headers["location"] == f"/{t_seeded.txt.code}/raw"

    def test_browser_redirects_to_info(self, t_seeded):
        """HTML request redirects to /{code}/info."""
        resp = t_seeded.browser.get(f"/{t_seeded.txt.code}", follow_redirects=False)
        assert resp.status_code == 302
        assert resp.headers["location"] == f"/{t_seeded.txt.code}/info"

    @pytest.mark.parametrize(
        "accept_head, expected",
        [
            ("text/html", "/f00bar/info"),
            ("*/*", "/f00bar/raw"),
            ("some/format", "/f00bar/raw"),
            ("", "/f00bar/raw"),
        ],
    )
    def test_different_client_redirects(self, t_client, accept_head, expected):
        kwargs = {"headers": {"Accept": accept_head}, "follow_redirects": False}
        resp = t_client.get("/f00bar", **kwargs)
        assert resp.status_code == 302
        assert resp.headers["location"] == expected

    def test_unknown_code_redirects(self, t_client):
        """Unknown code still redirects (validation happens at canonical route)."""
        # First test redirection for browsers sending text/html accept headers
        kwargs = {"headers": {"Accept": "text/html"}, "follow_redirects": False}
        resp = t_client.get("/N0EX1ST", **kwargs)
        assert resp.status_code == 302
        assert resp.headers["location"] == "/N0EX1ST/info"
        # Second test redirection for api clients sending */* accept headers
        kwargs = {"headers": {"Accept": "*/*"}, "follow_redirects": False}
        resp = t_client.get("/N0EX1ST", **kwargs)
        assert resp.status_code == 302
        assert resp.headers["location"] == "/N0EX1ST/raw"


class TestGetInfo:
    """Tests for GET /{code}/info.
    Uses t_seeded for pre-populated items, t_client for 404."""

    def test_text_item_info(self, t_seeded):
        """Text item returns metadata as plain text."""
        resp = t_seeded.client.get(f"/{t_seeded.txt.code}/info")
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/plain")
        assert f"code={t_seeded.txt.code}" in resp.text
        assert "kind=txt" in resp.text
        assert "format=md" in resp.text
        assert "size_b=" in resp.text

    def test_pic_item_info(self, t_seeded):
        """Pic item returns metadata including dimensions."""
        resp = t_seeded.client.get(f"/{t_seeded.pic.code}/info")
        assert resp.status_code == 200
        assert "kind=pic" in resp.text
        assert "width=320" in resp.text
        assert "height=240" in resp.text

    def test_link_item_info(self, t_seeded):
        """Link item returns metadata including URL."""
        resp = t_seeded.client.get(f"/{t_seeded.link.code}/info")
        assert resp.status_code == 200
        assert "kind=url" in resp.text
        assert "url=http://example.com" in resp.text

    def test_unknown_code_404(self, t_client):
        """Unknown code returns 404."""
        assert t_client.get("/ZZZZZZZZ/info").status_code == 404


class TestInfoPage:
    """GET /{code}/info serves correct template per item type."""

    def _assert_info_page(self, resp, template: str, code: str):
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/html")
        assert f"<!-- BEGIN: info/{template}" in resp.text
        assert code in resp.text

    def test_text(self, t_seeded):
        resp = t_seeded.browser.get(f"/{t_seeded.txt.code}/info")
        self._assert_info_page(resp, "text.html", t_seeded.txt.code)

    def test_pic(self, t_seeded):
        resp = t_seeded.browser.get(f"/{t_seeded.pic.code}/info")
        self._assert_info_page(resp, "pic.html", t_seeded.pic.code)

    def test_link(self, t_seeded):
        resp = t_seeded.browser.get(f"/{t_seeded.link.code}/info")
        self._assert_info_page(resp, "link.html", t_seeded.link.code)

    def test_copy_url_absolute(self, t_seeded):
        """Copy URL button has absolute URL."""
        resp = t_seeded.browser.get(f"/{t_seeded.txt.code}/info")
        assert 'data-copy="http' in resp.text


class TestInfoPageNotFound:
    """GET /{code}/info for unknown code"""

    def test_unknown_code_returns_404(self, t_browser):
        """Unknown code returns 404."""
        assert t_browser.get("/ZZZZZZZZ/info").status_code == 404


class TestGetRaw:
    """Tests for GET /{code}/raw.
    Uses t_seeded for pre-populated items, t_client for 404."""

    def test_text_returns_raw_content(self, t_seeded):
        """Text item returns raw content with text/plain MIME."""
        resp = t_seeded.client.get(f"/{t_seeded.txt.code}/raw")
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/plain")
        assert "charset=utf-8" in resp.headers["content-type"]
        assert b"# Hello, World!" in resp.content

    def test_pic_returns_raw_bytes(self, t_seeded):
        """Pic item returns raw bytes with correct image MIME."""
        resp = t_seeded.client.get(f"/{t_seeded.pic.code}/raw")
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("image/jpeg")
        assert len(resp.content) == t_seeded.pic.size_b

    def test_link_returns_redirect(self, t_seeded):
        """LinkItem returns redirect to URL."""
        endpoint = f"/{t_seeded.link.code}/raw"
        resp = t_seeded.client.get(endpoint, follow_redirects=False)
        assert resp.status_code == 307
        assert resp.headers["location"] == "http://example.com"

    def test_unknown_code_returns_404(self, t_client):
        """Unknown code returns 404."""
        assert t_client.get("/ZZZZZZZZ/raw").status_code == 404
