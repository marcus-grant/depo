# src/depo/service/classify.py
"""
Content classification from bytes and hints.

Determines ItemKind and ContentFormat using priority:
requested_format > declared_mime > magic bytes > filename extension.

Author: Marcus Grant
Date: 2026-01-20
License: Apache-2.0
"""

import re
from dataclasses import dataclass

from depo.model.enums import ContentFormat, ItemKind
from depo.model.formats import format_for_extension, format_for_mime, kind_for_format


# ======== Classify DTO ========#
@dataclass(frozen=True)
class ContentClassification:
    """Result of content classification."""

    kind: ItemKind
    format: ContentFormat


# ======== Classify Helpers ========#
def _from_requested_format(
    requested_format: ContentFormat | None,
) -> ContentClassification | None:
    """Classify from explicit user format request.

    Args:
        requested_format: Validated ContentFormat from user.

    Returns:
        ContentClassification if provided, None otherwise.
    """
    if requested_format is None:
        return None
    kind = kind_for_format(requested_format)
    return ContentClassification(kind=kind, format=requested_format)


def _from_declared_mime(declared_mime: str | None) -> ContentClassification | None:
    """Classify from HTTP Content-Type header.

    Args:
        declared_mime: MIME type from request header.

    Returns:
        ContentClassification if MIME is recognized, None otherwise.
    """
    if declared_mime is None:
        return None
    fmt = format_for_mime(declared_mime)
    if fmt is None:
        return None
    kind = kind_for_format(fmt)
    return ContentClassification(kind=kind, format=fmt)


_URL_PATTERN = r"^[^\s<>{}\[\]:]+\.[^\s<>{}\[\]:]{1,8}([/?#][^\s<>{}\[\]]*)?$"
_URL_REGEX = re.compile(_URL_PATTERN)


def _from_url_pattern(data: bytes) -> ContentClassification | None:
    """Classify from URL pattern in byte content.

    Attempts UTF-8 decode, then matches against HTTP(S) URL pattern.
    Strips surrounding whitespace before matching.

    Args:
        data: Content bytes.

    Returns:
        ContentClassification(LINK, LINK) if URL detected, None otherwise.
    """
    if data.count(b"://") != 1:  # Only exactly one scheme separator allowed
        return None
    try:  # URLs must be UTF-8 encoded as with all text content
        text = data.decode("utf-8").strip().lower()
    except UnicodeDecodeError:
        return None
    schema, text = text.split("://", 1)
    if schema not in ("http", "https"):  # Only support HTTP(S) URLs for now
        return None
    if not _URL_REGEX.match(
        text
    ):  # TODO: Simplify pattern by removing schema & domain matching
        return None
    return ContentClassification(kind=ItemKind.LINK, format=ContentFormat.LINK)


def _detect_png_magic(data: bytes) -> ContentFormat | None:
    """Detect PNG from magic bytes.

    PNG signature (hex): 89 50 4E 47 0D 0A 1A 0A (8 bytes)
                (ascii): .  P  N  G  CR LF SB LF

    Args:
        data: Content bytes.

    Returns:
        ContentFormat.PNG if signature matches, None otherwise.
    """
    magic = bytes.fromhex("89 50 4E 47 0D 0A 1A 0A")
    if data.startswith(magic):
        return ContentFormat.PNG
    return None


def _detect_jpeg_magic(data: bytes) -> ContentFormat | None:
    """Detect JPEG from magic bytes.

    JPEG signatures:
    - FF D8 FF E0 (JFIF)
    - FF D8 FF E1 (EXIF)
    - FF D8 FF DB (raw)

    Args:
        data: Content bytes.

    Returns:
        ContentFormat.JPEG if signature matches, None otherwise.
    """
    magic = [
        bytes.fromhex("FF D8 FF E0"),
        bytes.fromhex("FF D8 FF E1"),
        bytes.fromhex("FF D8 FF DB"),
    ]
    if any(data.startswith(m) for m in magic):
        return ContentFormat.JPEG
    return None


def _detect_webp_magic(data: bytes) -> ContentFormat | None:
    """Detect WEBP from magic bytes.

    WEBP signature: RIFF....WEBP (bytes 0-3 = RIFF, bytes 8-11 = WEBP)
    Bytes 4-7 are file size (ignored).

    Args:
        data: Content bytes.

    Returns:
        ContentFormat.WEBP if signature matches, None otherwise.
    """
    if len(data) < 12:
        return None
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ContentFormat.WEBP
    return None


_MAGIC_DETECTORS = [_detect_png_magic, _detect_jpeg_magic, _detect_webp_magic]


def _from_magic_bytes(data: bytes) -> ContentClassification | None:
    """Classify from file signature (magic bytes).

    Args:
        data: Content bytes.

    Returns:
        ContentClassification if signature recognized, None otherwise.
    """
    for detector in _MAGIC_DETECTORS:
        fmt = detector(data)
        if fmt is not None:
            return ContentClassification(kind=kind_for_format(fmt), format=fmt)
    return None


def _from_filename(filename: str | None) -> ContentClassification | None:
    """Classify from filename extension.

    Args:
        filename: Original filename (e.g., "notes.md", "image.png").

    Returns:
        ContentClassification if extension recognized, None otherwise.
    """
    if filename is None:
        return None
    parts = filename.rsplit(".", 1)
    if len(parts) < 2 or parts[0] == "":
        return None
    fmt = format_for_extension(parts[1])
    if fmt is None:
        return None
    try:
        kind = kind_for_format(fmt)
    except ValueError:
        return None
    return ContentClassification(kind=kind, format=fmt)


# ======== Classify Orchestrator ========#
def classify(
    data: bytes,
    *,
    filename: str | None = None,
    declared_mime: str | None = None,
    requested_format: ContentFormat | None = None,
) -> ContentClassification:
    """Classify content and return kind/format.

    Args:
        data: Content bytes (used for magic byte detection).
        filename: Original filename hint (extension used as fallback).
        declared_mime: MIME type from HTTP Content-Type header.
        requested_format: Explicit format requested by user.

    Returns:
        ContentClassification with kind and format.

    Raises:
        ValueError: If content cannot be classified to a supported format.
    """
    try:
        result = (
            _from_requested_format(requested_format)
            or _from_declared_mime(declared_mime)
            or _from_magic_bytes(data)
            or _from_filename(filename)
        )
    except ValueError as e:
        raise ValueError(f"Unable to classify: Classification error: {e}") from None
    if result is None:
        inputs = requested_format or declared_mime or filename or "data bytes"
        msg = f"Unable to classify content to a supported format with inputs: {inputs}"
        raise ValueError(msg)
    return result
