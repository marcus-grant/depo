# tests/service/test_media.py
"""
Testing of depo.service.media module

Author: Marcus Grant
Date: 2026-01-23
License: Apache-2.0
"""

from dataclasses import FrozenInstanceError

import pytest
from tests.factories import gen_image
from tests.helpers import assert_field

from depo.model.enums import ContentFormat
from depo.service.media import ImageInfo, get_image_info
from depo.util.errors import (
    ImageDecodeError,
    MissingDependencyError,
    PayloadEmptyError,
    UnsupportedFormatError,
)


class TestImageInfo:
    """Tests for ImageInfo DTO dataclass."""

    def test_frozen_dataclass(self):
        """Is a frozen dataclass"""
        obj = ImageInfo()
        assert isinstance(obj, ImageInfo)
        with pytest.raises(FrozenInstanceError):
            obj.width, obj.height, obj.format = 640, 480, ContentFormat.PNG  # type: ignore

    @pytest.mark.parametrize(
        ("name", "typ", "required", "default"),
        [
            ("format", ContentFormat | None, False, None),
            ("width", int | None, False, None),
            ("height", int | None, False, None),
        ],
    )
    def test_fields(self, name, typ, required, default):
        """Has expected field: name, type, optionality, default value"""
        assert_field(ImageInfo, name, typ, required, default)


class TestGetImageInfo:
    """Tests depo.service.media.get_image_info"""

    @pytest.mark.parametrize(
        "fmt, width, height, expected_fmt",
        [
            ("PNG", 3, 2, ContentFormat.PNG),
            ("JPEG", 2, 3, ContentFormat.JPEG),
            ("WEBP", 4, 2, ContentFormat.WEBP),
        ],
    )
    def test_image_info_for_valid_imgs(self, fmt, width, height, expected_fmt):
        """Returns ImageInfo with correct format & dimensions."""
        result = get_image_info(gen_image(fmt, width, height))
        assert isinstance(result, ImageInfo)
        assert result.format == expected_fmt
        assert result.width == width
        assert result.height == height

    @pytest.mark.parametrize(
        "data, raises",
        [
            (b"", PayloadEmptyError),  # empty
            (b"not an image", ImageDecodeError),  # non-image
            (b"\x89PNG\r\n\x1a\n" + b"\x00" * 10, ImageDecodeError),  # corrupted PNG
        ],
    )
    def test_raises_for_invalid_data(self, data, raises):
        """Raises PayloadEmptyError or ImageDecodeError for unreadable image data."""
        with pytest.raises(raises):
            get_image_info(data)

    def test_raises_for_unsupported_format(self):
        """Raises UnsupportedFormatError for format PIL reads but we don't support."""
        with pytest.raises(UnsupportedFormatError):
            get_image_info(gen_image("ICO", 16, 16))

    def test_raises_if_pillow_unavailable(self, monkeypatch):
        """Raises MissingDependencyError if Pillow (PIL) unavailable for import"""
        monkeypatch.setattr("depo.service.media._HAS_PILLOW", False)
        with pytest.raises(MissingDependencyError, match=r"(?i)pillow"):
            get_image_info(b"\x00")

    def test_works_with_pillow_roundtrip(self):
        """Ensures Pillow compatibility by testing with generated images"""
        result = get_image_info(gen_image("PNG", 128, 256))
        assert isinstance(result, ImageInfo)
        assert result.format == ContentFormat.PNG
        assert result.width == 128
        assert result.height == 256
