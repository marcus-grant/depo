# tests/model/test_item.py
# tests depo.model.item
# Marcus Grant 2026-01-19

from dataclasses import MISSING, FrozenInstanceError, fields, is_dataclass

import pytest
from tests.factories import make_item, make_link_item, make_pic_item, make_text_item

from depo.model.enums import ItemKind, Visibility
from depo.model.item import Item, LinkItem, PicItem, TextItem

# Used to verify field specifications
# "name": field name, "typ": type (avoid py keyword),
# "required": non-optional, "default": default value
_ITEM_PARAM_NAMES = ("name", "typ", "required", "default")
_ITEM_PARAMS = [
    ("code", str, True, None),
    ("hash_rest", str, True, None),
    ("kind", ItemKind, True, None),
    ("mime", str, True, None),
    ("size_b", int, True, None),
    ("created_at", int, True, None),
    ("uid", int, True, None),
    ("perm", Visibility, True, None),
]


# TODO: Refactor with this assetion helper:
def _assert_field(cls, name, typ, required, default):
    field_map = {f.name: f for f in fields(cls)}
    assert name in field_map, f"missing field: {name}"
    f = field_map[name]
    assert f.type is typ, f"{name} type mismatch"
    if required:
        assert f.default is MISSING, f"{name} should be required"
    else:
        assert f.default == default, f"{name} default val mismatch"


class TestItem:
    """Tests for the Item model class"""

    def test_instance_dataclass(self):
        """Is a dataclass"""
        assert is_dataclass(Item)

    @pytest.mark.parametrize(_ITEM_PARAM_NAMES, _ITEM_PARAMS)
    def test_fields(self, name, typ, required, default):
        """Test name, type, optionality, default value of all fields"""
        _assert_field(Item, name, typ, required, default)

    def test_frozen(self):
        """Is frozen (immutable)."""
        item = make_item()
        with pytest.raises(FrozenInstanceError):
            item.code = "new value"  # pyright: ignore[reportAttributeAccessIssue] noqa


class TestTextItem:
    """Test TextItem dataclass (subtype of Item for text content)"""

    def test_instance_dataclass(self):
        """Is a dataclass"""
        assert is_dataclass(TextItem)

    def test_subclass_of_item(self):
        """Is a subclass of Item"""
        assert issubclass(TextItem, Item)

    @pytest.mark.parametrize(_ITEM_PARAM_NAMES, [("format", str, False, "txt")])
    def test_fields(self, name, typ, required, default):
        """Test name, type, optionality, default value of all fields"""
        _assert_field(TextItem, name, typ, required, default)

    @pytest.mark.parametrize(_ITEM_PARAM_NAMES, _ITEM_PARAMS)
    def test_inherits_item_fields(self, name, typ, required, default):
        """Inherits all Item field specifications"""
        _assert_field(TextItem, name, typ, required, default)

    def test_frozen(self):
        """Is frozen (immutable)"""
        textitem = make_text_item()
        with pytest.raises(FrozenInstanceError):
            textitem.code = "F00BAR"  # pyright: ignore[reportAttributeAccessIssue] noqa

    def test_instantiate(self):
        """Can instantiate with all requried fields"""
        textitem = make_text_item()
        assert textitem.code == "ABC12345"
        assert textitem.format == "txt"


class TestLinkItem:
    """Test LinkItem subclass type of Item content"""

    def test_instance_dataclass(self):
        """Is a dataclass"""
        assert is_dataclass(LinkItem)

    def test_subclass_of_item(self):
        """Subclass of Item"""
        assert issubclass(LinkItem, Item)

    @pytest.mark.parametrize(_ITEM_PARAM_NAMES, [("url", str, True, None)])
    def test_fields(self, name, typ, required, default):
        """Test name, type, optionality, default value of all fields"""
        _assert_field(LinkItem, name, typ, required, default)

    @pytest.mark.parametrize(_ITEM_PARAM_NAMES, _ITEM_PARAMS)
    def test_inherits_item_fields(self, name, typ, required, default):
        """Inherits all Item field specifications from subclass"""
        _assert_field(LinkItem, name, typ, required, default)

    def test_instantiate(self):
        """Can instantiate with all requried fields"""
        linkitem = make_link_item()
        assert linkitem.code == "ABC12345"
        assert linkitem.url == "https://example.com"

    def test_frozen(self):
        """Is frozen (immutable)"""
        linkitem = make_link_item()
        with pytest.raises(FrozenInstanceError):
            linkitem.code = "F00BAR"  # pyright: ignore[reportAttributeAccessIssue] noqa


class TestPicItem:
    """Test PicItem subclass type of Item content"""

    def test_instance_dataclass(self):
        """Is a dataclass"""
        assert is_dataclass(PicItem)

    def test_subclass_of_item(self):
        """Subclass of Item"""
        assert issubclass(PicItem, Item)

    @pytest.mark.parametrize(
        _ITEM_PARAM_NAMES,
        [
            ("format", str, True, None),
            ("width", int, True, None),
            ("height", int, True, None),
        ],
    )
    def test_fields(self, name, typ, required, default):
        """Test name, type, optionality, default value of all fields"""
        _assert_field(PicItem, name, typ, required, default)

    @pytest.mark.parametrize(_ITEM_PARAM_NAMES, _ITEM_PARAMS)
    def test_inherits_item_fields(self, name, typ, required, default):
        """Inherits all Item field specifications from subclass"""
        _assert_field(PicItem, name, typ, required, default)

    def test_instantiate(self):
        """Can instantiate with all requried fields"""
        linkitem = make_link_item()
        assert linkitem.code == "ABC12345"
        assert linkitem.url == "https://example.com"

    def test_frozen(self):
        """Is frozen (immutable)"""
        picitem = make_pic_item()
        with pytest.raises(FrozenInstanceError):
            picitem.code = "F00BAR"  # pyright: ignore[reportAttributeAccessIssue] noqa
