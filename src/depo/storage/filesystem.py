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
from depo.model.formats import extension_for_format
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
        self._root = root
        self._root.mkdir(parents=True, exist_ok=True)

    def _path_for(self, code: str, format: ContentFormat) -> Path:
        """
        Derive storage path for an item.

        Args:
            code: Short code identifier.
            format: Content format (determines extension).

        Returns:
            Path: {root}/{code}.{ext}
        """
        return self._root / f"{code}.{extension_for_format(format)}"

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
        # First validate source_* args
        if (source_bytes is None) == (source_path is None):
            raise ValueError("Exactly one of source_bytes or source_path required")
        if source_bytes is not None:
            # Write from bytes directly if source_bytes provided
            self._path_for(code, format).write_bytes(source_bytes)
        elif source_path is not None:
            # Write from bytes stored in source_path
            self._path_for(code, format).write_bytes(source_path.read_bytes())

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
        return self._path_for(code, format).open("rb")

    def delete(self, *, code: str, format: ContentFormat) -> None:
        """
        Remove payload from storage.

        Idempotent—no error if missing.

        Args:
            code: Short code identifier.
            format: Content format.
        """
        self._path_for(code, format).unlink(missing_ok=True)
