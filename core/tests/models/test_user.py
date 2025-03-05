# core/tests/models/test_user.py
from datetime import datetime, timedelta, UTC
import json
import pathlib
import tempfile

from django.apps import apps
from django.conf import settings
from django.db import IntegrityError
from django.http import HttpResponse
from django.test import TestCase, RequestFactory, override_settings

import jwt

from core.models.user import User, jwt_required
from core.apps import CoreConfig

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


class UserPrepopulationTests(TestCase):
    """Tests prepopulation takes place before server runs"""

    def setUp(self):
        # Ensure the User table is empty.
        User.objects.all().delete()
        # Create temporary config file with test users.
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_path = pathlib.Path(self.temp_dir.name) / "user.json"
        # Override settings for user config file location.
        self.override = override_settings(USERS_FILE=self.config_path)
        self.override.enable()
        # Setup test user dicts
        self.test_users = [
            {
                "name": "alice",
                "email": "alice@example.com",
                "password": "alicepassword",
            },
            {
                "name": "bob",
                "email": "bob@example.com",
                "password": "B0bpassword",
            },
        ]

    def setup_temp_config(self, config):
        """Used to control which user config is fed to the AppConfig and when."""
        with open(self.config_path, "w") as f:
            json.dump(config, f)

    def tearDown(self):
        self.override.disable()
        self.temp_dir.cleanup()

    def test_setup_empties_user_table(self):
        """Tests this class' setUp method empties User table."""
        self.assertEqual(User.objects.count(), 0)

    def test_prepopulate_users_if_empty(self):
        """If User table empty & user file exists, AppConfig.ready should populate."""
        # Act: Explicitly trigger prepopulation method using self.test_users
        self.setup_temp_config(self.test_users)
        app_cfg = apps.get_app_config("core")
        assert isinstance(app_cfg, CoreConfig)
        app_cfg.prepopulate_users()
        # Assert: The two test_users are now in the User table
        self.assertEqual(User.objects.count(), 2)
        alice = User.objects.get(email="alice@example.com")
        self.assertEqual(alice.name, "alice")
        self.assertTrue(alice.check_password("alicepassword"))
        self.assertNotEqual(alice.pass_hash, "alicepassword")

    # TODO: Refactor this before committing way shorter way to express this possible
    def test_skips_existing_users(self):
        # Arrange: Create existing "alice-old" user w| same email 'alice@example.com'
        user = User.objects.create(name="alice-old", email="alice@example.com")
        user.set_password("oldPassword")  # Different password, shouldn't change
        user.save()
        self.setup_temp_config(self.test_users)
        # Act: Run prepopulation using temporary user config
        app_cfg = apps.get_app_config("core")
        assert isinstance(app_cfg, CoreConfig)
        app_cfg.prepopulate_users()
        # Assert "alice-old" remains the same & "bob" is added from users file
        self.assertEqual(User.objects.count(), 2)
        alice = User.objects.get(email="alice@example.com")
        self.assertEqual(alice.name, "alice-old")
        self.assertNotEqual(alice.pass_hash, "oldPassword")
        self.assertTrue(alice.check_password("oldPassword"))
