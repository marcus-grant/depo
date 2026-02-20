# tests/web/test_info_page.py
"""
Tests for HTML info views.
Author: Marcus Grant
Created: 2026-02-16
License: Apache-2.0
"""

from bs4 import BeautifulSoup


class TestInfoPageText:
    """GET /{code}/info for TextItem"""

    def test_response(self, t_seeded):
        """Text info page returns correct template, shortcode, content, and metadata."""
        resp = t_seeded.browser.get(f"/{t_seeded.txt.code}/info")
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
        assert t_seeded.txt.code in code_el.text
        assert "Hello, World!" in resp.text
        assert "Format" in dts
        assert dts["Format"] == t_seeded.txt.format
        assert dts["Size"] == f"{t_seeded.txt.size_b} bytes"
        assert "Uploaded" in dts


class TestInfoPagePic:
    """GET /{code}/info for PicItem"""

    def test_response(self, t_seeded):
        """Text info page returns correct template, shortcode, content, and metadata."""
        resp = t_seeded.browser.get(f"/{t_seeded.pic.code}/info")
        assert resp.status_code == 200
        assert "<!-- BEGIN: info/pic.html" in resp.text
        assert "<!-- END: info/pic.html -->" in resp.text
        assert "<!-- BEGIN: base.html" in resp.text, "Page not wrapped in base template"
        soup = BeautifulSoup(resp.content, "html.parser")
        code_el = soup.find(class_="shortcode")
        dts = {dt.text: dt.find_next_sibling("dd").text for dt in soup.find_all("dt")}  # type: ignore
        img_el = soup.find("img")
        assert code_el is not None
        assert t_seeded.pic.code in code_el.text
        assert img_el is not None
        assert f"/api/{t_seeded.pic.code}/raw" in img_el["src"]
        assert "Format" in dts
        assert dts["Format"] == "jpg"
        assert dts["Size"] == f"{t_seeded.pic.size_b} bytes"
        assert "Uploaded" in dts
        assert dts["Dimensions"] == f"{t_seeded.pic.width}x{t_seeded.pic.height}"


class TestInfoPageLink:
    """GET /{code}/info for LinkItem"""

    def test_response(self, t_seeded):
        """Link info page returns correct template, shortcode, and clickable URL."""
        resp = t_seeded.browser.get(f"/{t_seeded.link.code}/info")
        assert resp.status_code == 200
        assert "<!-- BEGIN: info/link.html" in resp.text
        assert "<!-- END: info/link.html -->" in resp.text
        assert "<!-- BEGIN: base.html" in resp.text
        soup = BeautifulSoup(resp.content, "html.parser")
        code_el = soup.find(class_="shortcode")
        assert code_el is not None
        assert t_seeded.link.code in code_el.text
        link_el = soup.find("a", href=t_seeded.link.url)
        assert link_el is not None
        assert t_seeded.link.url in link_el.text
        dts = {dt.text: dt.find_next_sibling("dd").text for dt in soup.find_all("dt")}  # type: ignore
        assert "URL" in dts
        assert "Uploaded" in dts


class TestInfoPageNotFound:
    """GET /{code}/info for unknown code"""

    def test_unknown_code_returns_404(self, t_browser):
        """Unknown code returns 404."""
        assert t_browser.get("/ZZZZZZZZ/info").status_code == 404
