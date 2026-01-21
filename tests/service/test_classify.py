# tests/service/test_classify.py
"""
Tests for service/classify.py content classification.

Author: Marcus Grant
Date: 2026-01-20
License: Apache-2.0
"""

from dataclasses import FrozenInstanceError, is_dataclass

import pytest
from tests.helpers import assert_field

from depo.model.enums import ContentFormat, ItemKind
from depo.model.formats import kind_for_format
from depo.service.classify import (
    ContentClassification,
    _from_declared_mime,
    _from_requested_format,
    classify,
)


class TestContentClassification:
    """Tests for depo.service.classify.ContentClassification dataclass"""

    def test_is_frozen_dataclass(self):
        """Is a frozen dataclass."""
        assert is_dataclass(ContentClassification)
        with pytest.raises(FrozenInstanceError):
            k, f = ItemKind.TEXT, ContentFormat.PLAINTEXT
            c = ContentClassification(k, f)  # pyright: ignore
            c.kind = ItemKind.LINK  # pyright: ignore

    @pytest.mark.parametrize(
        "name,typ,required,default",
        [("kind", ItemKind, True, None), ("format", ContentFormat, True, None)],
    )
    def test_field_specs(self, name, typ, required, default):
        """Fields have correct name, type, optionality and defult."""
        assert_field(ContentClassification, name, typ, required, default)


class TestFromRequestedFormat:
    """Tests for _from_requested_format helper."""

    def test_returns_none_when_none(self):
        """Returns None if no format requested."""
        assert _from_requested_format(None) is None

    def test_returns_classification_with_correct_kind(self):
        """Returns ContentClassification with kind from kind_for_format."""
        for fmt in ContentFormat:
            result = _from_requested_format(fmt)
            msg_type = "Expected ContentClassification for "
            msg_type += f"{fmt.name}, got {type(result)}"
            assert isinstance(result, ContentClassification), msg_type
            assert result.format == fmt
            assert result.kind == kind_for_format(fmt)


class TestFromDeclaredMime:
    """Tests for _from_declared_mime helper."""

    def test_none_for_none(self):
        """Returns None if no MIME declared."""
        assert _from_declared_mime(None) is None

    def test_all_supported_mimes_classified_correctly(self):
        """All supported MIMEs return ContentClass. w/ correct format & kind."""
        from depo.model.formats import _MIME_TO_FORMAT_MAP

        # Loop through all supported MIME defined in _MIME_TO_FORMAT_MAP
        for mime, expected_fmt in _MIME_TO_FORMAT_MAP.items():
            result = _from_declared_mime(mime)
            msg = f"Expected ContentClassification for {mime}"
            assert result is not None, msg
            assert result.format == expected_fmt, f"Wrong format for {mime}"
            msg = f"Wrong kind for {mime}"
            assert result.kind == kind_for_format(expected_fmt), msg

    def test_none_for_unsupported_mime(self):
        """Returns None for unsupported MIME types."""
        assert _from_declared_mime("fake/MIME") is None
class TestClassify:
    """Tests for depo.service.classify.classify function"""

    @pytest.mark.skip("No implementation for classify yet")
    def test_placeholder(self):
        classify(b"hi")
