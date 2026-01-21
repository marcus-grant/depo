# src/depo/model/formats.py
"""
Bidirectional mapping between ContentFormat and MIME types.

Author: Marcus Grant
Date: 2026-01-20
License: Apache-2.0
"""

from depo.model.enums import ContentFormat, ItemKind

_FORMAT_TO_MIME_MAP: dict[ContentFormat, str] = {
    ContentFormat.PLAINTEXT: "text/plain",
    ContentFormat.MARKDOWN: "text/markdown",
    ContentFormat.JSON: "application/json",
    ContentFormat.YAML: "application/yaml",
    ContentFormat.PNG: "image/png",
    ContentFormat.JPEG: "image/jpeg",
    ContentFormat.WEBP: "image/webp",
}


def mime_for_format(fmt: ContentFormat) -> str:
    """Return MIME type for HTTP Content-Type header.
        Also wraps error reporting for unsupported formats.

    Args:
        fmt: Content format enum member.

    Returns:
        MIME type string (e.g., "image/png").

    Raises:
        ValueError: If format has no MIME mapping.
    """
    try:
        return _FORMAT_TO_MIME_MAP[fmt]
    except KeyError:
        f = fmt.name if hasattr(fmt, "name") else fmt
        raise ValueError(f"No MIME mapping for {f}") from None


# Extension overrides for formats where the canonical extension
# differs from the enum value. Add entries here when a format's
# common file extension doesn't match its ContentFormat.value.
_EXTENSION_OVERRIDES: dict[ContentFormat, str] = {
    ContentFormat.TIFF: "tif",  # DOS 8.3 legacy, widely expected
}


def extension_for_format(fmt: ContentFormat | str) -> str:
    """Return file extension for storage path.

    Most formats use their enum value directly (e.g., ContentFormat.PNG -> "png").
    Exceptions are defined in _EXTENSION_OVERRIDES for cases where the common
    extension differs from the canonical format name (e.g., TIFF -> "tif").

    Args:
        fmt: Content format enum member.

    Returns:
        Extension string without dot (e.g., "png", "tif").

    Raises:
        ValueError: If format has no extension mapping.
    """
    # Safety measure to quickly surface incomplete format handling code
    if not isinstance(fmt, ContentFormat):
        raise ValueError(f"No extension mapping for {fmt}")
    return _EXTENSION_OVERRIDES.get(fmt, fmt.value)


_FORMAT_TO_KIND_MAP: dict[ContentFormat, ItemKind] = {
    ContentFormat.PLAINTEXT: ItemKind.TEXT,
    ContentFormat.MARKDOWN: ItemKind.TEXT,
    ContentFormat.JSON: ItemKind.TEXT,
    ContentFormat.YAML: ItemKind.TEXT,
    ContentFormat.PNG: ItemKind.PICTURE,
    ContentFormat.JPEG: ItemKind.PICTURE,
    ContentFormat.WEBP: ItemKind.PICTURE,
    ContentFormat.TIFF: ItemKind.PICTURE,
}


def kind_for_format(fmt: ContentFormat) -> ItemKind:
    """Return ItemKind for a content format.

    Args:
        fmt: Content format enum member.

    Returns:
        ItemKind (TEXT or PICTURE).

    Raises:
        ValueError: If format has no kind mapping.
    """
    kind = _FORMAT_TO_KIND_MAP.get(fmt, None)
    if kind is None:
        raise ValueError(f"No ItemKind mapping for ContentFormat {fmt}")
    return kind
