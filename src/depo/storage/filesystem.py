# src/depo/storage/filesystem.py
"""
Local filesystem implementation of StorageBackend.

Author: Marcus Grant
Date: 2026-02-03
License: Apache-2.0
"""

from pathlib import Path
from typing import BinaryIO

from depo.model.enums import ContentFormat
from depo.storage.protocol import StorageBackend


class FilesystemStorage(StorageBackend):
    """Filesystem-backed storage for item payloads."""

    def __init__(self, root: Path) -> None:
        """
        Initialize storage with root directory.

        Args:
            root: Base directory for all stored files.
                  Created if it doesn't exist.
        """
        raise NotImplementedError

    def _path_for(self, code: str, format: ContentFormat) -> Path:
        """
        Derive storage path for an item.

        Args:
            code: Short code identifier.
            format: Content format (determines extension).

        Returns:
            Path: {root}/{code}.{ext}
        """
        raise NotImplementedError

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

        Args:
            code: Short code identifier.
            format: Content format.
            source_bytes: Raw bytes to write.
            source_path: Path to file to copy.

        Raises:
            ValueError: If neither or both source arguments provided.
        """
        raise NotImplementedError

    def open(self, *, code: str, format: ContentFormat) -> BinaryIO:
        """
        Open payload for reading.

        Args:
            code: Short code identifier.
            format: Content format.

        Returns:
            Binary file handle. Caller must close.

        Raises:
            FileNotFoundError: If payload doesn't exist.
        """
        raise NotImplementedError

    def delete(self, *, code: str, format: ContentFormat) -> None:
        """
        Remove payload from storage.

        Idempotent—no error if missing.

        Args:
            code: Short code identifier.
            format: Content format.
        """
        raise NotImplementedError
