# tests/web/routes/test_upload.py
"""
Tests for upload route handlers.
Covers POST /upload dispatch, GET /upload page render,
HTMX partial responses, API uploads, and request parsing.
Author: Marcus Grant
Created: 2026-02-23
License: Apache-2.0
"""

from io import BytesIO
from unittest.mock import AsyncMock, MagicMock

import pytest
from bs4 import BeautifulSoup
from fastapi import UploadFile
from starlette.datastructures import Headers

from depo.model.enums import ContentFormat
from depo.model.formats import ItemKind, kind_for_format
from depo.util.shortcode import _CROCKFORD32
from depo.web.routes.upload import _parse_form_upload, _parse_upload, _upload_response
from tests.factories import HEADER_HTMX, gen_image, make_persist_result


def _assert_api_upload_created(resp, expected_kind: ItemKind):
    """Assert standard API upload 201 response shape."""
    msg = f"status={resp.status_code} body={resp.text}"
    assert resp.status_code == 201, msg
    ct = resp.headers["content-type"]
    assert ct.startswith("text/plain"), f"content-type: {ct}"
    assert resp.text == resp.headers["X-Depo-Code"], "body != X-Depo-Code"
    kind = resp.headers.get("X-Depo-Kind")
    assert kind == expected_kind, f"kind={kind} != {expected_kind}"
    assert resp.headers["X-Depo-Created"] == "true"
    assert all(c in _CROCKFORD32 for c in resp.text), f"bad chars: {resp.text}"
    assert len(resp.text) == 8, f"len={len(resp.text)} != 8"


class TestUploadDispatch:
    """POST /upload dispatches by request context.
    HX-Request routes to HTMX partial handler,
    default routes to API plaintext handler.
    """

    def test_post_root_alias(self, t_client):
        """POST / routes same as /upload."""
        resp = t_client.post("/", files={"file": ("test.txt", b"hello root")})
        _assert_api_upload_created(resp, ItemKind.TEXT)

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


class TestUploadText:
    """Tests for text content upload."""

    def test_multipart_text_returns_201(self, t_client):
        """Multipart text upload returns 201, valid short code, metadata headers."""
        resp = t_client.post("/upload", files={"file": ("test.txt", b"hello world")})
        _assert_api_upload_created(resp, ItemKind.TEXT)

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
        _assert_api_upload_created(resp, ItemKind.PICTURE)

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
        _assert_api_upload_created(resp, ItemKind.LINK)

    def test_raw_body_url_returns_201(self, t_client):
        """Raw body containing URL returns 201 with url kind."""
        url, head = b"https://example.com", {"content-type": "text/plain"}
        resp = t_client.post("/upload?format=url", content=url, headers=head)
        assert resp.status_code == 201
        assert resp.headers["X-Depo-Kind"] == "url"


class TestUploadFormat:
    """Format override precedence: query param > header > auto."""

    @pytest.mark.skip(reason="Needs X-Depo-Format response header")
    @pytest.mark.parametrize(
        "query,headers,expected_fmt",
        [
            ("?format=md", {}, "md"),
            ("", {"X-Depo-Format": "yaml"}, "yaml"),
            ("?format=md", {"X-Depo-Format": "yaml"}, "md"),
        ],
        ids=["query-overrides-auto", "header-overrides-auto", "query-beats-header"],
    )
    def test_api_format_precedence(self, t_client, query, headers, expected_fmt):
        """Plaintext content with competing format signals resolves by precedence.
        Auto-classification would choose plaintext. Query param and header
        each override auto, and query param wins when both are present.
        """
        resp = t_client.post(f"/upload{query}", content=b"plaintext", headers=headers)
        assert resp.status_code == 201
        assert resp.headers["X-Depo-Format"] == expected_fmt

    @pytest.mark.skip(reason="No format visibility in success partial yet")
    def test_user_format_overrides_classification(self, t_htmx):
        """HTMX User selects markdown for plaintext content.
        Form format field overrides classifier's auto-detect."""
        resp = t_htmx.post("/upload", data={"content": "plaintext", "format": "md"})
        code = BeautifulSoup(resp.text, "html.parser").find("code", class_="shortcode")
        assert code is not None, "missing shortcode element"
        assert "format=md" in t_htmx.get(f"/{code.text.strip()}/info").text


class TestGetUploadPage:
    """GET /upload serves the upload form"""

    def test_returns_200_and_html_content(self, t_client):
        resp = t_client.get(url="/upload")
        assert resp.status_code == 200
        assert resp.headers.get("content-type") == "text/html; charset=utf-8"

    def test_returns_expected_html(self, t_client):
        """Returns template markers, form elements & content-type overrides"""
        resp = t_client.get(url="/upload")
        assert "<!-- BEGIN: upload.html -->" in resp.text
        assert "<!-- END: upload.html -->" in resp.text
        soup = BeautifulSoup(resp.text, "html.parser")
        assert soup.find("form", attrs={"method": "post", "action": "/upload"})
        assert soup.find("textarea", attrs={"name": "content"})
        assert soup.find("select", attrs={"name": "format"})
        button = soup.find("button", attrs={"type": "submit"})
        input_submit = soup.find("input", attrs={"type": "submit"})
        assert button or input_submit
        assert soup.find_all("optgroup")

    def test_format_select_covers_all_formats(self, t_client):
        """Upload form has an option for every ContentFormat."""
        soup = BeautifulSoup(t_client.get("/upload").text, "html.parser")
        select = soup.find("select", attrs={"name": "format"})
        assert select is not None
        options = set()
        for opt in select.find_all("option"):
            val = str(opt.get("value", ""))
            if val:
                options.add(val)
        expected = {f.value for f in ContentFormat}
        assert options == expected, f"Missing: {expected - options}"


class TestHtmxUploadSuccess:
    """POST /upload with HX-Request returns success partial.
    Makes use of t_client fixture and module constant _HEADER_HX"""

    def test_success_returns_shortcode(self, t_htmx):
        """Success partial contains a non-empty shortcode element."""
        resp = t_htmx.post("/upload", data={"content": "foobar", "format": ""})
        assert resp.status_code == 200
        code = BeautifulSoup(resp.text, "html.parser").find("code", class_="shortcode")
        assert code is not None
        assert len(code.text.strip()) > 0

    def test_success_contains_info_link(self, t_htmx):
        """Success partial links to the info page for the uploaded item."""
        resp = t_htmx.post("/upload", data={"content": "foobar", "format": ""})
        soup = BeautifulSoup(resp.text, "html.parser")
        code = soup.find("code", class_="shortcode").text.strip()  # type: ignore
        assert soup.find("a", href=f"/{code}/info") is not None

    def test_success_is_fragment(self, t_htmx):
        """Success partial is not wrapped in base template."""
        resp = t_htmx.post("/upload", data={"content": "hello world", "format": ""})
        assert "<!-- BEGIN: base.html -->" not in resp.text
        assert "<!-- BEGIN: partials/success.html" in resp.text


class TestHtmxUploadError:
    """POST /upload with HX-Request returns error partial on failure."""

    def test_empty_content_returns_error(self, t_htmx):
        """Empty content submission renders an error div."""
        resp = t_htmx.post("/upload", data={"content": "", "format": ""})
        assert resp.status_code == 200
        soup = BeautifulSoup(resp.text, "html.parser")
        assert soup.find("div", class_="upload-error") is not None

    def test_error_contains_message(self, t_htmx):
        """Error partial includes a descriptive error message."""
        resp = t_htmx.post("/upload", data={"content": "", "format": ""})
        assert "No content provided" in resp.text

    def test_error_is_fragment(self, t_htmx):
        """Error partial is not wrapped in base template."""
        resp = t_htmx.post("/upload", data={"content": "", "format": ""})
        assert "<!-- BEGIN: base.html -->" not in resp.text
        assert "<!-- BEGIN: partials/error.html" in resp.text


@pytest.mark.asyncio
class TestParseUpload:
    """Tests for parse_upload()."""

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

    async def test_url_param_extracts_payload_bytes(self):
        """URL query param extracts links to payload_bytes."""
        result = dict(await _parse_upload(file=None, url="http://a.eu", request=None))
        assert result["payload_bytes"] == b"http://a.eu"
        assert result["declared_mime"] is None

    async def test_raw_body_extracts_payload(self):
        """Raw body extracts payload_bytes and declared_mime."""
        mock_request = AsyncMock()
        mock_request.body.return_value = b"some raw content"
        mock_request.headers = Headers({"content-type": "application/octet-stream"})
        result = dict(await _parse_upload(file=None, url=None, request=mock_request))
        assert result["payload_bytes"] == b"some raw content"
        assert result["declared_mime"] == "application/octet-stream"
        assert "link_url" not in result

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

    async def test_textarea_content_extracts_payload(self):
        """Textarea content is extracted as payload_bytes."""
        result = await self._test_fn("hello", "")
        assert result["payload_bytes"] == b"hello"

    async def test_request_format_for_select_option(self):
        """Select options form for format returns correct requested_format."""
        cf_txt, cf_md = ContentFormat.PLAINTEXT, ContentFormat.MARKDOWN
        assert (await self._test_fn("hello", ""))["requested_format"] is None
        assert (await self._test_fn("hello", "txt"))["requested_format"] == cf_txt
        assert (await self._test_fn("hello", "md"))["requested_format"] == cf_md

    async def test_declared_mime_is_plaintext(self):
        """Form content always declares text/plain mime."""
        result = await self._test_fn("hello", "")
        assert result["declared_mime"] == "text/plain"

    @pytest.mark.parametrize("content", ["", "   "], ids=["empty", "whitespace"])
    async def test_empty_content_raises(self, content):
        """Empty or whitespace-only textarea raises ValueError."""
        with pytest.raises(ValueError, match="No content provided"):
            await self._test_fn(content, "")


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
