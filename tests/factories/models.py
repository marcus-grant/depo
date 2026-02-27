# tests/factories/models.py
"""
Factory functions for model instances.
Author: Marcus Grant
Date: 2026-01-26
License: Apache-2.0
"""

from depo.model.enums import ContentFormat, ItemKind, PayloadKind, Visibility
from depo.model.item import Item, LinkItem, PicItem, TextItem
from depo.model.write_plan import WritePlan

_HASH_SFX = "0123456789ABCDEFGHJKMNP"

_ITEM_DEFAULTS = dict(
    kind=ItemKind.TEXT,
    size_b=100,
    uid=1,
    perm=Visibility.PUBLIC,
    upload_at=1234567890,
    origin_at=None,
)


def make_item(**overrides) -> Item:
    defaults = _ITEM_DEFAULTS | dict(
        hash_full="X" + _HASH_SFX,
        code="X" + _HASH_SFX[:7],
    )
    return Item(**(defaults | overrides))  # type: ignore


def make_text_item(**overrides) -> TextItem:
    defaults = _ITEM_DEFAULTS | dict(
        hash_full="T" + _HASH_SFX,
        code="T" + _HASH_SFX[:7],
        format=ContentFormat.PLAINTEXT,
    )
    return TextItem(**(defaults | overrides))  # type: ignore


def make_link_item(**overrides) -> LinkItem:
    defaults = _ITEM_DEFAULTS | dict(
        hash_full="L" + _HASH_SFX,
        code="L" + _HASH_SFX[:7],
        kind=ItemKind.LINK,
        url="https://example.com",
    )
    return LinkItem(**(defaults | overrides))  # type: ignore


def make_pic_item(**overrides) -> PicItem:
    defaults = _ITEM_DEFAULTS | dict(
        hash_full="P" + _HASH_SFX,
        code="P" + _HASH_SFX[:7],
        kind=ItemKind.PICTURE,
        format=ContentFormat.JPEG,
        width=320,
        height=240,
    )
    return PicItem(**(defaults | overrides))  # type: ignore


def make_write_plan(**overrides) -> WritePlan:
    defaults = dict(
        hash_full="ABC1234567890DEFGHKMNPQR",
        code_min_len=8,
        payload_kind=PayloadKind.BYTES,
        kind=ItemKind.TEXT,
        size_b=100,
        upload_at=1234567890,
        format=None,
        origin_at=None,
        payload_bytes=None,
        payload_path=None,
        width=None,
        height=None,
    )
    return WritePlan(**(defaults | overrides))  # type: ignore
