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
from depo.model.formats import format_for_mime, kind_for_format


# ======== ContentClassification DTO ========#
@dataclass(frozen=True)
class ContentClassification:
    """Result of content classification."""

    kind: ItemKind
    format: ContentFormat


# ======== Classification Helpers ========#
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
