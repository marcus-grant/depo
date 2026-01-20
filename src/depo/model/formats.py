# src/depo/model/formats.py
"""
Bidirectional mapping between ContentFormat and MIME types.

Author: Marcus Grant
Date: 2026-01-20
License: Apache-2.0
"""

from depo.model.enums import ContentFormat

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


def extension_for_format(fmt: ContentFormat) -> str:
    """Return file extension for storage path.

    Args:
        fmt: Content format enum member.

    Returns:
        Extension string without dot (e.g., "png").

    Raises:
        ValueError: If format has no extension mapping.
    """

    # NOTE:Exceptions where extension differs from enum value
    # Example: ContentFormat.TIFF -> "tif" (not in MVP)
    _EXTENSION_OVERRIDES: dict[ContentFormat, str] = {
        ContentFormat.TIFF: "tif",  # DOS 8.3 legacy, widely expected
    }

    if not isinstance(fmt, ContentFormat):
        raise ValueError(f"No extension mapping for {fmt}")
    return _EXTENSION_OVERRIDES.get(fmt, fmt.value)
