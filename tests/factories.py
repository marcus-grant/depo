# tests/factories.py
# Author: Marcus Grant
# Date: 2026-01-09
# License: Apache-2.0

from depo.model.enums import ContentFormat, ItemKind, PayloadKind, Visibility
from depo.model.item import Item, LinkItem, PicItem, TextItem
from depo.model.write_plan import WritePlan

### Item Factories ###

_ITEM_DEFAULTS = dict(
    code="ABC12345",
    hash_rest="06789DEFGHKMNPQR",
    kind=ItemKind.TEXT,
    size_b=100,
    uid=1,
    perm=Visibility.PUBLIC,
    upload_at=1234567890,
    origin_at=None,
)


def make_item(**overrides) -> Item:
    return Item(**(_ITEM_DEFAULTS | overrides))  # pyright: ignore[reportArgumentType]


def make_text_item(**overrides) -> TextItem:
    defaults = _ITEM_DEFAULTS | dict(format=ContentFormat.PLAINTEXT)
    return TextItem(**(defaults | overrides))  # pyright: ignore[reportArgumentType]


def make_link_item(**overrides) -> LinkItem:
    defaults = _ITEM_DEFAULTS | dict(
        kind=ItemKind.LINK,
        url="https://example.com",
    )
    return LinkItem(**(defaults | overrides))  # pyright: ignore[reportArgumentType]


def make_pic_item(**overrides) -> PicItem:
    defaults = _ITEM_DEFAULTS | dict(
        kind=ItemKind.PICTURE,
        format=ContentFormat.PNG,
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
    size_b=100,
    upload_at=1234567890,
    format=None,
    origin_at=None,
    payload_bytes=None,
    payload_path=None,
    width=None,
    height=None,
    link_url=None,
)


def make_write_plan(**overrides) -> WritePlan:
    return WritePlan(**(_WRITE_PLAN_DEFAULTS | overrides))  # pyright: ignore[reportArgumentType]


### Image Factories ###
def gen_image(fmt: str, width: int, height: int) -> bytes:
    """Generate minimal valid image bytes."""

    from io import BytesIO

    from PIL import Image

    buf = BytesIO()
    img = Image.new("RGB", (width, height), color=(255, 0, 0))
    img.save(buf, format=fmt)
    return buf.getvalue()
