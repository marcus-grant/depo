# src/depo/service/media.py
"""
Heavy media data metadata extraction.

Any heavy soft dependencies for media handling should go here.
Soft dependency on Pillow —
raises ImportError or MissingDependencyError if unavailable.

Author: Marcus Grant
Date: 2026-01-23
License: Apache-2.0
"""

from dataclasses import dataclass
from io import BytesIO

from depo.model.enums import ContentFormat
from depo.util.errors import (
    ImageDecodeError,
    MissingDependencyError,
    PayloadEmptyError,
    UnsupportedFormatError,
)

# Dynamically import Pillow at module level with flags for testing or deployment
# Shouldn't attempt to load pillow unless this module is used
_HAS_PILLOW: bool
try:
    import PIL

    _HAS_PILLOW = True
    del PIL  # keeps namespace clean
except ImportError:
    _HAS_PILLOW = False


@dataclass(frozen=True)
class ImageInfo:
    """Image metadata extracted from bytes."""

    format: ContentFormat | None = None
    width: int | None = None
    height: int | None = None


# NOTE: Update this map when adding support for new formats
_PILLOW_TO_FORMAT: dict[str, ContentFormat] = {
    "PNG": ContentFormat.PNG,
    "JPEG": ContentFormat.JPEG,
    "WEBP": ContentFormat.WEBP,
}


def get_image_info(data: bytes) -> ImageInfo:
    """Extract image metadata from bytes.

    Args:
        data: Image bytes.

    Returns:
        ImageInfo with format, width, height.

    Raises:
        MissingDependencyError: If Pillow is not installed.
        PayloadEmptyError: If data is empty.
        ImageDecodeError: If data cannot be decoded as an image.
        UnsupportedFormatError: If image format is not supported by depo.
    """
    if len(data) <= 0:  # Check data length before attempting to decode/import
        raise PayloadEmptyError
    if not _HAS_PILLOW:
        raise MissingDependencyError("pillow")

    from PIL import Image, UnidentifiedImageError

    try:
        with Image.open(BytesIO(data)) as img:
            fmt, w, h = img.format, img.width, img.height
    except UnidentifiedImageError:
        raise ImageDecodeError from None
    if fmt not in _PILLOW_TO_FORMAT:
        raise UnsupportedFormatError(fmt)
    return ImageInfo(format=_PILLOW_TO_FORMAT[fmt], width=w, height=h)
