# tests/model/test_item.py
# tests depo.model.item
# Marcus Grant 2026-01-19

from dataclasses import is_dataclass, FrozenInstanceError, fields, MISSING
import pytest

from depo.model.item import Item
from depo.model.enums import ItemKind, Visibility


class TestItem:
    """Tests for the Item model class"""

    def test_instance_dataclass(self):
        """Is a dataclass"""
        assert is_dataclass(Item)

    @pytest.mark.parametrize(
        ("name", "typ", "required", "default"),
        [
            ("code", str, True, None),
            ("hash_rest", str, True, None),
            ("kind", ItemKind, True, None),
            ("mime", str, True, None),
            ("size_b", int, True, None),
            ("created_at", int, True, None),
            ("uid", int, True, None),
            ("perm", Visibility, False, Visibility.PUBLIC),
        ],
    )
    def test_fields(self, name, typ, required, default):
        """Test name, type, optionality, default value of all fields"""
        field_map = {f.name: f for f in fields(Item)}
        f = field_map[name]
        assert name in field_map, f"missing field: {name}"
        assert f.type is typ, f"{name} type mismatch"
        if required:
            assert f.default is MISSING, f"{name} should be required"
        else:
            assert f.default == default, f"{name} default val mismatch"

    def test_frozen(self):
        """Is frozen (immutable)."""
        item = Item(
            code="ABC",
            hash_rest="DEF",
            kind=ItemKind.TEXT,
            mime="text/plain",
            size_b=100,
            created_at=1234567890,
            uid=1,
        )
        with pytest.raises(FrozenInstanceError):
            item.code = "new value"  # pyright: ignore[reportAttributeAccessIssue] noqa


# --- TextItem ---
# 1. Is a dataclass
# 2. Is frozen
# 3. Is subclass of Item
# 4. Has field `format` of type `str`
# 5. Inherits all Item fields
# 6. Can instantiate with all required fields


# --- PicItem ---
# 1. Is a dataclass
# 2. Is frozen
# 3. Is subclass of Item
# 4. Has field `format` of type `str`
# 5. Has field `width` of type `int`
# 6. Has field `height` of type `int`
# 7. Inherits all Item fields
# 8. Can instantiate with all required fields


# --- LinkItem ---
# 1. Is a dataclass
# 2. Is frozen
# 3. Is subclass of Item
# 4. Has field `url` of type `str`
# 5. Inherits all Item fields
# 6. Can instantiate with all required fields
