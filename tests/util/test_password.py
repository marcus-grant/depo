# tests/util/test_password.py
"""
Tests for depo.util.password.
Author: Marcus Grant
Created: 2026-06-17
License: Apache-2.0
"""

from depo.util.password import hash_password, verify_password


class TestHashPassword:
    """Tests for hash_password."""

    def test_returns_phc_style_string(self):
        """Returns a PHC-style string with algorithm, params, salt_hex, digest_hex."""
        result = hash_password("hunter2", n=2, r=8, p=1)
        parts = result.split("$")
        assert parts[0] == "scrypt"
        assert "n=" in parts[1]
        assert "r=" in parts[1]
        assert "p=" in parts[1]
        assert len(parts[2]) > 0
        assert len(parts[3]) > 0

    def test_random_salt_produces_unique_hashes(self):
        """Produces unique hashes for the same password due to random salt."""
        # should return different strings on two calls with identical inputs
        pword, kw = "fO0B@r", {"n": 2**14, "r": 8, "p": 1}
        a, b = hash_password(pword, **kw), hash_password(pword, **kw)
        assert a != b


class TestVerifyPassword:
    """Tests for verify_password."""

    def test_correct_password_verifies(self):
        """Returns True when the password matches the stored hash."""
        stored = hash_password("hunter2", n=2, r=8, p=1)
        assert verify_password("hunter2", stored) is True

    def test_wrong_password_fails(self):
        """Returns False when the password does not match the stored hash."""
        stored = hash_password("hunter2", n=2, r=8, p=1)
        assert verify_password("wrong", stored) is False

    def test_tampered_digest_fails(self):
        """Returns False when the digest field of the stored hash is tampered."""
        stored = hash_password("hunter2", n=2, r=8, p=1)
        parts = stored.split("$")
        parts[3] = "00" * 32
        assert verify_password("hunter2", "$".join(parts)) is False
