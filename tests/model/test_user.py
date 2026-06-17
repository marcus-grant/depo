# tests/model/test_user.py
"""
Tests for the User domain model.
Author: Marcus Grant
Created: 2026-06-11
License: Apache-2.0
"""

from dataclasses import FrozenInstanceError, is_dataclass

import pytest
from tests.factories.models import make_user
from tests.helpers import assert_field

from depo.model.user import User

_USER_PARAMS = [
    ("id", int, True, None),
    ("email", str, True, None),
    ("name", str, True, None),
    ("pw_hash", str, True, None),
    ("created_at", int, True, None),
]


class TestUser:
    """Tests for the User dataclass."""

    def test_instance_dataclass(self):
        """User is a dataclass."""
        assert is_dataclass(User)

    @pytest.mark.parametrize("name,typ,required,default", _USER_PARAMS)
    def test_fields(self, name, typ, required, default):
        """Each field has the correct name, type, and optionality."""
        assert_field(User, name, typ, required, default)

    def test_frozen(self):
        """User instances are immutable, ie can't change a member from instances"""
        with pytest.raises(FrozenInstanceError):
            (make_user()).id = 999999  # type: ignore

    def test_instantiate(self):
        """User can be constructed with all required fields."""
        assert make_user(id=42).id == 42
        assert make_user(email="e@mail.se").email == "e@mail.se"
        assert make_user(name="Bob").name == "Bob"
        assert make_user(pw_hash="pass_hash").pw_hash == "pass_hash"
        assert make_user(created_at=0).created_at == 0
