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

    # Empty payload returns 400
    # Classification failure returns 400 with message


class TestUploadImage:
    """Tests for image content upload."""

    # Multipart image upload returns 201 with short code


class TestUploadLink:
    """Tests for link/URL submission."""

    # Query param url= returns 201 with short code
    # Raw body containing URL is detected as link


class TestUploadShortcuts:
    """Tests for convenience route aliases."""

    # POST /upload works same as /api/upload
    # POST / works same as /api/upload
