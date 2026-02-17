# tests/web/test_upload_page.py
"""
Tests for the upload form page.
Author: Marcus Grant
Created: 2026-02-13
License: Apache-2.0
"""

from bs4 import BeautifulSoup

from depo.model.formats import ContentFormat, ItemKind, kind_for_format


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
        """Every ContentFormat has an option, every ItemKind has an optgroup."""
        soup = BeautifulSoup(t_client.get("/upload").text, "html.parser")
        select = soup.find("select", attrs={"name": "format"})

        # Auto-detect default exists with empty value
        assert select is not None
        auto = select.find("option", attrs={"value": ""})
        assert auto is not None

        # Map optgroup labels to ItemKind
        label_to_kind = {
            "text": ItemKind.TEXT,
            "image": ItemKind.PICTURE,
            "link": ItemKind.LINK,
        }
        groups = select.find_all("optgroup")
        group_labels = {g["label"].lower() for g in groups}  # type: ignore

        # Every ItemKind has an optgroup (except LINK — pending URL classification PR)
        ## TODO: Remove when URL enters pipeline as content
        _DEFERRED_KINDS = {ItemKind.LINK}
        for kind in ItemKind:
            if kind in _DEFERRED_KINDS:
                continue
            assert kind in label_to_kind.values(), f"No label mapping for {kind}"

        for label, kind in label_to_kind.items():
            if kind in _DEFERRED_KINDS:
                continue
            assert label in group_labels, f"Missing optgroup for {kind}"

        # Every option maps to the correct kind via kind_for_format
        seen_formats = set()
        for group in groups:
            expected_kind = label_to_kind[group["label"].lower()]  # type: ignore
            for option in group.find_all("option"):
                fmt = ContentFormat(option["value"])
                assert fmt not in seen_formats, f"Duplicate option: {fmt}"
                seen_formats.add(fmt)
                assert kind_for_format(fmt) == expected_kind, f"{fmt} in wrong group"

        # Every ContentFormat is represented
        assert seen_formats == set(ContentFormat), (
            f"Missing: {set(ContentFormat) - seen_formats}"
        )


class TestRootRedirect:
    """GET / redirects to /upload.

    # Returns redirect status
    # Redirects to /upload
    """

    def test_redirects_to_upload_302(self, t_client):
        """GET / redirects with 302 to /upload"""
        resp = t_client.get(url="/", follow_redirects=False)
        assert resp.status_code == 302
        assert resp.headers.get("location") == "/upload"
