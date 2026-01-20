# src/depo/model/enums.py
"""
Enums for domain models and DTOs.

StrEnum subclasses with short values for database storage.
ContentFormat values are canonical extensions used for storage paths
and format identification. MIME types are derived at serve time.

Author: Marcus Grant
Date: 2026-01-20
License: Apache-2.0
"""

from enum import StrEnum


class ItemKind(StrEnum):
    """Content type discriminator for Item subtypes."""

    TEXT = "txt"
    LINK = "url"
    PICTURE = "pic"


class Visibility(StrEnum):
    """Access control level for items."""

    UNLISTED = "unl"
    PRIVATE = "prv"
    PUBLIC = "pub"


class PayloadKind(StrEnum):
    """Payload source indicator for WritePlan.

    Tells downstream code whether to read from bytes in memory
    or from a file path on disk. Transient; not stored in DB.
    """

    BYTES = "byte"
    FILE = "file"


class ContentFormat(StrEnum):
    """Canonical content formats for supported file types.

    Values are short extensions used for storage paths and format
    identification. MIME types are derived at serve time via util/formats.py.
    """

    PLAINTEXT = "txt"
    MARKDOWN = "md"
    JSON = "json"
    YAML = "yaml"
    PNG = "png"
    JPEG = "jpg"
    WEBP = "webp"
