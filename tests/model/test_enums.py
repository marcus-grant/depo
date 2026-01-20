# tests/model/test_enums.py
"""
Tests for depo/model/enums.py.

Author: Marcus Grant
Date: 2026-01-19
License: Apache-2.0
"""

from enum import StrEnum

import pytest

from depo.model.enums import ContentFormat, ItemKind, PayloadKind, Visibility


class TestItemKind:
    """Tests the ItemKind enum used as a content discriminator."""

    def test_is_str_enum(self):
        """Always a StrEnum subclass."""
        for member in ItemKind:
            assert isinstance(member, StrEnum)

    def test_member_count(self):
        """Always 3 members for now"""
        assert len(ItemKind) == 3

    @pytest.mark.parametrize(
        "key,val", [("TEXT", "txt"), ("LINK", "url"), ("PICTURE", "pic")]
    )
    def test_member_key_values(self, key, val):
        """Should have these expected member names"""
        member = ItemKind[key]
        assert member.name == key
        assert member.value == val
        assert member == val


class TestVisibility:
    """Test visibility or perm or Permission Enum"""

    def test_is_str_enum(self):
        """Always a StrEnum subclass."""
        for member in Visibility:
            assert isinstance(member, StrEnum)

    def test_member_count(self):
        """Always 3 members for now"""
        assert len(Visibility) == 3

    @pytest.mark.parametrize(
        "key,val", [("UNLISTED", "unl"), ("PRIVATE", "prv"), ("PUBLIC", "pub")]
    )
    def test_member_key_values(self, key, val):
        """Should have these expected member names"""
        member = Visibility[key]
        assert member.name == key
        assert member.value == val
        assert member == val


class TestPayloadKind:
    """Test PayloadKind enum, gives info on how to handle payload"""

    def test_is_str_enum(self):
        """Always a StrEnum subclass."""
        for member in PayloadKind:
            assert isinstance(member, StrEnum)

    def test_member_count(self):
        """Always 2 members for now"""
        assert len(PayloadKind) == 2

    @pytest.mark.parametrize("key,val", [("BYTES", "byte"), ("FILE", "file")])
    def test_member_key_values(self, key, val):
        """Should have these expected member names"""
        member = PayloadKind[key]
        assert member.name == key
        assert member.value == val
        assert member == val


class TestContentFormat:
    """Tests ContentFormat enum against its supported formats."""

    def test_is_str_enum(self):
        """Always a StrEnum subclass."""
        for member in ContentFormat:
            assert isinstance(member, StrEnum)

    def test_member_count(self):
        assert len(ContentFormat) == 8

    @pytest.mark.parametrize(
        "key,val",
        [
            ("PLAINTEXT", "txt"),
            ("MARKDOWN", "md"),
            ("JSON", "json"),
            ("YAML", "yaml"),
            ("PNG", "png"),
            ("JPEG", "jpg"),
            ("WEBP", "webp"),
        ],
    )
    def test_member_key_values(self, key, val):
        """Has these member key/value pairings"""
        member = ContentFormat[key]
        assert member.name == key
        assert member.value == val
        assert member == val
