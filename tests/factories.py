# tests/factories.py
# Author: Marcus Grant
# Date: 2026-01-09
# License: Apache-2.0

from depo.model.enums import ItemKind, Visibility
from depo.model.item import Item, LinkItem, PicItem, TextItem

_ITEM_DEFAULTS = dict(
    code="ABC12345",
    hash_rest="06789DEFGHKMNPQRSTVWXYZ",
    kind=ItemKind.TEXT,
    mime="text/plain",
    size_b=100,
    created_at=1234567890,
    uid=1,
    perm=Visibility.PUBLIC,
)


def make_item(**overrides) -> Item:
    return Item(**(_ITEM_DEFAULTS | overrides))  # pyright: ignore[reportArgumentType]


def make_text_item(**overrides) -> TextItem:
    defaults = _ITEM_DEFAULTS | dict(format="txt")
    return TextItem(**(defaults | overrides))  # pyright: ignore[reportArgumentType]


def make_link_item(**overrides) -> LinkItem:
    defaults = _ITEM_DEFAULTS | dict(
        kind=ItemKind.LINK,
        mime="text/uri-list",
        url="https://example.com",
    )
    return LinkItem(**(defaults | overrides))  # pyright: ignore[reportArgumentType]


def make_pic_item(**overrides) -> PicItem:
    defaults = _ITEM_DEFAULTS | dict(
        kind=ItemKind.PICTURE,
        mime="image/png",
        format="png",
        width=320,
        height=240,
    )
    return PicItem(**(defaults | overrides))  # pyright: ignore[reportArgumentType]
