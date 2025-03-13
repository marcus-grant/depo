# core/tests/management/test_commands.py
import contextlib
import environ
import io
import os
from pathlib import Path
import tempfile

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model

User = get_user_model()

# TODO: Add tests for hash_password command in own class
# TODO: Supress stdout from command from test output


class TestEnviron(TestCase):
    """Ensures environ works as needed."""

    def test_shell_precedence(self):
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
            f.write("__TESTVAR=FromFile\n")
            f.flush()
            tmp_env_path = Path(f.name)
            os.environ["__TESTVAR"] = "FromShell"
            env = environ.Env()
            env.read_env(tmp_env_path)
            self.assertEqual(env("__TESTVAR"), "FromShell")


class CreateSuperuserTests(TestCase):
    def setUp(self):
        # Define the environment variable keys used by tests.
        self.env_keys = [
            "DEPO_SUPERUSER_NAME",
            "DEPO_SUPERUSER_EMAIL",
            "DEPO_SUPERUSER_PASS",
            "DEPO_ENV_FILE",
        ]
        # Store original environment variables to restore later.
        self.original_env = {key: os.environ.get(key) for key in self.env_keys}
        self._clear_env_vars()

    def tearDown(self):
        # Clear out any leftover environment variables.
        self._clear_env_vars()
        # Optionally restore original environment variables.
        for key, value in self.original_env.items():
            if value is not None:
                os.environ[key] = value

    def _clear_env_vars(self):
        for key in self.env_keys:
            if key in os.environ:
                del os.environ[key]

    def _set_env_vars(self, vars_dict):
        # Set multiple environment variables from a dictionary.
        for key, value in vars_dict.items():
            os.environ[key] = value

    @override_settings(
        SUPERUSER_NAME="admin", SUPERUSER_EMAIL="admin@example.com", SUPERUSER_PASS=""
    )
    def test_no_new_user_created_when_incomplete_env_variables(self):
        """
        When one or two of the required environment variables
        (SUPERUSER_NAME, SUPERUSER_EMAIL, SUPERUSER_PASS)
        are missing or empty, no new user should be created.
        """
        initial_count = User.objects.count()
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            call_command("create_superuser")
        self.assertEqual(
            User.objects.count(),
            initial_count,
            "A new user should not be created when env vars are incomplete.",
        )

    def test_existing_user_not_overwritten(self):
        """
        If a user already exists in the database with the same username,
        the create_superuser command should not override the current user.
        """
        # Create an initial user.
        User.objects.create_superuser(  # type: ignore
            username="existing", email="existing@example.com", password="secret"
        )
        # Set env variables (simulate a superuser creation with the same username).
        self._set_env_vars(
            {
                "DEPO_SUPERUSER_NAME": "existing",
                "DEPO_SUPERUSER_EMAIL": "new@example.com",
                "DEPO_SUPERUSER_PASS": "newsecret",
            }
        )
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            call_command("create_superuser")
        # Ensure the user's details have not been changed.
        user = User.objects.get(username="existing")
        self.assertEqual(
            user.email,  # type: ignore
            "existing@example.com",
            "The existing user should not be overridden by the command.",
        )
