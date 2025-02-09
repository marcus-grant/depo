# core/user/tests.py
from django.test import TestCase
from django.db import IntegrityError
from core.user.models import User


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
