# tests/web/test_info_page.py
"""
Tests for HTML info views.
Author: Marcus Grant
Created: 2026-02-16
License: Apache-2.0
"""

from bs4 import BeautifulSoup

from tests.factories.payloads import gen_image
from tests.factories import make_client


class TestInfoPageText:
    """GET /{code}/info for TextItem"""

    def test_response(self, tmp_path):
        """Text info page returns correct template, shortcode, content, and metadata."""
        client, file = make_client(tmp_path), {"file": ("hello.txt", b"Hello, World!")}
        resp = client.post("/api/upload", files=file)
        assert resp.status_code == 201
        code = resp.text
        resp = client.get(f"/{code}/info")
        msg = "Response is not HTML"
        assert resp.headers.get("content-type", "").startswith("text/html"), msg
        assert resp.status_code == 200
        assert "<!-- BEGIN: info/text.html" in resp.text
        assert "<!-- END: info/text.html -->" in resp.text
        assert "<!-- BEGIN: base.html" in resp.text, "Page not wrapped in base template"
        soup = BeautifulSoup(resp.content, "html.parser")
        code_el = soup.find(class_="shortcode")
        dts = {dt.text: dt.find_next_sibling("dd").text for dt in soup.find_all("dt")}  # type: ignore
        assert code_el is not None
        assert code in code_el.text
        assert "Hello, World!" in resp.text
        assert "Format" in dts
        assert dts["Format"] == "txt"
        assert dts["Size"] == "13 bytes"
        assert "Uploaded" in dts


class TestInfoPagePic:
    """GET /{code}/info for PicItem"""

    def test_response(self, tmp_path):
        """Text info page returns correct template, shortcode, content, and metadata."""
        img = gen_image("jpeg", width=64, height=64)
        client, file = make_client(tmp_path), {"file": ("test.jpg", img)}
        resp = client.post("/api/upload", files=file)
        assert resp.status_code == 201, "Failed to assemble test item as upload"
        code = resp.text
        resp = client.get(f"/{code}/info")
        assert resp.status_code == 200
        assert "<!-- BEGIN: info/pic.html" in resp.text
        assert "<!-- END: info/pic.html -->" in resp.text
        assert "<!-- BEGIN: base.html" in resp.text, "Page not wrapped in base template"
        soup = BeautifulSoup(resp.content, "html.parser")
        code_el = soup.find(class_="shortcode")
        dts = {dt.text: dt.find_next_sibling("dd").text for dt in soup.find_all("dt")}  # type: ignore
        img_el = soup.find("img")
        assert code_el is not None
        assert code in code_el.text
        assert img_el is not None
        assert f"/api/{code}/raw" in img_el["src"]
        assert "Format" in dts
        assert dts["Format"] == "jpg"
        assert dts["Size"] == f"{len(img)} bytes"
        assert "Uploaded" in dts
        assert dts["Dimensions"] == "64x64"


class TestInfoPageLink:
    """GET /{code}/info for LinkItem"""

    def test_response(self, tmp_path):
        """Link info page returns correct template, shortcode, and clickable URL."""
        url = "https://example.com"
        client = make_client(tmp_path)
        resp = client.post(f"/api/upload?url={url}")
        assert resp.status_code == 201, "Failed to assemble test item as upload"
        code = resp.text
        resp = client.get(f"/{code}/info")
        assert resp.status_code == 200
        assert "<!-- BEGIN: info/link.html" in resp.text
        assert "<!-- END: info/link.html -->" in resp.text
        assert "<!-- BEGIN: base.html" in resp.text
        soup = BeautifulSoup(resp.content, "html.parser")
        code_el = soup.find(class_="shortcode")
        assert code_el is not None
        assert code in code_el.text
        link_el = soup.find("a", href=url)
        assert link_el is not None
        assert url in link_el.text
        dts = {dt.text: dt.find_next_sibling("dd").text for dt in soup.find_all("dt")}  # type: ignore
        assert "URL" in dts
        assert "Uploaded" in dts


class TestInfoPageNotFound:
    """GET /{code}/info for unknown code"""

    def test_unknown_code_returns_404(self, tmp_path):
        """Unknown code returns 404."""
        client = make_client(tmp_path)
        resp = client.get("/ZZZZZZZZ/info")
        assert resp.status_code == 404
