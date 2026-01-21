# src/depo/service/classify.py
"""
Content classification from bytes and hints.

Determines ItemKind and ContentFormat using priority:
requested_format > declared_mime > magic bytes > filename extension.

Author: Marcus Grant
Date: 2026-01-20
License: Apache-2.0
"""

from dataclasses import dataclass

from depo.model.enums import ContentFormat, ItemKind


@dataclass(frozen=True)
class ContentClassification:
    """Result of content classification."""

    kind: ItemKind
    format: ContentFormat


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


def classify(
    data: bytes,
    *,
    filename: str | None = None,
    declared_mime: str | None = None,
    requested_format: str | None = None,
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
    ...
