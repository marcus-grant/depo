# tests/web/test_routes.py
"""
Integration tests for route handlers.

Round-trip tests via TestClient against the FastAPI
application.

Author: Marcus Grant
Created: 2026-02-10
License: Apache-2.0
"""


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
