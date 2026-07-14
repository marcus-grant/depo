# tests/web/routes/test_upload.py
"""
Tests for upload route handlers.
Covers POST /upload dispatch, GET /upload page render,
HTMX partial responses, API uploads, and request parsing.
Author: Marcus Grant
Created: 2026-02-23
Revised: [2026-06-09]
License: Apache-2.0
"""

from io import BytesIO
from unittest.mock import AsyncMock, MagicMock

import pytest
from bs4 import BeautifulSoup
from fastapi import UploadFile
from httpx import Response
from starlette.datastructures import Headers
from starlette.testclient import TestClient

from depo.cli import defaults
from depo.model.enums import ContentFormat
from depo.model.formats import ItemKind
from depo.util import errors
from depo.util.shortcode import _CROCKFORD32
from depo.web.routes.upload import _parse_form_upload, _parse_upload, _upload_response
from tests.factories import HEADER_BROWSER, HEADER_HTMX, gen_image, make_persist_result


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

    def test_post_root_alias(self, t_user: TestClient):
        """POST / routes same as /upload."""
        resp = t_user.post("/", files={"file": ("test.txt", b"hello root")})
        _assert_api_upload_created(resp, ItemKind.TEXT)

    def test_htmx_request_returns_html_partial(self, t_user: TestClient):
        """HX-Request header triggers HTMX partial response."""
        data = {"content": "hello dispatch", "format": "txt"}
        resp = t_user.post("/upload", data=data, headers=HEADER_HTMX)
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]

    def test_default_request_returns_plaintext(self, t_user: TestClient):
        """No HX-Request header triggers API plaintext response."""
        resp = t_user.post("/upload", files={"file": ("test.txt", b"hello dispatch")})
        assert resp.status_code == 201
        assert "text/plain" in resp.headers["content-type"]
        assert "X-Depo-Code" in resp.headers


class TestUploadText:
    """Tests for text content upload."""

    def test_multipart_text_returns_201(self, t_user: TestClient):
        """Multipart text upload returns 201, valid short code, metadata headers."""
        resp = t_user.post("/upload", files={"file": ("test.txt", b"hello world")})
        _assert_api_upload_created(resp, ItemKind.TEXT)

    def test_empty_payload_returns_400(self, t_user: TestClient):
        """Empty file upload returns 400."""
        file = {"file": ("0.txt", b"")}
        assert t_user.post("/upload", files=file).status_code == 400

    def test_unclassifiable_returns_422(self, t_user: TestClient):
        """Unclassifiable content returns 400 with message."""
        resp = t_user.post("/upload", files={"file": ("noext", b"\xff\xfe\xfd")})
        assert resp.status_code == 422
        assert len(resp.text) > 0  # error message present


class TestUploadImage:
    """Tests for image content upload."""

    def test_multipart_pic_returns_201(self, t_user: TestClient):
        """Multipart pic upload returns 201, valid, short code, meta headers"""
        file = {"file": ("p.jpg", gen_image("jpeg", 16, 16))}
        resp = t_user.post("/upload", files=file)
        _assert_api_upload_created(resp, ItemKind.PICTURE)

    def test_corrupt_jpeg_returns_422(self, t_user: TestClient):
        """JPEG magic bytes without valid image data returns 400."""
        resp = t_user.post("/upload", files={"file": b"\xff\xd8\xff\xe0"})
        assert resp.status_code == 422
        assert len(resp.text) > 0


class TestUploadLink:
    """Tests for link/URL submission."""

    def test_url_param_returns_201(self, t_user: TestClient):
        """URL query param returns 201 with url kind."""
        resp = t_user.post("/upload?url=https://example.com")
        _assert_api_upload_created(resp, ItemKind.LINK)

    def test_raw_body_url_returns_201(self, t_user: TestClient):
        """Raw body containing URL returns 201 with url kind."""
        url, head = b"https://example.com", {"content-type": "text/plain"}
        resp = t_user.post("/upload?format=url", content=url, headers=head)
        assert resp.status_code == 201
        assert resp.headers["X-Depo-Kind"] == "url"


class TestUploadFormat:
    """Format override precedence: query param > header > auto."""

    @pytest.mark.parametrize(
        "query,headers,expected_fmt",
        [
            ("?format=md", {}, "md"),
            ("", {"X-Depo-Format": "yaml"}, "yaml"),
            ("?format=md", {"X-Depo-Format": "yaml"}, "md"),
        ],
        ids=["query-overrides-auto", "header-overrides-auto", "query-beats-header"],
    )
    def test_api_format_precedence(self, t_user, query, headers, expected_fmt):
        """Plaintext content with competing format signals resolves by precedence.
        Auto-classification would choose plaintext. Query param and header
        each override auto, and query param wins when both are present.
        """
        resp = t_user.post(f"/upload{query}", content=b"plaintext", headers=headers)
        assert resp.status_code == 201
        assert resp.headers["X-Depo-Format"] == expected_fmt

    def test_user_format_overrides_classification(self, t_user: TestClient):
        """HTMX User selects markdown for plaintext content.
        Form format field overrides classifier's auto-detect."""
        data = {"content": "plaintext", "format": "md"}
        resp = t_user.post("/upload", data=data, headers=HEADER_HTMX)
        code = BeautifulSoup(resp.text, "html.parser").find("code", class_="shortcode")
        assert code is not None, "missing shortcode element"
        info = t_user.get(f"/{code.text.strip()}/info")
        assert "format=md" in info.text


class TestGetUploadPage:
    """GET /upload serves the upload form"""

    def select(self, selector, client):
        """Test helper requests from /upload and parses using soup selector."""
        resp = client.get("/upload")
        return BeautifulSoup(resp.text, "html.parser").select(selector)

    def test_returns_200_and_html_content(self, t_logged_in):
        resp = t_logged_in.get(url="/upload")
        assert resp.status_code == 200
        assert resp.headers.get("content-type") == "text/html; charset=utf-8"

    def test_returns_expected_html(self, t_logged_in):
        """Returns template markers, form elements & content-type overrides"""
        resp = t_logged_in.get(url="/upload")
        assert "<!-- BEGIN: upload/page.html" in resp.text
        assert "<!-- END: upload/page.html" in resp.text
        soup = BeautifulSoup(resp.text, "html.parser")
        assert soup.find("form", attrs={"method": "post", "action": "/upload"})
        assert soup.find("textarea", attrs={"name": "content"})
        assert soup.find("select", attrs={"name": "format"})
        button = soup.find("button", attrs={"type": "submit"})
        input_submit = soup.find("input", attrs={"type": "submit"})
        assert button or input_submit
        assert soup.find_all("optgroup")

    def test_format_select_covers_all_formats(self, t_logged_in):
        """Upload form has an option for every ContentFormat."""
        soup = BeautifulSoup(t_logged_in.get("/upload").text, "html.parser")
        select = soup.find("select", attrs={"name": "format"})
        assert select is not None
        options = set()
        for opt in select.find_all("option"):
            val = str(opt.get("value", ""))
            if val:
                options.add(val)
        expected = {f.value for f in ContentFormat}
        assert options == expected, f"Missing: {expected - options}"

    def test_has_file_input(self, t_logged_in):
        """Form includes a hidden file input for image uploads."""
        soup = BeautifulSoup(t_logged_in.get("/upload").text, "html.parser")
        finput = soup.find("input", attrs={"type": "file", "name": "file"})
        assert finput is not None
        hidden, style = finput.get("hidden"), finput.get("style") == "display:none"
        assert (hidden is not None) or (style == "display:none")

    def test_has_file_input_label(self, t_logged_in):
        """Form has a visible label triggering the file input."""
        soup = BeautifulSoup(t_logged_in.get("/upload").text, "html.parser")
        finput = soup.find("input", attrs={"type": "file", "name": "file"})
        label = soup.find("label", attrs={"for": finput.get("id")})  # type:ignore
        assert label is not None

    def test_has_attachment_card(self, t_logged_in):
        """Form includes an attachment preview container, hidden by default."""
        soup = BeautifulSoup(t_logged_in.get("/upload").text, "html.parser")
        card = soup.find(class_="attachment-card")
        assert card is not None


_HTMX_DEFAULT_DATA = {"content": "hello world", "format": "txt"}


class TestHtmxUploadSuccess:
    """POST /upload with HX-Request returns success partial.
    Makes use of t_user fixture and module constant HEADER_HTMX for auth'd htmx requests
    """

    def _act(
        self,
        client: TestClient,
        data: dict | None = None,
        files: dict | None = None,
    ) -> Response:
        """Performs main test assembly and act using a test client and data dict.
        Returns the response object when /upload request is made."""
        data = data if data is not None else _HTMX_DEFAULT_DATA
        return client.post("/upload", headers=HEADER_HTMX, data=data, files=files)

    def test_success_returns_shortcode(self, t_user: TestClient):
        """Success partial contains a non-empty shortcode element."""
        assert (resp := self._act(t_user)).status_code == 200
        code = BeautifulSoup(resp.text, "html.parser").find("code", class_="shortcode")
        assert code is not None
        assert len(code.text.strip()) > 0

    def test_success_contains_info_link(self, t_user: TestClient):
        """Success partial links to the info page for the uploaded item."""
        soup = BeautifulSoup(self._act(t_user).text, "html.parser")
        code = soup.find("code", class_="shortcode").text.strip()  # type: ignore
        assert soup.find("a", href=f"/{code}/info") is not None

    def test_success_is_fragment(self, t_user: TestClient):
        """Success partial is not wrapped in base template."""
        assert "<!-- BEGIN: base.html -->" not in (resp := self._act(t_user)).text
        assert "<!-- BEGIN: partials/success.html" in resp.text

    def test_file_upload_returns_shortcode(self, t_user: TestClient):
        """File upload via form returns success partial with shortcode."""
        files = {"file": ("pic.jpg", gen_image("jpeg", 16, 16), "image/jpeg")}
        resp = self._act(t_user, data={"content": "", "format": ""}, files=files)
        code = BeautifulSoup(resp.text, "html.parser").find("code", class_="shortcode")
        assert resp.status_code == 200
        assert code is not None


class TestHtmxUploadError:
    """POST /upload with HX-Request returns error partial on failure."""

    def _act(self, client: TestClient) -> Response:
        """Uses test client to POST empty content and format to
        /upload with HX-Request header."""
        data = {"content": "", "format": ""}
        return client.post("/upload", headers=HEADER_HTMX, data=data)

    def test_empty_content_returns_error(self, t_user: TestClient):
        """Empty content submission renders an error div."""
        assert (resp := self._act(t_user)).status_code == 200
        soup = BeautifulSoup(resp.text, "html.parser")
        assert soup.find("div", class_="error") is not None

    def test_error_contains_message(self, t_user: TestClient):
        """Error partial includes a descriptive error message."""
        assert all(s in self._act(t_user).text.lower() for s in ["empty", "payload"])

    def test_error_is_fragment(self, t_user: TestClient):
        """Error partial is not wrapped in base template."""
        assert "<!-- BEGIN: base.html -->" not in (resp := self._act(t_user)).text
        assert "<!-- BEGIN: errors/partial.html" in resp.text


class TestApiUploadError:
    """Tests for API upload error responses."""

    def test_oversized_returns_413(self, t_user: TestClient):
        """API upload exceeding max size returns 413."""
        payload = b"x" * (defaults.MAX_SIZE_BYTES + 1)
        resp = t_user.post("/upload", files={"file": ("big.txt", payload)})
        assert resp.status_code == 413

    def test_bad_format_token_returns_422(self, t_user: TestClient):
        """API upload with unknown format token returns 422."""
        resp = t_user.post("/upload", content=b"hello", params={"format": "???"})
        assert resp.status_code == 422


class TestFormFallbackError:
    """Non-HTMX form POST renders full-page browser_error on domain errors."""

    def _act(self, client: TestClient, data: dict) -> Response:
        """POSTs form data to /upload as a browser, no HX-Request header.
        Returns the response object."""
        return client.post("/upload", headers=HEADER_BROWSER, data=data)

    def _assert_page_error(self, resp: Response, status: int) -> None:
        """Asserts the response is a full-page HTML error at the given status."""
        assert resp.status_code == status
        assert "text/html" in resp.headers["content-type"]
        assert "BEGIN: errors/page.html#content" in resp.text

    def test_empty_content_renders_page_error(self, t_user: TestClient):
        """Empty non-HTMX form POST renders full-page HTML error at 400."""
        self._assert_page_error(self._act(t_user, {"content": "", "format": ""}), 400)

    def test_oversized_renders_page_error(self, t_user: TestClient):
        """Oversized non-HTMX form POST renders full-page HTML error at 413."""
        payload = "x" * (defaults.MAX_SIZE_BYTES + 1)
        data = {"content": payload, "format": ""}
        self._assert_page_error(self._act(t_user, data), 413)

    def test_bad_format_renders_page_error(self, t_user: TestClient):
        """Bad format token on nonHTMX form POST renders fullpage HTML error @ 422"""
        data = {"content": "hello", "format": "bogus"}
        self._assert_page_error(self._act(t_user, data), 422)


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
        with pytest.raises(errors.PayloadSourceError, match="file.*url.*request"):
            await _parse_upload(file=None, url=None, request=None)

    def test_missing_dependency_returns_error(self, t_user: TestClient, monkeypatch):
        """Missing Pillow dependency returns error partial with message."""
        monkeypatch.setattr("depo.service.media._HAS_PILLOW", False)
        file = {"file": ("photo.jpg", gen_image("jpeg", 16, 16))}
        resp = t_user.post("/upload", files=file, headers=HEADER_HTMX)
        assert resp.status_code == 200
        soup = BeautifulSoup(resp.text, "html.parser")
        assert soup.find("div", class_="error") is not None
        assert "pillow" in resp.text.lower() or "depend" in resp.text.lower()


@pytest.mark.asyncio
class TestParseFormUpload:
    """Parse browser form fields into orchestrator kwargs."""

    async def _test_fn(self, content: str, fmt: str) -> dict:
        req = MagicMock()
        req.form = AsyncMock(return_value={"content": content, "format": fmt})
        return dict(await _parse_form_upload(req))

    async def _file_fn(
        self,
        data: bytes = b"\xff\xd8\xff\xe0",
        ctype: str = "image/jpeg",
        filename: str = "photo.jpg",
        content: str = "",
        fmt: str = "",
    ) -> dict:
        file = MagicMock(spec=UploadFile)
        file.read = AsyncMock(return_value=data)
        file.content_type = ctype
        file.filename = filename
        file.size = len(data)
        form = {"content": content, "format": fmt, "file": file}
        req = MagicMock()
        req.form = AsyncMock(return_value=form)
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

    async def test_bad_format_token_raises(self):
        """A bad format token on non-empty content raises UnsupportedFormatError."""
        with pytest.raises(errors.UnsupportedFormatError):
            await self._test_fn("hello", "bogus")

    async def test_declared_mime_is_plaintext(self):
        """Form content always declares text/plain mime."""
        result = await self._test_fn("hello", "")
        assert result["declared_mime"] == "text/plain"

    @pytest.mark.parametrize("content", ["", "   "], ids=["empty", "whitespace"])
    async def test_empty_content_raises(self, content):
        """Empty or whitespace-only textarea raises ValueError."""
        with pytest.raises(errors.PayloadEmptyError):
            await self._test_fn(content, "")

    async def test_file_extracts_fields(self):
        """File bytes, content_type, and filename are extracted."""
        result = await self._file_fn()
        assert result["payload_bytes"] == b"\xff\xd8\xff\xe0"
        assert result["declared_mime"] == "image/jpeg"
        assert result["filename"] == "photo.jpg"

    async def test_file_preferred_over_textarea(self):
        """File takes precedence when both content and file present."""
        result = await self._file_fn(content="leftover text")
        assert result["payload_bytes"] == b"\xff\xd8\xff\xe0"

    async def test_empty_file_raises(self):
        """Empty file raises ValueError."""
        with pytest.raises(errors.PayloadEmptyError):
            await self._file_fn(data=b"")


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
