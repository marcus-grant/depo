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
from depo.service.classify import ContentClassification, classify


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


class TestClassify:
    """Tests for depo.service.classify.classify function"""

    @pytest.mark.skip("No implementation for classify yet")
    def test_placeholder(self):
        classify(b"hi")
