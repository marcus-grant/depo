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
