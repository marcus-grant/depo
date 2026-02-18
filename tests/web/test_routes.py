# tests/web/test_routes.py
"""
Integration tests for route handlers.

Round-trip tests via TestClient against the FastAPI
application.

Author: Marcus Grant
Created: 2026-02-10
License: Apache-2.0
"""

from depo.util.shortcode import _CROCKFORD32
from tests.factories import gen_image


class TestUploadText:
    """Tests for text content upload."""

    def test_multipart_text_returns_201(self, t_client):
        """Multipart text upload returns 201, valid short code, metadata headers."""
        resp = t_client.post("/api/upload", files={"file": ("hello.txt", b"Hello!")})
        assert resp.status_code == 201
        assert resp.headers["content-type"].startswith("text/plain")
        assert resp.text == resp.headers["X-Depo-Code"]
        assert resp.headers["X-Depo-Kind"] == "txt"
        assert resp.headers["X-Depo-Created"] == "true"
        assert all(char in _CROCKFORD32 for char in resp.text)
        assert len(resp.text) == 8

    def test_empty_payload_returns_400(self, t_client):
        """Empty file upload returns 400."""
        file = {"file": ("0.txt", b"")}
        assert t_client.post("/api/upload", files=file).status_code == 400

    def test_unclassifiable_returns_400(self, t_client):
        """Unclassifiable content returns 400 with message."""
        resp = t_client.post("/api/upload", files={"file": ("noext", b"\xff\xfe\xfd")})
        assert resp.status_code == 400
        assert len(resp.text) > 0  # error message present


class TestUploadImage:
    """Tests for image content upload."""

    def test_multipart_pic_returns_201(self, t_client):
        """Multipart pic upload returns 201, valid, short code, meta headers"""
        file = {"file": ("screenshot.jpg", gen_image("jpeg", 16, 16))}
        resp = t_client.post("/api/upload", files=file)
        assert resp.status_code == 201
        assert resp.headers["content-type"].startswith("text/plain")
        assert resp.text == resp.headers["X-Depo-Code"]
        assert resp.headers["X-Depo-Kind"] == "pic"
        assert resp.headers["X-Depo-Created"] == "true"
        assert all(char in _CROCKFORD32 for char in resp.text)
        assert len(resp.text) == 8

    def test_corrupt_jpeg_returns_400(self, t_client):
        """JPEG magic bytes without valid image data returns 400."""
        resp = t_client.post("/api/upload", files={"file": b"\xff\xd8\xff\xe0"})
        assert resp.status_code == 400
        assert len(resp.text) > 0


class TestUploadLink:
    """Tests for link/URL submission."""

    def test_url_param_returns_201(self, t_client):
        """URL query param returns 201 with url kind."""
        resp = t_client.post("/api/upload?url=https://example.com")
        assert resp.status_code == 201
        assert resp.headers["X-Depo-Kind"] == "url"
        assert resp.headers["X-Depo-Created"] == "true"
        assert all(char in _CROCKFORD32 for char in resp.text)

    def test_raw_body_url_returns_201(self, t_client):
        """Raw body containing URL returns 201 with url kind."""
        url, head = b"https://example.com", {"content-type": "text/plain"}
        resp = t_client.post("/api/upload", content=url, headers=head)
        assert resp.status_code == 201
        assert resp.headers["X-Depo-Kind"] == "url"


class TestUploadShortcuts:
    """Tests for convenience route aliases."""

    def test_post_root_alias(self, t_client):
        """POST / routes same as /api/upload."""
        resp = t_client.post("/", files={"file": ("test.txt", b"hello root")})
        assert resp.status_code == 201
        assert resp.headers["X-Depo-Code"] == resp.text
        assert resp.headers["X-Depo-Kind"] == "txt"
        assert resp.headers["X-Depo-Created"] == "true"


class TestGetInfo:
    """Tests for GET /api/{code}/info.
    Uses t_seeded for pre-populated items, t_client for 404."""

    def test_text_item_info(self, t_seeded):
        """Text item returns metadata as plain text."""
        resp = t_seeded.client.get(f"/api/{t_seeded.txt.code}/info")
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/plain")
        assert f"code={t_seeded.txt.code}" in resp.text
        assert "kind=txt" in resp.text
        assert "format=md" in resp.text
        assert "size_b=" in resp.text

    def test_pic_item_info(self, t_seeded):
        """Pic item returns metadata including dimensions."""
        resp = t_seeded.client.get(f"/api/{t_seeded.pic.code}/info")
        assert resp.status_code == 200
        assert "kind=pic" in resp.text
        assert "width=320" in resp.text
        assert "height=240" in resp.text

    def test_link_item_info(self, t_seeded):
        """Link item returns metadata including URL."""
        resp = t_seeded.client.get(f"/api/{t_seeded.link.code}/info")
        assert resp.status_code == 200
        assert "kind=url" in resp.text
        assert "url=http://example.com" in resp.text

    def test_unknown_code_returns_404(self, t_client):
        """Unknown code returns 404."""
        assert t_client.get("/api/ZZZZZZZZ/info").status_code == 404


class TestGetRaw:
    """Tests for GET /api/{code}/raw.
    Uses t_seeded for pre-populated items, t_client for 404."""

    def test_text_returns_raw_content(self, t_seeded):
        """Text item returns raw content with text/plain MIME."""
        resp = t_seeded.client.get(f"/api/{t_seeded.txt.code}/raw")
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/plain")
        assert "charset=utf-8" in resp.headers["content-type"]
        assert b"# Hello, World!" in resp.content

    def test_pic_returns_raw_bytes(self, t_seeded):
        """Pic item returns raw bytes with correct image MIME."""
        resp = t_seeded.client.get(f"/api/{t_seeded.pic.code}/raw")
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("image/jpeg")
        assert len(resp.content) == t_seeded.pic.size_b

    def test_link_returns_redirect(self, t_seeded):
        """LinkItem returns redirect to URL."""
        endpoint = f"/api/{t_seeded.link.code}/raw"
        resp = t_seeded.client.get(endpoint, follow_redirects=False)
        assert resp.status_code == 307
        assert resp.headers["location"] == "http://example.com"

    def test_unknown_code_returns_404(self, t_client):
        """Unknown code returns 404."""
        assert t_client.get("/api/ZZZZZZZZ/raw").status_code == 404
