# core/tests/templates/test_index.py
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User


# TODO: Test the redirection of the shortcode using URLs
# TODO: Test that login form appears when not logged in and upload form does not
class IndexTemplateElemsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")

    def test_index_contains_form(self):
        self.client.login(username="testuser", password="testpass")
        resp = self.client.get(reverse("index"))
        self.assertContains(resp, "<form")
        self.assertContains(resp, 'name="content"')
        self.assertContains(resp, 'type="submit"')
        self.assertNotContains(resp, "/details")

    def test_index_contains_form_post(self):
        self.client.login(username="testuser", password="testpass")
        ctx = {"content": "https://www.google.com"}
        resp = self.client.post(reverse("index"), ctx)
        self.assertContains(resp, "<form")
        self.assertContains(resp, 'name="content"')
        self.assertContains(resp, 'type="submit"')
        # Check for the confirmation link unique to POST
        self.assertContains(resp, "/details")
