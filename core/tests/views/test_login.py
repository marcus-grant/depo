# core/tests/views/test_login.py
from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch


# TODO: Fix or consider if testing calling of login_view necessary
# TODO: Consider which core.user.tests should move here
# class LoginViewTests(TestCase):
#     """Tests for the core.views.login.view & mapped url @ /login"""
#
#     def setUp(self):
#         self.client = Client()
#         self.url = reverse("login")
#
#     @patch("core.urls.login_view")
#     def test_get_returns_form(self, mock):
#         """GET request to /login calls this function with mock"""
#         resp = self.client.get(self.url)  # Act:
#         mock.assert_called_once()  # Assert core.views.login.view
