# tests/web/test_upload.py
"""
Tests for upload routes.

Round-trip tests for POST /api/upload, /upload, and /.

Author: Marcus Grant
Created: 2026-02-09
License: Apache-2.0
"""

from depo.util.shortcode import _CROCKFORD32
from depo.web.upload import _looks_like_url, parse_upload, upload_response
from tests.factories.web import make_client


# TODO: Needs to be moved to proper validate/classify stage of ingest pipeline
class TestLooksLikeUrl:
    """Tests for _looks_like_url() helper."""

    def test_happy_paths(self):
        """Valid URLs return True."""
        assert _looks_like_url(b"http://example.com") is True
        assert _looks_like_url(b"https://example.com") is True
        assert _looks_like_url(b"https://example.com/path/to/thing") is True
        assert _looks_like_url(b"https://example.com/page?q=search&lang=en") is True
        assert _looks_like_url(b"https://sub.domain.example.com") is True
        assert _looks_like_url(b"https://example.io") is True
        assert _looks_like_url(b"  https://example.com  ") is True  # whitespace trimmed

    def test_missing_scheme(self):
        """URLs without http(s):// scheme return False."""
        assert _looks_like_url(b"example.com") is False
        assert _looks_like_url(b"www.example.com") is False
        assert _looks_like_url(b"ftp://example.com") is False

    def test_scheme_only(self):
        """Scheme without domain returns False."""
        assert _looks_like_url(b"https://") is False
        assert _looks_like_url(b"http://") is False

    def test_no_dot_in_domain(self):
        """Domain without TLD dot returns False."""
        assert _looks_like_url(b"https://localhost") is False
        assert _looks_like_url(b"http://example") is False

    def test_whitespace_in_body(self):
        """URLs containing whitespace return False."""
        assert _looks_like_url(b"https://example.com/some path") is False
        assert _looks_like_url(b"https://example .com") is False

    def test_unsafe_characters(self):
        """URLs with non-URL-safe characters return False."""
        assert _looks_like_url(b"https://example.com/<script>") is False
        assert _looks_like_url(b"https://example.com/{bad}") is False
        assert _looks_like_url(b"https://example.com/[nope]") is False

    def test_binary_data(self):
        """Non-UTF8 binary data returns False."""
        assert _looks_like_url(b"\x89PNG\r\n\x1a\n") is False
        assert _looks_like_url(b"\xff\xd8\xff\xe0") is False

    def test_plain_text(self):
        """Ordinary text content returns False."""
        assert _looks_like_url(b"hello world") is False
        assert _looks_like_url(b"just some notes") is False
        assert _looks_like_url(b"") is False


class TestParseUpload:
    """Tests for parse_upload()."""

    # Multipart file extracts payload_bytes, filename, declared_mime
    # URL query param extracts link_url
    # Raw body extracts payload_bytes and content-type as declared_mime
    # Raw body containing URL extracts link_url
    # No file, no url, no body raises ValueError


class TestUploadResponse:
    """Tests for upload_response()."""

    # Returns 201 with short code as body
    # Sets X-Depo-Code header matching body
    # Sets X-Depo-Kind header from result item kind
    # Content-Type is text/plain
