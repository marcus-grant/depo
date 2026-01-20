# tests/model/test_item.py
# tests depo.model.item
# Marcus Grant 2026-01-19

from dataclasses import FrozenInstanceError, is_dataclass

import pytest
from tests.factories import make_item, make_link_item, make_pic_item, make_text_item
from tests.helpers import assert_field

from depo.model.enums import ContentFormat, ItemKind, Visibility
from depo.model.item import Item, LinkItem, PicItem, TextItem

# Used to verify Item field specifications
# Pulled out for reuse because subtypes need to check inheritance of these fields
# "name": field name, "typ": type (avoid py keyword 'type'),
# "required": non-optional, "default": default value
_ITEM_PARAMS = [
    ("code", str, True, None),
    ("hash_rest", str, True, None),
    ("kind", ItemKind, True, None),
    ("size_b", int, True, None),
    ("uid", int, True, None),
    ("perm", Visibility, True, None),
    ("upload_at", int, True, None),
    ("origin_at", int | None, False, None),
]


class TestItem:
    """Tests for the Item model class"""

    def test_instance_dataclass(self):
        """Is a dataclass"""
        assert is_dataclass(Item)

    @pytest.mark.parametrize("name,typ,required,default", _ITEM_PARAMS)
    def test_fields(self, name, typ, required, default):
        """Test name, type, optionality, default value of all fields"""
        assert_field(Item, name, typ, required, default)

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

    @pytest.mark.parametrize(
        "name,typ,required,default", [("format", ContentFormat, False, "txt")]
    )
    def test_fields(self, name, typ, required, default):
        """Test name, type, optionality, default value of all fields"""
        assert_field(TextItem, name, typ, required, default)

    @pytest.mark.parametrize("name,typ,required,default", _ITEM_PARAMS)
    def test_inherits_item_fields(self, name, typ, required, default):
        """Inherits all Item field specifications"""
        assert_field(TextItem, name, typ, required, default)

    def test_frozen(self):
        """Is frozen (immutable)"""
        textitem = make_text_item()
        with pytest.raises(FrozenInstanceError):
            textitem.code = "F00BAR"  # pyright: ignore[reportAttributeAccessIssue] noqa

    def test_instantiate(self):
        """Can instantiate with all requried fields"""
        textitem = make_text_item()
        assert textitem.code == "ABC12345"
        assert textitem.format == ContentFormat.PLAINTEXT


class TestLinkItem:
    """Test LinkItem subclass type of Item content"""

    def test_instance_dataclass(self):
        """Is a dataclass"""
        assert is_dataclass(LinkItem)

    def test_subclass_of_item(self):
        """Subclass of Item"""
        assert issubclass(LinkItem, Item)

    @pytest.mark.parametrize("name,typ,required,default", [("url", str, True, None)])
    def test_fields(self, name, typ, required, default):
        """Test name, type, optionality, default value of all fields"""
        assert_field(LinkItem, name, typ, required, default)

    @pytest.mark.parametrize("name,typ,required,default", _ITEM_PARAMS)
    def test_inherits_item_fields(self, name, typ, required, default):
        """Inherits all Item field specifications from subclass"""
        assert_field(LinkItem, name, typ, required, default)

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
        "name,typ,required,default",
        [
            ("format", ContentFormat, True, None),
            ("width", int, True, None),
            ("height", int, True, None),
        ],
    )
    def test_fields(self, name, typ, required, default):
        """Test name, type, optionality, default value of all fields"""
        assert_field(PicItem, name, typ, required, default)

    @pytest.mark.parametrize("name,typ,required,default", _ITEM_PARAMS)
    def test_inherits_item_fields(self, name, typ, required, default):
        """Inherits all Item field specifications from subclass"""
        assert_field(PicItem, name, typ, required, default)

    def test_instantiate(self):
        """Can instantiate with all requried fields"""
        picitem = make_pic_item(format=ContentFormat.JPEG)
        assert picitem.code == "ABC12345"
        assert picitem.format == ContentFormat.JPEG

    def test_frozen(self):
        """Is frozen (immutable)"""
        picitem = make_pic_item()
        with pytest.raises(FrozenInstanceError):
            picitem.code = "F00BAR"  # pyright: ignore[reportAttributeAccessIssue] noqa
