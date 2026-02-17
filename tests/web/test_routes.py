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

    def test_post_root_alias(self, tmp_path):
        """POST / routes same as /api/upload."""
        client = make_client(tmp_path)
        resp = client.post("/", files={"file": ("test.txt", b"hello root")})
        assert resp.status_code == 201
        assert resp.headers["X-Depo-Code"] == resp.text
        assert resp.headers["X-Depo-Kind"] == "txt"
        assert resp.headers["X-Depo-Created"] == "true"


class TestGetInfo:
    """Tests for GET /api/{code}/info."""

    def test_text_item_info(self, tmp_path):
        """Text item returns metadata as plain text."""
        client = make_client(tmp_path)
        file = ("hello.txt", b"hello world")
        upload = client.post("/api/upload", files={"file": file})
        code = upload.text
        resp = client.get(f"/api/{code}/info")
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/plain")
        assert f"code={code}" in resp.text
        assert "kind=txt" in resp.text
        assert "format=txt" in resp.text
        assert "size_b=" in resp.text

    def test_pic_item_info(self, tmp_path):
        """Pic item returns metadata including dimensions."""
        client = make_client(tmp_path)
        file = ("img.jpg", gen_image("jpeg", 16, 16))
        upload = client.post("/api/upload", files={"file": file})
        code = upload.text
        resp = client.get(f"/api/{code}/info")
        assert resp.status_code == 200
        assert "kind=pic" in resp.text
        assert "width=16" in resp.text
        assert "height=16" in resp.text

    def test_link_item_info(self, tmp_path):
        """Link item returns metadata including URL."""
        client = make_client(tmp_path)
        upload = client.post("/api/upload?url=https://example.com")
        code = upload.text
        resp = client.get(f"/api/{code}/info")
        assert resp.status_code == 200
        assert "kind=url" in resp.text
        assert "url=https://example.com" in resp.text

    def test_unknown_code_returns_404(self, tmp_path):
        """Unknown code returns 404."""
        client = make_client(tmp_path)
        resp = client.get("/api/ZZZZZZZZ/info")
        assert resp.status_code == 404


class TestGetRaw:
    """Tests for GET /api/{code}/raw."""

    def test_text_returns_raw_content(self, tmp_path):
        """Text item returns raw content with text/plain MIME."""
        client = make_client(tmp_path)
        file = ("hello.txt", b"Hello, World!")
        upload = client.post("/api/upload", files={"file": file})
        resp = client.get(f"/api/{upload.text}/raw")  # upload.text is the code
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/plain")
        assert "charset=utf-8" in resp.headers["content-type"]
        assert resp.content == file[1]

    def test_pic_returns_raw_bytes(self, tmp_path):
        """Pic item returns raw bytes with correct image MIME."""
        client = make_client(tmp_path)
        file = ("img.jpg", gen_image("jpeg", 16, 16))
        upload = client.post("/api/upload", files={"file": file})
        resp = client.get(f"/api/{upload.text}/raw")
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("image/jpeg")
        assert len(resp.content) > 0

    def test_link_returns_redirect(self, tmp_path):
        """LinkItem returns redirect to URL."""
        client = make_client(tmp_path)
        upload = client.post("/api/upload?url=https://example.com")
        resp = client.get(f"/api/{upload.text}/raw", follow_redirects=False)
        assert resp.status_code == 307
        assert resp.headers["location"] == "https://example.com"

    def test_unknown_code_returns_404(self, tmp_path):
        """Unknown code returns 404."""
        client = make_client(tmp_path)
        resp = client.get("/api/ZZZZZZZZ/raw")
        assert resp.status_code == 404
