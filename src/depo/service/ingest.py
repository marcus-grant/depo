# src/depo/service/ingest.py
"""
Ingest pipeline orchestrator.

Thin service that wires validation, hashing, classification,
and metadata extraction into a WritePlan.

Author: Marcus Grant
Date: 2026-01-23
License: Apache-2.0
"""

import time
from pathlib import Path

from depo.model.enums import ContentFormat, ItemKind, PayloadKind
from depo.model.write_plan import WritePlan
from depo.service.classify import classify
from depo.service.media import get_image_info
from depo.util.shortcode import hash_full_b32


# TODO: Create config loader infrastructure and centralized defaults
# TODO: Implement file streaming for classification, hashing and sizing
class IngestService:
    """Orchestrates the ingest pipeline."""

    def __init__(
        self, *, min_code_length: int = 8, max_size_bytes: int = 2**20
    ) -> None:
        """Initialize with configuration.

        Args:
            min_code_length: Minimum short code length.
            max_size_bytes: Maximum allowed upload size.
        """
        self.min_code_length = min_code_length
        self.max_size_bytes = max_size_bytes

    def build_plan(
        self,
        *,
        payload_bytes: bytes | None = None,
        payload_path: Path | None = None,
        filename: str | None = None,
        declared_mime: str | None = None,
        requested_format: ContentFormat | None = None,
    ) -> WritePlan:
        """Build a WritePlan from upload data.

        Args:
            payload_bytes: Content as in-memory bytes.
            payload_path: Path to content on disk.
            filename: Original filename hint.
            declared_mime: MIME type from HTTP header.
            requested_format: Explicit format requested by user.

        Returns:
            WritePlan ready for repository persistence.

        Raises:
            ValueError: If validation or classification fails.
            ValueError: If invalid size payload given
        """
        # Validate and resolve payload to bytes
        if (payload_bytes is None) == (payload_path is None):
            raise ValueError("Expected one of payload_bytes or payload_path.")
        if payload_bytes is not None:
            data = payload_bytes
            payload_kind = PayloadKind.BYTES
        else:
            assert payload_path is not None  # for type checker
            data = payload_path.read_bytes()
            payload_kind = PayloadKind.FILE

        # Validate size
        size = len(data)
        if size > self.max_size_bytes:
            msg = f"Payload size {size} bytes exceeds limit {self.max_size_bytes}"
            raise ValueError(msg)
        if size <= 0:
            raise ValueError("Payload is empty")

        # Create shortcode from payload and classify it
        hash = hash_full_b32(data)
        content_class = classify(
            data,
            filename=filename,
            declared_mime=declared_mime,
            requested_format=requested_format,
        )

        # If ItemKind.PICTURE - Extract Image metadata & verify image data
        width, height = None, None
        if content_class.kind == ItemKind.PICTURE:
            img_info = get_image_info(data)
            width, height = img_info.width, img_info.height

        # Assemble write plan
        return WritePlan(
            payload_kind=payload_kind,
            size_b=size,
            code_min_len=self.min_code_length,
            hash_full=hash,
            kind=content_class.kind,
            format=content_class.format,
            upload_at=int(time.time()),
            width=width,
            height=height,
        )
