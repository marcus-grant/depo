# tests/web/test_info_templates.py
"""
Tests for info page templates (link, text, pic).
Author: Marcus Grant
Created: 2026-02-25
License: Apache-2.0
"""

from bs4 import BeautifulSoup as BSoup

from tests.factories import render_template
from tests.factories.models import make_link_item


def _info_link_soup() -> BSoup:
    """Helper to render link info template and return soup."""
    return render_template("info/link.html", {"item": make_link_item()})


class TestInfoStructure:
    """Shared window structure across all info templates."""

    def info_select(self, selector: str):
        return _info_link_soup().select_one(selector)

    def test_window_container(self):
        """Info page content renders inside a .window container."""
        assert self.info_select("article.window") is not None

    def test_code_first(self):
        """Renders shortcode as first child of .window."""
        assert self.info_select("article.window > .shortcode") is not None

    def test_action_after_code(self):
        """Has .action-row after shortcode."""
        assert self.info_select("article.window > .shortcode + .action-row") is not None

    def test_payload_after_action(self):
        """Has #payload container after action row."""
        assert self.info_select("article.window > .action-row + #payload") is not None

    def test_payload_meta_divider(self):
        """Has divider between payload and metadata."""
        assert self.info_select("#payload + hr.divider") is not None

    def test_metadata_after_divider(self):
        """Has #metadata dl after divider."""
        assert self.info_select("hr.divider + dl#metadata") is not None

    def test_action_copy_content_disabled(self):
        """Copy content button exists but is disabled."""
        btn = self.info_select(".action-row button[disabled]")
        assert btn is not None

    def test_action_copy_url(self):
        """Copy URL button carries raw URL for clipboard."""
        btn = self.info_select(".action-row button.secondary[data-copy]")
        assert btn is not None
        assert "/raw" in btn.get("data-copy", "")  # type: ignore

    def test_action_copy_shortcode(self):
        """Copy shortcode button carries code value for clipboard."""
        btn = self.info_select(".action-row button.outline[data-copy]")
        assert btn is not None
        assert btn.get("data-copy") != ""

    def test_action_facts_jump(self):
        """Facts anchor links to metadata section."""
        assert self.info_select(".action-row a[href='#metadata']") is not None


class TestInfoLink:
    """Link-specific info template content."""

    # should render URL in payload
    # should render upload_at in metadata
    ...


class TestInfoText:
    """Text-specific info template content."""

    # should render content in pre>code inside payload
    # should render format, size_b, upload_at in metadata
    ...


class TestInfoPic:
    """Pic-specific info template content."""

    # should render img tag in payload with correct src
    # should render format, size_b, dimensions, upload_at in metadata
    ...
