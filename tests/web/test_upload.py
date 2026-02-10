# tests/web/test_upload.py
"""
Tests for upload routes.

Round-trip tests for POST /api/upload, /upload, and /.

Author: Marcus Grant
Created: 2026-02-09
License: Apache-2.0
"""

from io import BytesIO
from unittest.mock import AsyncMock

import pytest
from fastapi import UploadFile
from starlette.datastructures import Headers

from depo.web.upload import _looks_like_url, parse_upload, upload_response
from tests.factories.dto import make_persist_result


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

    @pytest.mark.asyncio
    async def test_multipart_extracts_kwargs(self):
        """Multipart file extracts payload_bytes, filename, declared_mime."""
        file = UploadFile(
            filename="hello.txt",
            file=BytesIO(b"hello world"),
            headers=Headers({"content-type": "text/plain"}),
        )
        result = dict(await parse_upload(file=file, url=None, request=None))
        assert result["payload_bytes"] == b"hello world"
        assert result["filename"] == "hello.txt"
        assert result["declared_mime"] == "text/plain"

    @pytest.mark.asyncio
    async def test_url_param_extracts_link_url(self):
        """URL query param extracts link_url."""
        result = dict(await parse_upload(file=None, url="http://a.eu", request=None))
        assert result["link_url"] == "http://a.eu"
        assert "payload_bytes" not in result

    @pytest.mark.asyncio
    async def test_raw_body_extracts_payload(self):
        """Raw body extracts payload_bytes and declared_mime."""
        mock_request = AsyncMock()
        mock_request.body.return_value = b"some raw content"
        mock_request.headers = Headers({"content-type": "application/octet-stream"})
        result = dict(await parse_upload(file=None, url=None, request=mock_request))
        assert result["payload_bytes"] == b"some raw content"
        assert result["declared_mime"] == "application/octet-stream"
        assert "link_url" not in result

    @pytest.mark.asyncio
    async def test_raw_body_url_detected_as_link(self):
        """Raw body containing URL extracts link_url instead of payload_bytes."""
        mock_request = AsyncMock()
        mock_request.body.return_value = b"https://example.com"
        mock_request.headers = Headers({"content-type": "text/plain"})
        result = dict(await parse_upload(file=None, url=None, request=mock_request))
        assert result["link_url"] == "https://example.com"
        assert "payload_bytes" not in result

    @pytest.mark.asyncio
    async def test_no_input_raises(self):
        """No file, no url, no body raises ValueError."""
        with pytest.raises(ValueError, match="routing bug"):
            await parse_upload(file=None, url=None, request=None)


class TestUploadResponse:
    """Tests for upload_response()."""

    def test_returns_201_with_code(self):
        """Returns 201 with short code as plain text body."""
        result = make_persist_result()
        resp = upload_response(result)
        assert resp.status_code == 201
        assert resp.body == b"01234567"
        assert resp.headers["content-type"].startswith("text/plain")
        assert resp.headers["X-Depo-Code"] == "01234567"
        assert resp.headers["X-Depo-Kind"] == "txt"
        assert resp.headers["X-Depo-Created"] == "true"

    def test_dedupe_returns_200(self):
        """Duplicate upload returns 200 with same code and created=false header."""
        result = make_persist_result(created=False)
        resp = upload_response(result)
        assert resp.status_code == 200
        assert resp.body == b"01234567"
        assert resp.headers["X-Depo-Code"] == "01234567"
        assert resp.headers["X-Depo-Kind"] == "txt"
        assert resp.headers["X-Depo-Created"] == "false"
