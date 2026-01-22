# tests/service/test_classify.py
"""
Tests for service/classify.py content classification.

Author: Marcus Grant
Date: 2026-01-20
License: Apache-2.0
"""

from dataclasses import FrozenInstanceError, is_dataclass

import pytest
from tests.helpers import assert_field

from depo.model.enums import ContentFormat, ItemKind
from depo.model.formats import kind_for_format
from depo.service.classify import (
    ContentClassification,
    _detect_jpeg_magic,
    _detect_png_magic,
    _detect_webp_magic,
    _from_declared_mime,
    _from_filename,
    _from_magic_bytes,
    _from_requested_format,
    classify,
)



class TestContentClassification:
    """Tests for depo.service.classify.ContentClassification dataclass"""

    def test_is_frozen_dataclass(self):
        """Is a frozen dataclass."""
        assert is_dataclass(ContentClassification)
        with pytest.raises(FrozenInstanceError):
            k, f = ItemKind.TEXT, ContentFormat.PLAINTEXT
            c = ContentClassification(k, f)  # pyright: ignore
            c.kind = ItemKind.LINK  # pyright: ignore

    @pytest.mark.parametrize(
        "name,typ,required,default",
        [("kind", ItemKind, True, None), ("format", ContentFormat, True, None)],
    )
    def test_field_specs(self, name, typ, required, default):
        """Fields have correct name, type, optionality and defult."""
        assert_field(ContentClassification, name, typ, required, default)


class TestFromRequestedFormat:
    """Tests for _from_requested_format helper."""

    def test_returns_none_when_none(self):
        """Returns None if no format requested."""
        assert _from_requested_format(None) is None

    def test_returns_classification_with_correct_kind(self):
        """Returns ContentClassification with kind from kind_for_format."""
        for fmt in ContentFormat:
            result = _from_requested_format(fmt)
            msg_type = "Expected ContentClassification for "
            msg_type += f"{fmt.name}, got {type(result)}"
            assert isinstance(result, ContentClassification), msg_type
            assert result.format == fmt
            assert result.kind == kind_for_format(fmt)


class TestFromDeclaredMime:
    """Tests for _from_declared_mime helper."""

    def test_none_for_none(self):
        """Returns None if no MIME declared."""
        assert _from_declared_mime(None) is None

    def test_all_supported_mimes_classified_correctly(self):
        """All supported MIMEs return ContentClass. w/ correct format & kind."""
        from depo.model.formats import _MIME_TO_FORMAT_MAP

        # Loop through all supported MIME defined in _MIME_TO_FORMAT_MAP
        for mime, expected_fmt in _MIME_TO_FORMAT_MAP.items():
            result = _from_declared_mime(mime)
            msg = f"Expected ContentClassification for {mime}"
            assert result is not None, msg
            assert result.format == expected_fmt, f"Wrong format for {mime}"
            msg = f"Wrong kind for {mime}"
            assert result.kind == kind_for_format(expected_fmt), msg

    def test_none_for_unsupported_mime(self):
        """Returns None for unsupported MIME types."""
        assert _from_declared_mime("fake/MIME") is None


_PNG = b"\x89PNG\r\n\x1a\n"


class TestDetectPngMagic:
    """Tests for _detect_png_magic magic bytes detector"""

    def test_png_for_png_bytes(self):
        """Returns ContentFormat.PNG for valid PNG magic bytes"""
        assert _detect_png_magic(_PNG) == ContentFormat.PNG
        assert _detect_png_magic(_PNG + b"\xde\xad\xbe\xef") == ContentFormat.PNG

    def test_none_for_non_png_bytes(self):
        """Returns None for non-PNG, empty, or partial signature"""
        assert _detect_png_magic(b"\xde\xad\xbe\xef" * 99) is None, "non-PNG"
        assert _detect_png_magic(b"") is None, "empty"
        assert _detect_png_magic(b"\x89PNG\r\n\x1a") is None, "partial magic bytes"


# JPEG marker magic bytes (same prefix) suffixes (JFIF, EXIF, raw JPEG)
_JPG = [b"\xff\xd8\xff" + b for b in [b"\xe0", b"\xe1", b"\xdb"]]


class TestDetectJpegMagic:
    """Tests for _detect_jpeg_magic magic bytes detector"""

    @pytest.mark.parametrize("data", _JPG)
    def test_jpg_for_valid_bytes(self, data):
        """Returns ContentFormat.JPEG for valid JPEG magic bytes"""
        more_data = data + (b"\xde\xad\xbe\xef\x00") * 99
        assert _detect_jpeg_magic(data) == ContentFormat.JPEG
        assert _detect_jpeg_magic(more_data) == ContentFormat.JPEG

    def test_none_for_non_jpg_bytes(self):
        """Returns None for non-JPEG, empty, or partial signature"""
        assert _detect_jpeg_magic(b"\xde\xad\xbe\xef" * 99) is None, "non-JPG"
        assert _detect_jpeg_magic(b"") is None, "empty"
        assert _detect_jpeg_magic(b"\xff") is None, "partial magic 1 byte"
        assert _detect_jpeg_magic(b"\xff\xd8") is None, "partial magic 2 byte"
        assert _detect_jpeg_magic(b"\xff\xd8\xff") is None, "partial magic 3 byte"


# Test data constants for WEBP detection
_RIFF = b"RIFF"
_WEBP = b"WEBP"
_4x00 = b"\x00\x00\x00\x00"


class TestDetectWebpMagic:
    """Tests for _detect_webp_magic magic bytes detector"""

    @pytest.mark.parametrize(
        "data",
        [
            # Minimal boundary case: exactly 12 bytes
            (_RIFF + _4x00 + _WEBP),
            # Realistic sizes in RIFF size field (bytes 4-7, little-endian)
            (_RIFF + (0).to_bytes(4, "little") + _WEBP + b"VP8 " + _4x00),
            (_RIFF + (4).to_bytes(4, "little") + _WEBP + b"VP8L" + _4x00),
            (_RIFF + (0xFFFFFFFF).to_bytes(4, "little") + _WEBP + b"VP8X" + _4x00),
            # Arbitrary payload after header
            (_RIFF + b"\x12\x34\x56\x78" + _WEBP + b"\x00" * 32),
        ],
    )
    def test_webp_for_valid_bytes(self, data):
        """Returns ContentFormat.WEBP for valid WEBP magic bytes"""
        more_data = data + (b"\xde\xad\xbe\xef") * 99
        assert _detect_webp_magic(data) == ContentFormat.WEBP
        assert _detect_webp_magic(more_data) == ContentFormat.WEBP

    def test_none_for_invalid_bytes(self):
        """Returns None for non-WEBP, empty, partial, or malformed bytes"""
        # Non-WEBP bytes
        assert _detect_webp_magic(b"\xde\xad\xbe\xef" * 99) is None, "non-WEBP"
        # Empty
        assert _detect_webp_magic(b"") is None, "empty"
        # Shorter than 12 bytes
        assert _detect_webp_magic(_RIFF) is None, "4 bytes"
        assert _detect_webp_magic(_RIFF + _4x00) is None, "8 bytes"
        assert _detect_webp_magic(_RIFF + _4x00 + b"WEB") is None, "11 bytes"
        # RIFF without WEBP marker
        assert _detect_webp_magic(_RIFF + _4x00 + b"WAVE") is None, "RIFF but WAVE"


# _from_magic_bytes
class TestFromMagicBytes:
    """Tests for _from_magic_bytes magic bytes detection orchestrator"""

    @pytest.mark.parametrize(
        "data,kind,fmt",
        [
            (_PNG, ItemKind.PICTURE, ContentFormat.PNG),
            (_JPG[1], ItemKind.PICTURE, ContentFormat.JPEG),
            (_RIFF + _4x00 + _WEBP, ItemKind.PICTURE, ContentFormat.WEBP),
        ],
    )
    def test_class_for_valid_magic_bytes(self, data, kind, fmt):
        """Returns ContentClass for PNGs given PNG bytes"""
        result = _from_magic_bytes(data)
        assert isinstance(result, ContentClassification)
        assert result.kind == kind
        assert result.format == fmt

    def test_none_for_invalid_bytes(self):
        """Returns None for unrecognizable magic bytes from input"""
        assert _from_magic_bytes(b"\xde\xad\xbe\xef" * 99) is None, "Invalid bytes"
        assert _from_magic_bytes(b"") is None, "Empty bytes"
        assert _from_magic_bytes(b"\x0f") is None, "Single byte"


class TestFromFilename:
    """Tests for _from_filename extension & name based classification"""

    def test_none_for_none_filename(self):
        """Returns None if filename is None"""
        assert _from_filename(None) is None

    def test_classification_for_supported_extensions(self):
        """Returns ContentClassification for supported extensions"""
        # Use internal mapping to test all supported extensions & format pairs
        from depo.model.formats import _EXT_TO_FORMAT

        for ext, expected_fmt in _EXT_TO_FORMAT.items():
            # Arrange inputs and results
            filename = f"file.{ext}"

            # Act on tested funciton with inputs
            result = _from_filename(filename)

            # Assert result is ContentClass with expected format & kind
            msg = f"Expected ContentClassification type for filename {filename}"
            assert isinstance(result, ContentClassification), msg
            msg = f"Wrong format for filename {filename}, got {result.format}"
            assert result.format == expected_fmt, msg
            # Assert kind derived via kind_for_format
            msg = f"Wrong ItemKind for {filename}, got {result.kind}"
            assert result.kind == kind_for_format(expected_fmt)

    @pytest.mark.parametrize(
        "filename,expected_fmt",
        [
            ("FILE.txt", ContentFormat.PLAINTEXT),
            ("FILE.MD", ContentFormat.MARKDOWN),
            ("image.PnG", ContentFormat.PNG),
            ("pAcKaGe.jSoN", ContentFormat.JSON),
        ],
    )
    def test_classification_for_mixed_cases(self, filename, expected_fmt):
        """Returns ContentClassification for mixed-case extensions/filenames"""
        result = _from_filename(filename)
        assert isinstance(result, ContentClassification)
        assert result.format == expected_fmt
        assert result.kind == kind_for_format(expected_fmt)

    @pytest.mark.parametrize(
        "filename,expected_fmt",
        [
            (".tar.json", ContentFormat.JSON),
            (".j2.yaml", ContentFormat.YAML),
            ("20260122.bak.md", ContentFormat.MARKDOWN),
        ],
    )
    def test_handles_multiple_dots(self, filename, expected_fmt):
        """Returns classification using last extension for multi-dot filenames"""
        result = _from_filename(filename)
        assert isinstance(result, ContentClassification)
        assert result.format == expected_fmt
        assert result.kind == kind_for_format(expected_fmt)

    def test_none_for_no_extension(self):
        """Returns None for filenames without extension (e.g., README)"""
        assert _from_filename("README") is None

    def test_none_for_dotfiles_without_extension(self):
        """Returns None for dotfiles without extension (e.g., .bashrc)"""
        assert _from_filename(".bashrc") is None
        assert _from_filename(".md") is None

    def test_none_for_unsupported_extension(self):
        """Returns None for unsupported file extensions"""
        assert _from_filename("file.xyz") is None


# Test data for classify: each hint resolves to a different format
_PRIO_1 = ContentFormat.YAML  # YAML
_PRIO_MIME = "application/json"  # JSON
_PRIO_DATA = b"\x89PNG\r\n\x1a\n"  # PNG magic bytes
_PRIO_FILENAME = "notes.md"  # Markdown


class TestClassify:
    """Tests for classify orchestration function."""

    @pytest.mark.parametrize(
        "requested_format,declared_mime,data,filename,expected_fmt",
        [
            # All hints → uses requested_format (YAML)
            (_PRIO_1, _PRIO_MIME, _PRIO_DATA, _PRIO_FILENAME, ContentFormat.YAML),
            # No requested → uses declared_mime (JSON)
            (None, _PRIO_MIME, _PRIO_DATA, _PRIO_FILENAME, ContentFormat.JSON),
            # No requested, no mime → uses magic bytes (PNG)
            (None, None, _PRIO_DATA, _PRIO_FILENAME, ContentFormat.PNG),
            # No requested, no mime, no magic match → uses filename (MD)
            (None, None, b"no magic", _PRIO_FILENAME, ContentFormat.MARKDOWN),
        ],
    )
    def test_classification_priority(
        self, requested_format, declared_mime, data, filename, expected_fmt
    ):
        """Respects priority:
        requested_format > declared_mime > magic_bytes > filename."""
        result = classify(
            data,
            filename=filename,
            declared_mime=declared_mime,
            requested_format=requested_format,
        )
        assert isinstance(result, ContentClassification)
        assert result.format == expected_fmt
        assert result.kind == kind_for_format(expected_fmt)

    def test_raises_when_nothing_matches(self):
        """Raises ValueError when no classification strategy matches."""
        with pytest.raises(ValueError, match=r"^Unable to classify.*"):
            classify(b"no magic", filename="no_extension", declared_mime="fake/mime")
