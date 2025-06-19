from django.urls import reverse
from django.test import TestCase, Client

from core.util.shortcode import hash_b32, SHORTCODE_MIN_LEN


class WebIndexViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url_index = reverse("index")
        self.url_login = reverse("login")
        self.url_upload = reverse("web_upload")

    def test_get_request_renders_index(self):
        """Test root GET request renders index.html"""
        resp = self.client.get(self.url_index)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "index.html")
        self.assertNotContains(resp, "error")
        self.assertNotContains(resp, "shortcode is: <strong>")

    def test_root_post_request_creates_item(self):
        """Test root POST request creates an item"""
        url = "https://www.google.com"
        resp = self.client.post(self.url_index, {"content": url})
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "index.html")

        # Check response contents against Item contents
        shortcode = hash_b32(url)[:SHORTCODE_MIN_LEN]
        pattern_href = f'href="[^"]*{shortcode}/details"'
        self.assertContains(resp, f"{shortcode}</strong>")
        self.assertRegex(resp.content.decode(), pattern_href)

    def test_index_shows_login_for_anon(self):
        """When anonymous user, index page should show login link over upload widget"""
        response = self.client.get(self.url_index)
        expected_link = f"{self.url_login}?next={self.url_index}"
        self.assertContains(response, f'href="{expected_link}"')
