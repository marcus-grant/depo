# tests/model/test_formats.py
"""
Tests for model/formats.py MIME and extension lookups.

Author: Marcus Grant
Date: 2026-01-20
License: Apache-2.0
"""

import pytest

from depo.model.enums import ContentFormat, ItemKind
from depo.model.formats import extension_for_format, kind_for_format, mime_for_format


# mime_for_format
#
# 8. All ContentFormat members have a mapping (no ValueError)
class TestMimeForFormat:
    """Tests for depo.model.formats.mime_for_format"""

    @pytest.mark.parametrize(
        "fmt,mime",
        [
            (ContentFormat.PLAINTEXT, "text/plain"),
            (ContentFormat.MARKDOWN, "text/markdown"),
            (ContentFormat.JSON, "application/json"),
            (ContentFormat.YAML, "application/yaml"),
            (ContentFormat.PNG, "image/png"),
            (ContentFormat.JPEG, "image/jpeg"),
            (ContentFormat.WEBP, "image/webp"),
        ],
    )
    def test_returns_text_plain(self, fmt, mime):
        """Returns correct MIME string for given ContentFormat"""
        assert mime_for_format(fmt) == mime

    def test_raises_on_insupported_format(self):
        """When unsupported ContentFormat provided, raise ValueError"""
        with pytest.raises(ValueError):
            mime_for_format("not-supported")  # pyright: ignore[reportArgumentType]


class TestExtensionForFormat:
    """Tests for extension_for_format lookup function."""

    @pytest.mark.parametrize(
        "fmt,expected",
        [
            (ContentFormat.PLAINTEXT, "txt"),
            (ContentFormat.MARKDOWN, "md"),
            (ContentFormat.JSON, "json"),
            (ContentFormat.YAML, "yaml"),
            (ContentFormat.PNG, "png"),
            (ContentFormat.JPEG, "jpg"),
            (ContentFormat.WEBP, "webp"),
            (ContentFormat.TIFF, "tif"),
        ],
    )
    def test_extension_mappings(self, fmt, expected):
        """Returns correct extension for each format."""
        assert extension_for_format(fmt) == expected

    def test_all_formats_have_extension(self):
        """All ContentFormat members return a valid extension."""
        for fmt in ContentFormat:
            result = extension_for_format(fmt)
            assert isinstance(result, str)
            assert len(result) > 0

    def test_unsupported_raises(self):
        """Raises ValueError for unsupported format."""
        with pytest.raises(ValueError, match="No extension mapping"):
            extension_for_format("not_a_format")  # pyright: ignore[reportArgumentType]


class TestKindForFormat:
    """Tests for depo.service.classify.kind_for_format."""

    @pytest.mark.parametrize(
        "fmt,kind",
        [
            (ContentFormat.PLAINTEXT, ItemKind.TEXT),
            (ContentFormat.MARKDOWN, ItemKind.TEXT),
            (ContentFormat.JSON, ItemKind.TEXT),
            (ContentFormat.YAML, ItemKind.TEXT),
            (ContentFormat.PNG, ItemKind.PICTURE),
            (ContentFormat.JPEG, ItemKind.PICTURE),
            (ContentFormat.WEBP, ItemKind.PICTURE),
            (ContentFormat.TIFF, ItemKind.PICTURE),
        ],
    )
    def test_kind_mappings(self, fmt, kind):
        assert kind_for_format(fmt) == kind

    def test_all_format_members_mapped(self):
        """All ContentFormat members either return a kind or raise ValueError."""
        for fmt in ContentFormat:
            try:
                kind_for_format(fmt)
            except ValueError:
                msg = f"ContentFormat {fmt} has no kind mapping"
                pytest.fail(msg)

    def test_raises_on_unsupported_format(self):
        """Raises ValueError for unsupported format."""
        with pytest.raises(ValueError):
            kind_for_format("not-supported")  # pyright: ignore[reportArgumentType]
