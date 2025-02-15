# core/tests/templates/test_index.py
from django.test import TestCase
from django.urls import reverse


# TODO: Test the redirection of the shortcode using URLs
class IndexTemplateElemsTest(TestCase):
    def test_index_contains_form(self):
        resp = self.client.get(reverse("web_index"))
        self.assertContains(resp, "<form")
        self.assertContains(resp, 'name="content"')
        self.assertContains(resp, 'type="submit"')
        self.assertNotContains(resp, "/details")

    def test_index_contains_form_post(self):
        ctx = {"content": "https://www.google.com"}
        resp = self.client.post(reverse("web_index"), ctx)
        self.assertContains(resp, "<form")
        self.assertContains(resp, 'name="content"')
        self.assertContains(resp, 'type="submit"')
        # Check for the confirmation link unique to POST
        self.assertContains(resp, "/details")
