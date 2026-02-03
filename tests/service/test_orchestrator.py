# tests/service/test_orchestrator.py
"""
Tests for orchestrator module.

Author: Marcus Grant
Date: 2026-02-03
License: Apache-2.0
"""

from dataclasses import FrozenInstanceError

import pytest
from tests.factories.models import make_link_item, make_pic_item, make_text_item
from tests.helpers.assertions import assert_field

from depo.model.item import LinkItem, PicItem, TextItem
from depo.service.orchestrator import PersistResult


class TestPersistResult:
    """Tests for PersistResult DTO."""

    @pytest.mark.parametrize(
        ("name", "typ", "required", "default"),
        [
            ("item", LinkItem | PicItem | TextItem, True, None),
            ("created", bool, True, None),
        ],
    )
    def test_correct_fields(self, name, typ, required, default):
        """Field properties (name, type, required, default value) are correct."""
        assert_field(PersistResult, name, typ, required, default)

    def test_frozen_dataclass(self):
        """Is a frozen dataclass"""
        obj = PersistResult(item=make_link_item(), created=True)
        assert isinstance(obj, PersistResult)
        with pytest.raises(FrozenInstanceError):
            obj.created = False  # type: ignore

    def test_accepts_all_item_kinds(self):
        """Can be instantiated with any Item subtype."""
        for factory in [make_text_item, make_pic_item, make_link_item]:
            item = factory()
            result = PersistResult(item=item, created=False)
            assert result.item is item, f"Failed for {type(item).__name__}"
