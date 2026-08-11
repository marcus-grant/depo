# tests/util/test_shortcode.py
"""
Tests for shortcode hashing and Crockford encoding.
Author: Marcus Grant
Date: 2026-01-26
Revisions: [2026-07-22, 2026-08-02]
License: Apache-2.0
"""

import pytest

from depo.util.shortcode import (
    canonicalize_code,
    hash_full_b32,
)

CONVENIENCE_ENCODED_VECTORS = [
    (b"Hello, World!\n", "C8SR6JYEF0BXP7J03F7EMAWB", "hello"),
    (b"\x00\xff\r\n\x1a", "56V71DGBAMEA57K94KP1NKF8", "hard_bytes"),
    (b"\xe2\x9c\x85", "2A9V46HDZYE86ESAZ71PZ8Y6", "check_emoji"),
]
CONVENIENCE_ENCODED_PYTEST = [
    pytest.param(x[0], x[1], id=x[2]) for x in CONVENIENCE_ENCODED_VECTORS
]


class TestHashFullB32:
    """Depo's thin wrapper over the b3c32 contract pipeline.

    Contract claims (composition, prefix relation, width guard) are
    certified upstream in b3c32's suite; this class proves only that
    depo's wrapper wires the import at 120 bits.
    """

    @pytest.mark.parametrize("data,expect", CONVENIENCE_ENCODED_PYTEST)
    def test_matches_frozen_codes(self, data: bytes, expect: str):
        """Wrapper output matches codes depo has already stored."""
        assert hash_full_b32(data) == expect


class TestCanonicalizeCode:
    """Contract section 5, the lenient side. Normalizes user-typed input
    toward canonical form.

    Coerces O to 0 and I and L to 1 unconditionally, since those are
    invalid in both the data alphabet and the checksum set. U is
    rejected, not coerced: it is the mod-37 check symbol, and coercing
    it to V waits on an explicit non-checksum declaration that no caller
    can yet make.
    """

    def test_uppercase_valid_input(self):
        """Valid lowercase input should be upper cased"""
        assert canonicalize_code("abcd1234") == "ABCD1234"

    @pytest.mark.parametrize(
        "code,expect",
        [
            pytest.param("oil1", "0111", id="lowercase_ambiguous"),
            pytest.param("OIL1OIL", "0111011", id="uppercase_ambiguous"),
            pytest.param("oIl1OiL", "0111011", id="mixcase_ambiguous"),
        ],
    )
    def test_ambiguous_char_mappings(self, code: str, expect: str):
        """Ambiguous characters O, I, L should map to 0, 1, 1."""
        assert canonicalize_code(code) == expect

    @pytest.mark.parametrize(
        "code,expect",
        [
            pytest.param("ab-cd", "ABCD", id="hyphen"),
            pytest.param("ab cd", "ABCD", id="space"),
            pytest.param("ab-cd 12", "ABCD12", id="mixed_separators"),
            pytest.param("AB--CD", "ABCD", id="double_hyphen"),
        ],
    )
    def test_separators_removed(self, code: str, expect: str):
        """Hyphens and spaces should be stripped for readability."""
        assert canonicalize_code(code) == expect

    @pytest.mark.parametrize(
        "code",
        [
            pytest.param("FOO!", id="exclamation"),
            pytest.param("=", id="equals"),
            pytest.param("abc@def", id="at_sign"),
            pytest.param("test_123", id="underscore"),
        ],
    )
    def test_rejects_invalid_chars(self, code: str):
        """Invalid characters should raise ValueError."""
        with pytest.raises(ValueError):
            canonicalize_code(code)

    @pytest.mark.parametrize(
        "code",
        [
            pytest.param("", id="empty"),
            pytest.param(" ", id="space_only"),
            pytest.param("  ", id="multiple_spaces"),
            pytest.param("-", id="hyphen_only"),
            pytest.param("- -", id="hyphens_and_spaces"),
            pytest.param(" - - ", id="padded_separators"),
        ],
    )
    def test_rejects_empty_after_norm(self, code: str):
        """Empty string after normalization should raise ValueError."""
        with pytest.raises(ValueError):
            canonicalize_code(code)

    @pytest.mark.parametrize(
        "code",
        [
            pytest.param("abcd123", id="simple"),
            pytest.param("oil1", id="ambiguous"),
            pytest.param("ab-cd 12", id="separators"),
            pytest.param("  OIL-O  ", id="mixed"),
        ],
    )
    def test_idempotent(self, code: str):
        """Canonical twice should produce same result as once"""
        once = canonicalize_code(code)
        twice = canonicalize_code(once)
        assert once == twice
