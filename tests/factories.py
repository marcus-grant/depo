# tests/factories.py
# Author: Marcus Grant
# Date: 2026-01-09
# License: Apache-2.0

from depo.model.enums import ItemKind, PayloadKind, Visibility
from depo.model.item import Item, LinkItem, PicItem, TextItem
from depo.model.write_plan import WritePlan

### Item Factories ###

_ITEM_DEFAULTS = dict(
    code="ABC12345",
    hash_rest="06789DEFGHKMNPQR",
    kind=ItemKind.TEXT,
    mime="text/plain",
    size_b=100,
    uid=1,
    perm=Visibility.PUBLIC,
    upload_at=1234567890,
    origin_at=None,
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


### WritePlan Factories ###

_WRITE_PLAN_DEFAULTS = dict(
    hash_full="ABC1234567890DEFGHKMNPQR",
    code_min_len=8,
    payload_kind=PayloadKind.BYTES,
    kind=ItemKind.TEXT,
    mime="text/plain",
    size_b=100,
    upload_at=1234567890,
    origin_at=None,
    payload_bytes=None,
    payload_path=None,
    text_format=None,
    link_url=None,
    pic_format=None,
    pic_width=None,
    pic_height=None,
)


def make_write_plan(**overrides) -> WritePlan:
    return WritePlan(**(_WRITE_PLAN_DEFAULTS | overrides))  # pyright: ignore[reportArgumentType]
