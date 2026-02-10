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
from tests.factories.payloads import gen_image
from tests.factories.web import make_client


class TestUploadText:
    """Tests for text content upload."""

    def test_multipart_text_returns_201(self, tmp_path):
        """Multipart text upload returns 201, valid short code, metadata headers."""
        client, fname, data = make_client(tmp_path), "hello.txt", b"# Hello, World!"
        resp = client.post("/api/upload", files={"file": (fname, data)})
        assert resp.status_code == 201
        assert resp.headers["content-type"].startswith("text/plain")
        assert resp.text == resp.headers["X-Depo-Code"]
        assert resp.headers["X-Depo-Kind"] == "txt"
        assert resp.headers["X-Depo-Created"] == "true"
        assert all(char in _CROCKFORD32 for char in resp.text)
        assert len(resp.text) == 8

    def test_empty_payload_returns_400(self, tmp_path):
        """Empty file upload returns 400."""
        client = make_client(tmp_path)
        resp = client.post("/api/upload", files={"file": ("empty.txt", b"")})
        assert resp.status_code == 400

    def test_unclassifiable_returns_400(self, tmp_path):
        """Unclassifiable content returns 400 with message."""
        client = make_client(tmp_path)
        resp = client.post("/api/upload", files={"file": ("noext", b"mystery stuff")})
        assert resp.status_code == 400
        assert len(resp.text) > 0  # error message present


class TestUploadImage:
    """Tests for image content upload."""

    def test_multipart_pic_returns_201(self, tmp_path):
        """Multipart pic upload returns 201, valid, short code, meta headers"""
        fname, data = "screenshot.jpg", gen_image("jpeg", 16, 16)
        client = make_client(tmp_path)
        resp = client.post("/api/upload", files={"file": (fname, data)})
        assert resp.status_code == 201
        assert resp.headers["content-type"].startswith("text/plain")
        assert resp.text == resp.headers["X-Depo-Code"]
        assert resp.headers["X-Depo-Kind"] == "pic"
        assert resp.headers["X-Depo-Created"] == "true"
        assert all(char in _CROCKFORD32 for char in resp.text)
        assert len(resp.text) == 8

    def test_corrupt_jpeg_returns_400(self, tmp_path):
        """JPEG magic bytes without valid image data returns 400."""
        client = make_client(tmp_path)
        resp = client.post("/api/upload", files={"file": b"\xff\xd8\xff\xe0"})
        assert resp.status_code == 400
        assert len(resp.text) > 0


class TestUploadLink:
    """Tests for link/URL submission."""

    def test_url_param_returns_201(self, tmp_path):
        """URL query param returns 201 with url kind."""
        client = make_client(tmp_path)
        resp = client.post("/api/upload?url=https://example.com")
        assert resp.status_code == 201
        assert resp.headers["X-Depo-Kind"] == "url"
        assert resp.headers["X-Depo-Created"] == "true"
        assert all(char in _CROCKFORD32 for char in resp.text)

    def test_raw_body_url_returns_201(self, tmp_path):
        """Raw body containing URL returns 201 with url kind."""
        client = make_client(tmp_path)
        resp = client.post(
            "/api/upload",
            content=b"https://example.com",
            headers={"content-type": "text/plain"},
        )
        assert resp.status_code == 201
        assert resp.headers["X-Depo-Kind"] == "url"


class TestUploadShortcuts:
    """Tests for convenience route aliases."""

    def test_post_upload_alias(self, tmp_path):
        """POST /upload routes same as /api/upload."""
        client = make_client(tmp_path)
        resp = client.post("/upload", files={"file": ("test.txt", b"hello upload")})
        assert resp.status_code == 201
        assert resp.headers["X-Depo-Code"] == resp.text
        assert resp.headers["X-Depo-Kind"] == "txt"
        assert resp.headers["X-Depo-Created"] == "true"

    def test_post_root_alias(self, tmp_path):
        """POST / routes same as /api/upload."""
        client = make_client(tmp_path)
        resp = client.post("/", files={"file": ("test.txt", b"hello root")})
        assert resp.status_code == 201
        assert resp.headers["X-Depo-Code"] == resp.text
        assert resp.headers["X-Depo-Kind"] == "txt"
        assert resp.headers["X-Depo-Created"] == "true"
