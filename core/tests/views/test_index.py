from django.urls import reverse
from django.test import TestCase

from core.util.shortcode import hash_b32, SHORTCODE_MIN_LEN


class WebIndexViewTest(TestCase):
    def test_get_request_renders_index(self):
        """Test root GET request renders index.html"""
        resp = self.client.get(reverse("web_index"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "index.html")
        self.assertNotContains(resp, "error")
        self.assertNotContains(resp, "shortcode is: <strong>")

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
