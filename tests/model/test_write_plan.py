# tests/model/test_write_plan.py

"""
Test specifications for WritePlan DTO.

Verifies dataclass behavior, immutability, and field definitions.
WritePlan is the handoff between IngestService and Repository.

Author: Marcus Grant
Date: 2026-01-19
License: Apache-2.0
"""

from dataclasses import FrozenInstanceError, is_dataclass
from pathlib import Path

import pytest
from tests.factories import make_write_plan
from tests.helpers import assert_field

from depo.model.enums import ContentFormat, ItemKind, PayloadKind
from depo.model.write_plan import WritePlan


class TestWritePlan:
    """Test the WritePlan DTO class passesd from IngestService & Repository"""

    def test_is_dataclass(self):
        """Is a dataclass"""
        assert is_dataclass(WritePlan)

    @pytest.mark.parametrize(
        ("name", "typ", "required", "default"),
        # (field name, type, required?, default value)
        [
            ("hash_full", str, True, None),
            ("code_min_len", int, True, None),
            ("payload_kind", PayloadKind, True, None),
            ("payload_bytes", bytes | None, False, None),
            ("payload_path", Path | None, False, None),
            ("kind", ItemKind, True, None),
            ("format", ContentFormat | None, False, None),
            ("size_b", int, True, None),
            ("upload_at", int, True, None),
            ("origin_at", int | None, False, None),
            ("width", int | None, False, None),
            ("height", int | None, False, None),
            ("link_url", str | None, False, None),
        ],
    )
    def test_fields(self, name, typ, required, default):
        """Test specs of class dataclass fields"""
        assert_field(WritePlan, name, typ, required, default)

    def test_instantiate_requried_fields(self):
        """Instantiates with only required fields"""
        # See tests.factories.make_write_plan for default factory field values
        write_plan = make_write_plan(hash_full="F00BAR12")
        assert write_plan.hash_full == "F00BAR12"
        assert write_plan.code_min_len == 8
        assert write_plan.upload_at == 1234567890
        assert write_plan.origin_at is None
        assert write_plan.payload_path is None

    def test_frozen(self):
        """Is frozen (immutable)"""
        write_plan = make_write_plan()
        with pytest.raises(FrozenInstanceError):
            write_plan.hash_full = "F00BAR12"  # pyright: ignore[reportAttributeAccessIssue] noqa
