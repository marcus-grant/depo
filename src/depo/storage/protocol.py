# src/depo/storage/protocol.py
"""
Storage backend protocol definition.

Author: Marcus Grant
Date: 2026-02-03
License: Apache-2.0
"""

from pathlib import Path
from typing import BinaryIO, Protocol

from depo.model.enums import ContentFormat


class StorageBackend(Protocol):
    """Protocol for payload storage backends."""

    def put(
        self,
        *,
        code: str,
        format: ContentFormat,
        source_bytes: bytes | None = None,
        source_path: Path | None = None,
    ) -> None:
        """
        Write payload to storage.

        Exactly one of source_bytes or source_path must be provided.

        Args:
            code: Short code identifier for the item.
            format: Content format (determines file extension).
            source_bytes: Raw bytes to write.
            source_path: Path to file to copy.

        Raises:
            ValueError: If neither or both source arguments provided.
        """
        ...

    def open(self, *, code: str, format: ContentFormat) -> BinaryIO:
        """
        Open payload for reading.

        Caller responsible for closing the handle.

        Args:
            code: Short code identifier for the item.
            format: Content format (determines file extension).

        Returns:
            Binary file handle for reading.

        Raises:
            FileNotFoundError: If payload doesn't exist.
        """
        ...

    def delete(self, *, code: str, format: ContentFormat) -> None:
        """
        Remove payload from storage.

        Idempotent—no error if file doesn't exist.

        Args:
            code: Short code identifier for the item.
            format: Content format (determines file extension).
        """
        ...
