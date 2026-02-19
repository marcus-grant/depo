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
from depo.web.upload import parse_form_upload, parse_upload, upload_response
from tests.factories import make_persist_result


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
    async def test_url_param_extracts_payload_bytes(self):
        """URL query param extracts links to payload_bytes."""
        result = dict(await parse_upload(file=None, url="http://a.eu", request=None))
        assert result["payload_bytes"] == b"http://a.eu"
        assert result["declared_mime"] is None

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
    async def test_no_input_raises(self):
        """No file, no url, no body raises ValueError."""
        with pytest.raises(ValueError, match="routing bug"):
            await parse_upload(file=None, url=None, request=None)


@pytest.mark.asyncio
class TestParseFormUpload:
    """Parse browser form fields into orchestrator kwargs."""

    async def _test_fn(self, content: str, fmt: str) -> dict:
        req = MagicMock()
        req.form = AsyncMock(return_value={"content": content, "format": fmt})
        return dict(await parse_form_upload(req))

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
