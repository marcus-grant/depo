# core/tests/views/test_login.py
from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch


# TODO: Rename to test_user and include login view tests here?
class LoginViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("login")

    def test_get_returns_form(self):
        """GET request to /login returns HTML login form"""
        resp = self.client.get(self.url)
        content = resp.content.decode("utf-8")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("<form", content)
        self.assertIn('<input type="password', content)
        self.assertIn('<button type="submit"', content)
