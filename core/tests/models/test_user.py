# core/user/tests.py
from datetime import datetime, timedelta, UTC

# from django import test # DELETEME: Why is this here?
from django.conf import settings
from django.db import IntegrityError
from django.http import HttpResponse
from django.test import TestCase, RequestFactory, override_settings
import jwt

from core.models.user import User, jwt_required


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


def dummy_view(_):  # Place requests here as views usually do, just wont be used
    return HttpResponse("foobar", status=200, content_type="text/plain")


class JWTDecoratorTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        # Create a valid token payload with 1-hour expiration time.
        payload = {
            "email": "test@example.com",
            "name": "tester",
            "exp": datetime.now(UTC) + timedelta(hours=1),
        }
        self.valid_payload = payload
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        # Ensure token is a string
        if isinstance(token, bytes):
            token = token.decode("utf-8")
        self.valid_token = token

    def test_no_token(self):
        """Request w|o Authorization header should return 401 Unauthorized."""
        request = self.factory.get("/testing")
        # Apply decorator
        decorated_view = jwt_required(dummy_view)
        resp = decorated_view(request)
        self.assertEqual(resp.status_code, 401)
        self.assertIn(b"bearer", resp.content.lower())
        self.assertIn(b"token", resp.content.lower())
        self.assertIn(b"unauthor", resp.content.lower())

    def test_valid_token_uses_dummy_view_with_valid_payload(self):
        """Request w| valid Bearer token should allow access and
        user_payload should be present in request.user_payload."""
        auth_header = f"Bearer {self.valid_token}"
        request = self.factory.get("/testing", HTTP_AUTHORIZATION=auth_header)
        resp = jwt_required(dummy_view)(request)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, b"foobar")
        # Now assert that the correct request.user_payload object is present
        user_payload = getattr(request, "user_payload", None)
        self.assertTrue(user_payload)
        email = user_payload.get("email", None)  # type: ignore
        self.assertEqual(email, self.valid_payload["email"])
        name = user_payload.get("name", None)  # type: ignore
        self.assertEqual(name, self.valid_payload["name"])
        exp = user_payload.get("exp", None)  # type: ignore
        self.assertLessEqual(exp - self.valid_payload["exp"].timestamp(), 1)

    def test_invalid_token(self):
        """Invalid tokens encountering jwt_required views are unauthorized."""
        invalid_token = jwt.encode(
            self.valid_payload, "wrong_secret", algorithm="HS256"
        )
        if isinstance(invalid_token, bytes):
            invalid_token = invalid_token.decode("utf-8")
        request = self.factory.get(
            "/testing", HTTP_AUTHORIZATION=f"Bearer {invalid_token}"
        )
        decorated_view = jwt_required(dummy_view)
        resp = decorated_view(request)
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp["X-Error"], "true")
        self.assertIn(b"invalid", resp.content.lower())

    def test_expired_token(self):
        """Expired tokens encountering jwt_required views are unauthorized."""
        expired_payload = self.valid_payload.copy()
        expired_payload["exp"] = datetime.now(UTC) - timedelta(seconds=1)
        expired_token = jwt.encode(
            expired_payload, settings.SECRET_KEY, algorithm="HS256"
        )
        request = self.factory.get(
            "/dummy", HTTP_AUTHORIZATION=f"Bearer {expired_token}"
        )
        decorated_view = jwt_required(dummy_view)
        resp = decorated_view(request)
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp["X-Error"], "true")
        self.assertIn(b"expire", resp.content.lower())

    def test_with_malformed_header(self):
        request = self.factory.get("/testing", HTTP_AUTHORIZATION="InVaLiDTooKeNForMat")
        decorated_view = jwt_required(dummy_view)
        resp = decorated_view(request)
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp["X-Error"], "true")
        self.assertIn(b"unauthorized", resp.content.lower())
