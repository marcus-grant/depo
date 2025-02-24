# core/tests/views/test_login.py
import jwt
from datetime import datetime, timedelta, timezone

from django.conf import settings
from django.test import TestCase, Client
from django.urls import reverse

from core.models.user import User
from core.views.user import JWT_EXP_DELTA_SECONDS

# JWT_EXP_DELTA_SECONDS = 3600


# TODO: Rename to test_user and include login view tests here?
class LoginViewTests(TestCase):
    """Tests involving core.views.user.login_view or /login URL"""

    def setUp(self):
        # Prepare client and member var for url needed for tests
        self.client = Client()
        self.url = reverse("login")
        # Create dummy user (hard-coded for now)
        self.user = User.objects.create(name="tester", email="test@example.com")
        self.user.set_password("password")
        self.user.save()

    def test_get_returns_form(self):
        """GET request to /login returns HTML login form"""
        resp = self.client.get(self.url)
        content = resp.content.decode("utf-8")
        self.assertEqual(resp.status_code, 200)
        self.assertIn('<form method="post" action="/login"', content)
        self.assertIn('<input type="password', content)
        self.assertIn('<button type="submit"', content)

    def test_post_valid_creds_returns_valid_jwt(self):
        """POST request w| valid credentials returns plaintext containing valid JWT"""
        # Arrange: valid login credentials
        data = {"email": "test@example.com", "password": "password"}

        # Act: POST request to /login
        resp = self.client.post(self.url, data)
        token = resp.content.decode("utf-8").strip()
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        now = int(datetime.now(timezone.utc).timestamp())

        # Assert
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "text/plain")
        self.assertEqual(resp["X-Auth-Token"], token)
        self.assertEqual(decoded["name"], "tester")
        self.assertEqual(decoded["email"], "test@example.com")
        self.assertLessEqual(decoded["exp"] - now, JWT_EXP_DELTA_SECONDS)

    def test_post_login_invalid_creds_returns_401(self):
        """POST with invalid creds should return 401 Unauthorized"""
        data = {"email": "tester", "password": "wrongpassword"}
        resp = self.client.post(self.url, data)
        content = resp.content.decode("utf-8")
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp["X-Error"], "true")
        self.assertEqual(resp["Content-Type"], "text/plain")
        self.assertIn("access", content.lower())
        self.assertIn("unauthor", content.lower())

    def test_non_post_get_request_returns_error(self):
        """If request method is neither POST or GET, return 405 Method Not Allowed"""
        resp_put = self.client.put(self.url)
        self.assertEqual(resp_put.status_code, 405)
        self.assertEqual(resp_put["Allow"], "GET, POST")
        self.assertIn("method not allowed", resp_put.content.decode("utf-8").lower())
