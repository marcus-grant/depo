# tests/model/test_formats.py
"""
Tests for model/formats.py MIME and extension lookups.
Mostly tests relations of canonical ContentFormat & ItemKind to
other content specifiers like file extensions or MIME types.
Coverage is handled by enforcing consistent mappings to
different type specifiers including missing relations with ContentFormat's
NOTE: Developers must map relations of new ContentFormat before tests pass.

If a new relationship is needed you need to test that:
- Every ContentFormat member maps to one or more of this new type
- That there are no new type members without a single ContentFormat

Author: Marcus Grant
Date: 2026-01-20
License: Apache-2.0
"""

import pytest

from depo.model.enums import ContentFormat, ItemKind
from depo.model.formats import (
    extension_for_format,
    format_for_mime,
    kind_for_format,
    mime_for_format,
)

# NOTE: Central format specifications
# This test module is mostly for asserting schemas/relations
# Define all ContentFormat relations below in this order
# (ContentFormat, MIME, file extension, ItemKind)
_FORMAT_SPECS = [
    (ContentFormat.PLAINTEXT, "text/plain", "txt", ItemKind.TEXT),
    (ContentFormat.MARKDOWN, "text/markdown", "md", ItemKind.TEXT),
    (ContentFormat.JSON, "application/json", "json", ItemKind.TEXT),
    (ContentFormat.YAML, "application/yaml", "yaml", ItemKind.TEXT),
    (ContentFormat.PNG, "image/png", "png", ItemKind.PICTURE),
    (ContentFormat.JPEG, "image/jpeg", "jpg", ItemKind.PICTURE),
    (ContentFormat.WEBP, "image/webp", "webp", ItemKind.PICTURE),
    (ContentFormat.TIFF, "image/tiff", "tif", ItemKind.PICTURE),
]

# NOTE: Derived params for each test class
# Use centralized spec to generate all pytest.mark.parametrize lists here
# _FORMAT_SPECS format: [(ContentFormat, MIME, extension, ItemKind)]
_FMT_MIME = [(f, m) for f, m, _, _ in _FORMAT_SPECS]
_FMT_EXT = [(f, e) for f, _, e, _ in _FORMAT_SPECS]
_FMT_KIND = [(f, k) for f, _, _, k in _FORMAT_SPECS]
_MIME_FMT = [(m, f) for f, m, _, _ in _FORMAT_SPECS]

# NOTE: Special cases
# Some special cases need a different pattern
# Below is an example where two MIMEs map to same ContentFormat
_MIME_FMT_WITH_LEGACY = _MIME_FMT + [("application/x-yaml", ContentFormat.YAML)]


class TestMimeForFormat:
    """Tests for mime_for_format lookup function."""

    @pytest.mark.parametrize("fmt,mime", _FMT_MIME)
    def test_mime_mappings(self, fmt, mime):
        """Returns correct MIME string for given ContentFormat."""
        assert mime_for_format(fmt) == mime

    def test_all_formats_have_mime(self):
        """All ContentFormat members have a MIME mapping."""
        for fmt in ContentFormat:
            result = mime_for_format(fmt)
            msg = f"Expected str for {fmt.name}, got {type(result)}"
            assert isinstance(result, str), msg
            msg = f"Expected MIME format for {fmt.name}, got {result}"
            assert "/" in result, msg

    def test_raises_on_unsupported_format(self):
        """Raises ValueError for unsupported format."""
        with pytest.raises(ValueError):
            mime_for_format("not-supported")  # pyright: ignore[reportArgumentType]


class TestFormatForMime:
    """Tests for depo.model.formats.format_for_mime lookup function."""

    @pytest.mark.parametrize("mime,fmt", _MIME_FMT_WITH_LEGACY)
    def test_format_mappings(self, mime, fmt):
        """Returns correct ContentFormat for given MIME type.
        Also accounts for multiple common MIME types for same format.
        Example: application/yaml & application/x-yaml => ContentFormat.YAML."""
        assert format_for_mime(mime) == fmt

    def test_all_formats_reachable(self):
        """All ContentFormat members are reachable via some MIME type."""
        reachable = {fmt for _, fmt in _MIME_FMT}
        for fmt in ContentFormat:
            msg = f"ContentFormat {fmt.name} has no MIME mapping"
            assert fmt in reachable, msg

    def test_returns_none_for_unsupported_mime(self):
        """Returns None for unrecognized MIME types."""
        assert format_for_mime("application/octet-stream") is None
        assert format_for_mime("video/mp4") is None
        assert format_for_mime("nonsense") is None


class TestExtensionForFormat:
    """Tests for extension_for_format lookup function."""

    @pytest.mark.parametrize("fmt,ext", _FMT_EXT)
    def test_extension_mappings(self, fmt, ext):
        """Returns correct extension for each format."""
        assert extension_for_format(fmt) == ext

    def test_all_formats_have_extension(self):
        """All ContentFormat members have an extension mapping."""
        for fmt in ContentFormat:
            result = extension_for_format(fmt)
            msg = f"Expected str for {fmt.name}, got {type(result)}"
            assert isinstance(result, str), msg
            msg = f"Expected non-empty extension for {fmt.name}"
            assert len(result) > 0, msg

    def test_raises_on_unsupported_format(self):
        """Raises ValueError for unsupported format."""
        with pytest.raises(ValueError, match="No extension mapping"):
            extension_for_format("not_a_format")  # pyright: ignore[reportArgumentType]


class TestKindForFormat:
    """Tests for kind_for_format lookup function."""

    @pytest.mark.parametrize("fmt,kind", _FMT_KIND)
    def test_kind_mappings(self, fmt, kind):
        """Returns correct ItemKind for each format."""
        assert kind_for_format(fmt) == kind

    def test_all_formats_have_kind(self):
        """All ContentFormat members have a kind mapping."""
        for fmt in ContentFormat:
            result = kind_for_format(fmt)
            msg = f"Expected ItemKind for {fmt.name}, got {type(result)}"
            assert isinstance(result, ItemKind), msg

    def test_raises_on_unsupported_format(self):
        """Raises ValueError for unsupported format."""
        with pytest.raises(ValueError):
            kind_for_format("not-supported")  # pyright: ignore[reportArgumentType]
