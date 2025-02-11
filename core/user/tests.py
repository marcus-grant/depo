# core/user/tests.py
from datetime import datetime, UTC
from django import test
from django.conf import settings
from django.db import IntegrityError
from django.test import TestCase, Client
from django.urls import reverse
import jwt

from core.user.models import User


###
### Models Tests
###


class UserModelTests(TestCase):
    def test_create_user_valid_schema(self):
        """Users created with valid data should have valid schemas"""
        # Arrange: Create new user instance.
        user = User.objects.create(name="tester", email="tester@example.com")
        user.set_password("password")
        user.save()
        # Act: Retrieve user from DB
        saved_user = User.objects.get(name="tester")
        # Assert: Retrieved user has same email, hashed password & check_password works
        self.assertEqual(saved_user.email, "tester@example.com")
        self.assertNotEqual(saved_user.pass_hash, "password")
        self.assertNotEqual(saved_user.pass_hash, None)
        self.assertNotEqual(saved_user.pass_hash, "")
        self.assertTrue(saved_user.check_password("password"))

    def test_duplicate_username_raises(self):
        """Any duplicate User.name must raise errors, can't be allowed"""
        User.objects.create(name="unique_dude", email="unique@dude.lol")
        with self.assertRaises(IntegrityError):
            User.objects.create(name="unique_dude", email="unique@dude.lol")

    def test_duplicate_email_raises(self):
        """Any duplicate User.email must raise errors"""
        User.objects.create(name="unique@dude", email="unique@dude.lol")
        with self.assertRaises(IntegrityError):
            User.objects.create(name="unique_dude", email="unique@dude.lol")


###
### Views Tests
###


class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.login_url = reverse("login")
        self.user = User.objects.create(name="tester", email="test@example.com")
        self.user.set_password("password")
        self.user.save()

    def test_valid_login_returns_jwt(self):
        """POSTs to login url w| valid credentials should return a JWT token"""
        # Arrange: Credentialed login request
        creds = {"email": "test@example.com", "password": "password"}
        # Act: POST JWT request with login URL and record response, extract token
        resp = self.client.post(self.login_url, creds)
        token = resp.content.decode("utf-8")
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        # Assert: 200 status, ctype, JWT token contents
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "text/plain")
        self.assertTrue(token, "The returned token in response body shouldn't be empty")
        self.assertEqual(resp["X-Auth-Token"], token)
        self.assertEqual(decoded["name"], "tester")
        self.assertEqual(decoded["email"], "test@example.com")
        self.assertTrue(int(decoded["exp"]))
        self.assertGreater(int(decoded["exp"]), datetime.now(UTC).timestamp())

    # def test_invalid_pass_returns_unauthorized(self):
    #     """POST to login with bad credentials should return 401 with unauthorized message"""
    #     # Arrange: Create payload with bad credentials
    #     payload = {"email": "test@example.com", "password": "wrong-pass"}
    #     # Act: POST bad payload & record response
    #     resp = self.client.post(
    #         self.login_url, json.dumps(payload), content_type="application/json"
    #     )
    #     # Assert: 401 code and error message response
    #     self.assertEqual(resp.status_code, 401)
    #     self.assertEqual(resp["X-Error"], "true")
    #     self.assertIn(b"unauthorized", resp.content.lower())
    #     self.assertIn(b"password", resp.content.lower())
