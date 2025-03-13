# core/tests/models/test_user.py
from datetime import datetime, timedelta, UTC

from django.apps import apps
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

User = get_user_model()

###
### Models Tests
###


class UserPrepopulationTests(TestCase):
    """Tests prepopulation takes place before server runs"""

    def setUp(self):
        # Ensure user table empty for tests
        User.objects.all().delete()

    def test_prepopulate_superuser_when_empty(self):
        """
        If no superuser exists, calling prepopulate_superuser should create one
        using the SUPERUSER_USERNAME, SUPERUSER_EMAIL, and SUPERUSER_PASSWORD settings.
        """
        settings_overrides = {
            "SUPERUSER_USERNAME": "admin",
            "SUPERUSER_EMAIL": "admin@example.com",
            "SUPERUSER_PASSWORD": "adminpass",
        }
        with override_settings(**settings_overrides):
            app_cfg = apps.get_app_config("core")
            # Trigger the superuser prepopulation.
            app_cfg.prepopulate_superuser()  # type:ignore
            # Assert that one user is now in the User table.
            self.assertEqual(User.objects.count(), 1)
            user = User.objects.get(username="admin")
            self.assertTrue(user.is_superuser)  # type: ignore
            self.assertTrue(user.is_staff)  # type: ignore
            self.assertTrue(user.check_password("adminpass"))

    def test_skips_existing_superuser(self):
        """
        If a superuser with the same username already exists,
        prepopulate_superuser should not create a duplicate or alter the existing user.
        """
        settings_overrides = {
            "SUPERUSER_USERNAME": "admin",
            "SUPERUSER_EMAIL": "admin@example.com",
            "SUPERUSER_PASSWORD": "adminpass",
        }
        with override_settings(**settings_overrides):
            # Arrange: Create an existing superuser with a different password.
            User.objects.create_superuser(  # type: ignore
                username="admin", email="admin@example.com", password="oldpass"
            )
            app_cfg = apps.get_app_config("core")
            # Act: Trigger the superuser prepopulation.
            app_cfg.prepopulate_superuser()  # type: ignore
            # Assert: The user count remains 1 and the original password is not overwritten.
            self.assertEqual(User.objects.count(), 1)
            user = User.objects.get(username="admin")
            self.assertTrue(user.check_password("oldpass"))
