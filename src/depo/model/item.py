# src/depo/model/item.py
"""
Domain models for content items.

Defines Item base class & its subtypes: TextItem, PicItem, LinkItem, etc.
These are pure, frozen dataclasses representing content-addressed items.
No I/O or framework dependencies.

Author: Marcus Grant
Date: 2026-01-19
License: Apache-2.0
"""

from dataclasses import dataclass

from depo.model.enums import ContentFormat, ItemKind, Visibility


@dataclass(frozen=True, kw_only=True)
class Item:
    code: str
    hash_full: str
    kind: ItemKind
    size_b: int
    uid: int
    perm: Visibility
    upload_at: int
    origin_at: int | None = None


@dataclass(frozen=True, kw_only=True)
class TextItem(Item):
    """
    Text content item.

    Covers plain text, code, markdown, data formats (JSON, YAML, CSV).
    Format field determines rendering behavior on /info.
    """

    format: ContentFormat = ContentFormat.PLAINTEXT


@dataclass(frozen=True, kw_only=True)
class LinkItem(Item):
    """
    URL shortener/bookmarking item.

    Explicit creation only; no auto-detection.
    Redirects to target URL on access.
    """

    url: str


@dataclass(frozen=True, kw_only=True)
class PicItem(Item):
    """
    Image content item.

    Raster formats only for MVP (PNG, JPEG, GIF, WEBP).
    Dimensions required; EXIF support deferred.
    """

    format: ContentFormat
    width: int
    height: int
