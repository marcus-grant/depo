# tests/web/test_info_templates.py
"""
Tests for info page templates (link, text, pic).
Author: Marcus Grant
Created: 2026-02-25
License: Apache-2.0
"""

from bs4 import BeautifulSoup as BSoup

from depo.model.item import Item
from tests.factories import render_template
from tests.factories.models import make_link_item, make_pic_item, make_text_item
from tests.factories.payloads import gen_image


def _info_page_soup(template: str, item: Item, **ctx) -> BSoup:
    """Helper to render info page template and return soup."""
    ctx.setdefault("request", type("Req", (), {"base_url": "http://test/"})())
    return render_template(template, {"item": item, **ctx})


def _link_info_soup_select(selector: str):
    """Create BeautifulSoup of rendered LinkItem info template and select element"""
    return _info_page_soup("info/link.html", make_link_item()).select_one(selector)


_TXT_DATA = "Hello, world!"


def _text_info_soup_select(selector: str):
    """Create BeautifulSoup of rendered TextItem info template and select element"""
    args = ("info/text.html", make_text_item())
    return _info_page_soup(*args, content=_TXT_DATA).select_one(selector)


_PIC_DATA = gen_image("png", 32, 24)  # Red image data


def _pic_info_soup_select(selector: str):
    """Create BeautifulSoup of rendered PicItem info template and select element"""
    args = ("info/pic.html", make_pic_item())
    return _info_page_soup(*args, content=_PIC_DATA).select_one(selector)


class TestInfoStructure:
    """Shared window structure across all info templates."""

    def select(self, selector):
        """Alias for the same selection of info soup on every test"""
        return _link_info_soup_select(selector)

    def test_window_container(self):
        """Info page content renders inside a .window container."""
        assert self.select("article.window") is not None

    def test_code_first(self):
        """Renders shortcode as first child of .window."""
        assert self.select("article.window > .shortcode") is not None

    def test_action_after_code(self):
        """Has .action-row after shortcode."""
        assert self.select("article.window > .shortcode + .action-row") is not None

    def test_payload_after_action(self):
        """Has #payload container after action row."""
        assert self.select("article.window > .action-row + #payload") is not None

    def test_payload_meta_divider(self):
        """Has divider between payload and metadata."""
        assert self.select("#payload + hr.divider") is not None

    def test_metadata_after_divider(self):
        """Has #metadata dl after divider."""
        assert self.select("hr.divider + dl#metadata") is not None

    def test_action_copy_content_disabled(self):
        """Copy content button exists but is disabled."""
        assert self.select(".action-row button[disabled]") is not None

    def test_action_copy_url(self):
        """Copy URL button carries raw URL for clipboard."""
        btn = self.select(".action-row button.secondary[data-copy]")
        assert btn is not None
        assert "/raw" in btn.get("data-copy", "")  # type: ignore

    def test_action_copy_shortcode(self):
        """Copy shortcode button carries code value for clipboard."""
        btn = self.select(".action-row button.outline[data-copy]")
        assert btn is not None
        assert btn.get("data-copy") != ""

    def test_action_facts_jump(self):
        """Facts anchor links to metadata section."""
        assert self.select(".action-row a[href='#metadata']") is not None

    def test_clipboard_script(self):
        """Clipboard handler script is present."""
        assert self.select("script") is not None


class TestInfoLink:
    """Link-specific info template content."""

    def select(self, selector):
        """Alias for the same selection of info soup on every test"""
        return _link_info_soup_select(selector)

    def test_url_in_payload(self):
        """Renders URL in payload section."""
        assert self.select("#payload a") is not None
        assert self.select("#payload a").text == "https://example.com"  # type: ignore

    def test_upload_at_in_metadata(self):
        """Renders upload timestamp in metadata."""
        dl = self.select("dl#metadata")
        assert dl is not None
        assert any(w in dl.text.lower() for w in ("upload", "creat", "date", "time"))

    def test_payload_modifier(self):
        """Payload has type-specific class."""
        assert self.select("#payload.payload--link") is not None


class TestInfoText:
    """Text-specific info template content."""

    def select(self, selector):
        """Alias for the same selection of text info soup on every test"""
        return _text_info_soup_select(selector)

    def test_content_in_pre_code_payload(self):
        """Renders text content inside <pre><code> in payload."""
        el = self.select("#payload pre code")
        assert el is not None
        assert _TXT_DATA in el.text

    def test_metadata_fields_present(self):
        """Renders format, size, upload timestamp in metadata."""
        dl = self.select("dl#metadata")
        assert dl is not None
        text = dl.text.lower()
        assert any(w in text for w in ("format", "type"))
        assert any(w in text for w in ("size", "bytes", "length"))
        assert any(w in text for w in ("upload", "created", "date", "time"))

    def test_payload_modifier(self):
        """Payload has type-specific class."""
        assert self.select("#payload.payload--text") is not None


class TestInfoPic:
    """Pic-specific info template content."""

    def select(self, selector):
        """Alias for the same selection of pic info soup on every test"""
        return _pic_info_soup_select(selector)

    def test_img_tag_in_payload(self):
        """Renders <img> tag in payload with correct src."""
        img = self.select("#payload img")
        assert img is not None
        assert img.get("src", "") != ""
        assert "/raw" in img.get("src", "")  # type: ignore

    def test_metadata_fields_present(self):
        """Renders format, size, dimensions, upload timestamp in metadata."""
        dl = self.select("dl#metadata")
        assert dl is not None
        text = dl.text.lower()
        assert any(w in text for w in ("format", "type"))
        assert any(w in text for w in ("size", "bytes", "length"))
        assert any(w in text for w in ("dim", "res", "width", "height"))
        assert any(w in text for w in ("upload", "created", "date", "time"))

    def test_payload_modifier(self):
        """Payload has type-specific class."""
        assert self.select("#payload.payload--pic") is not None
