# core/tests/test_views.py

from django.test import TestCase
from django.urls import reverse

from core.shortcode import hash_b32, SHORTCODE_MIN_LEN
from core.models import Item


# TODO: Test the redirection of the shortcode using URLs
class WebIndexViewTest(TestCase):
    def test_get_request_renders_index(self):
        """Test root GET request renders index.html"""
        resp = self.client.get(reverse("web_index"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "index.html")
        self.assertNotContains(resp, "error")
        self.assertNotContains(resp, "item")

    def test_root_post_request_creates_item(self):
        """Test root POST request creates an item"""
        url = "https://www.google.com"
        resp = self.client.post(reverse("web_index"), {"content": url})
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "index.html")

        # Check response contents against Item contents
        shortcode = hash_b32(url)[:SHORTCODE_MIN_LEN]
        pattern_href = f'href="[^"]*{shortcode}/details"'
        self.assertContains(resp, f"{shortcode}</strong>")
        self.assertRegex(resp.content.decode(), pattern_href)

    # NOTE: I can't think of a case where this will happen
    # def test_post_no_content(self):
    #     """Test POST request missing content"""
    #     # breakpoint()
    #     resp = self.client.post(reverse("web_index"))
    #     breakpoint()
    #     self.assertEqual(resp.status_code, 400)
    #     self.assertTemplateUsed(resp, "index.html")
    #     self.assertContains(resp, "Content is required")


class ShortcodeDetailsViewTest(TestCase):
    def setUp(self):
        self.item = Item.ensure("https://www.google.com")

    def test_valid_shortcode_renders_details(self):
        """Test valid shortcode form request renders details page content"""
        shortcode = self.item.shortcode
        resp = self.client.get(reverse("shortcode_details", args=[shortcode]))
        breakpoint()
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "shortcode-details.html")
        self.assertContains(resp, f": {shortcode}")
        self.assertContains(resp, f"URL: {self.item.url}")
