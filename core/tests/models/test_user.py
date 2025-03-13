# core/tests/models/test_user.py
from datetime import datetime, timedelta, UTC

from django.apps import apps
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

User = get_user_model()

# TODO: Tests to ensure builtin user/auth stuff works as expected
