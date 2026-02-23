# tests/web/test_upload.py
"""
Tests for upload routes.

Round-trip tests for POST /api/upload, /upload, and /.

Author: Marcus Grant
Created: 2026-02-09
License: Apache-2.0
"""

from io import BytesIO
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import UploadFile
from starlette.datastructures import Headers

from depo.model.enums import ContentFormat
from depo.util.shortcode import _CROCKFORD32
from depo.web.routes.upload import _parse_form_upload, _parse_upload, _upload_response
from tests.factories import HEADER_HTMX, gen_image, make_persist_result


class TestUploadText:
    """Tests for text content upload."""

    def test_multipart_text_returns_201(self, t_client):
        """Multipart text upload returns 201, valid short code, metadata headers."""
        resp = t_client.post("/upload", files={"file": ("hello.txt", b"Hello!")})
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
        assert t_client.post("/upload", files=file).status_code == 400

    def test_unclassifiable_returns_400(self, t_client):
        """Unclassifiable content returns 400 with message."""
        resp = t_client.post("/upload", files={"file": ("noext", b"\xff\xfe\xfd")})
        assert resp.status_code == 400
        assert len(resp.text) > 0  # error message present


class TestUploadImage:
    """Tests for image content upload."""

    def test_multipart_pic_returns_201(self, t_client):
        """Multipart pic upload returns 201, valid, short code, meta headers"""
        file = {"file": ("screenshot.jpg", gen_image("jpeg", 16, 16))}
        resp = t_client.post("/upload", files=file)
        assert resp.status_code == 201
        assert resp.headers["content-type"].startswith("text/plain")
        assert resp.text == resp.headers["X-Depo-Code"]
        assert resp.headers["X-Depo-Kind"] == "pic"
        assert resp.headers["X-Depo-Created"] == "true"
        assert all(char in _CROCKFORD32 for char in resp.text)
        assert len(resp.text) == 8

    def test_corrupt_jpeg_returns_400(self, t_client):
        """JPEG magic bytes without valid image data returns 400."""
        resp = t_client.post("/upload", files={"file": b"\xff\xd8\xff\xe0"})
        assert resp.status_code == 400
        assert len(resp.text) > 0


class TestUploadLink:
    """Tests for link/URL submission."""

    def test_url_param_returns_201(self, t_client):
        """URL query param returns 201 with url kind."""
        resp = t_client.post("/upload?url=https://example.com")
        assert resp.status_code == 201
        assert resp.headers["X-Depo-Kind"] == "url"
        assert resp.headers["X-Depo-Created"] == "true"
        assert all(char in _CROCKFORD32 for char in resp.text)

    def test_raw_body_url_returns_201(self, t_client):
        """Raw body containing URL returns 201 with url kind."""
        url, head = b"https://example.com", {"content-type": "text/plain"}
        resp = t_client.post("/upload?format=url", content=url, headers=head)
        assert resp.status_code == 201
        assert resp.headers["X-Depo-Kind"] == "url"


class TestUploadFormat:
    """Tests for API format override via query param and X-Depo-Format header."""

    def test_format_query_param_overrides_classification(self, t_client):
        """Query param format overrides automatic classification."""
        data, head = b"# Hello", {"content-type": "text/plain"}
        resp = t_client.post("/upload?format=md", content=data, headers=head)
        assert resp.status_code == 201
        assert resp.headers["X-Depo-Kind"] == "txt"

    def test_format_header_overrides_classification(self, t_client):
        """X-Depo-Format header overrides automatic classification."""
        data, head = b"# Hello", {"X-Depo-Format": "md"}
        resp = t_client.post("/upload", content=data, headers=head)
        assert resp.status_code == 201
        assert resp.headers["X-Depo-Kind"] == "txt"

    def test_format_query_param_wins_over_header(self, t_client):
        """Query param takes precedence over header."""
        data, head = b"key: value", {"X-Depo-Format": "json"}
        resp = t_client.post("/upload?format=yaml", content=data, headers=head)
        assert resp.status_code == 201
        assert resp.headers["X-Depo-Kind"] == "txt"


class TestUploadShortcuts:
    """Tests for convenience route aliases."""

    def test_post_root_alias(self, t_client):
        """POST / routes same as /upload."""
        resp = t_client.post("/", files={"file": ("test.txt", b"hello root")})
        assert resp.status_code == 201
        assert resp.headers["X-Depo-Code"] == resp.text
        assert resp.headers["X-Depo-Kind"] == "txt"
        assert resp.headers["X-Depo-Created"] == "true"


class TestUploadDispatch:
    """POST /upload dispatches by request context.
    HX-Request routes to HTMX partial handler,
    default routes to API plaintext handler.
    """

    def test_htmx_request_returns_html_partial(self, t_client):
        """HX-Request header triggers HTMX partial response."""
        data = {"content": "hello dispatch", "format": "txt"}
        resp = t_client.post("/upload", data=data, headers=HEADER_HTMX)
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]

    def test_default_request_returns_plaintext(self, t_client):
        """No HX-Request header triggers API plaintext response."""
        resp = t_client.post("/upload", files={"file": ("test.txt", b"hello dispatch")})
        assert resp.status_code == 201
        assert "text/plain" in resp.headers["content-type"]
        assert "X-Depo-Code" in resp.headers


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
        result = dict(await _parse_upload(file=file, url=None, request=None))
        assert result["payload_bytes"] == b"hello world"
        assert result["filename"] == "hello.txt"
        assert result["declared_mime"] == "text/plain"

    @pytest.mark.asyncio
    async def test_url_param_extracts_payload_bytes(self):
        """URL query param extracts links to payload_bytes."""
        result = dict(await _parse_upload(file=None, url="http://a.eu", request=None))
        assert result["payload_bytes"] == b"http://a.eu"
        assert result["declared_mime"] is None

    @pytest.mark.asyncio
    async def test_raw_body_extracts_payload(self):
        """Raw body extracts payload_bytes and declared_mime."""
        mock_request = AsyncMock()
        mock_request.body.return_value = b"some raw content"
        mock_request.headers = Headers({"content-type": "application/octet-stream"})
        result = dict(await _parse_upload(file=None, url=None, request=mock_request))
        assert result["payload_bytes"] == b"some raw content"
        assert result["declared_mime"] == "application/octet-stream"
        assert "link_url" not in result

    @pytest.mark.asyncio
    async def test_no_input_raises(self):
        """No file, no url, no body raises ValueError."""
        with pytest.raises(ValueError, match="routing bug"):
            await _parse_upload(file=None, url=None, request=None)


@pytest.mark.asyncio
class TestParseFormUpload:
    """Parse browser form fields into orchestrator kwargs."""

    async def _test_fn(self, content: str, fmt: str) -> dict:
        req = MagicMock()
        req.form = AsyncMock(return_value={"content": content, "format": fmt})
        return dict(await _parse_form_upload(req))

    @pytest.mark.asyncio
    async def test_textarea_content_extracts_payload(self):
        """Textarea content is extracted as payload_bytes."""
        result = await self._test_fn("hello", "")
        assert result["payload_bytes"] == b"hello"

    @pytest.mark.asyncio
    async def test_request_format_for_select_option(self):
        """Select options form for format returns correct requested_format."""
        cf_txt, cf_md = ContentFormat.PLAINTEXT, ContentFormat.MARKDOWN
        assert (await self._test_fn("hello", ""))["requested_format"] is None
        assert (await self._test_fn("hello", "txt"))["requested_format"] == cf_txt
        assert (await self._test_fn("hello", "md"))["requested_format"] == cf_md

    @pytest.mark.asyncio
    async def test_empty_content_raises(self):
        """Empty textarea raises ValueError."""
        with pytest.raises(ValueError, match="No content provided"):
            await self._test_fn("", "")

    @pytest.mark.asyncio
    async def test_whitespace_content_raises(self):
        """Whitespace-only textarea raises ValueError."""
        with pytest.raises(ValueError, match="No content provided"):
            await self._test_fn("   ", "")

    @pytest.mark.asyncio
    async def test_declared_mime_is_plaintext(self):
        """Form content always declares text/plain mime."""
        result = await self._test_fn("hello", "")
        assert result["declared_mime"] == "text/plain"


class TestUploadResponse:
    """Tests for upload_response()."""

    def test_returns_201_with_code(self):
        """Returns 201 with short code as plain text body."""
        result = make_persist_result()
        resp = _upload_response(result)
        assert resp.status_code == 201
        assert resp.body == b"01234567"
        assert resp.headers["content-type"].startswith("text/plain")
        assert resp.headers["X-Depo-Code"] == "01234567"
        assert resp.headers["X-Depo-Kind"] == "txt"
        assert resp.headers["X-Depo-Created"] == "true"

    def test_dedupe_returns_200(self):
        """Duplicate upload returns 200 with same code and created=false header."""
        result = make_persist_result(created=False)
        resp = _upload_response(result)
        assert resp.status_code == 200
        assert resp.body == b"01234567"
        assert resp.headers["X-Depo-Code"] == "01234567"
        assert resp.headers["X-Depo-Kind"] == "txt"
        assert resp.headers["X-Depo-Created"] == "false"
