# src/depo/util/validate.py
"""
Input validation for ingest pipeline.

Pure validation functions that raise ValueError on failure.
No domain dependencies.

Author: Marcus Grant
Date: 2026-01-20
License: Apache-2.0
"""

from pathlib import Path


# TODO: Consider deleting these because they dont DRY anything
def validate_payload(
    payload_bytes: bytes | None,
    payload_path: Path | None,
) -> None:
    """Validate that exactly one payload source is provided.

    Args:
        payload_bytes: Content as in-memory bytes.
        payload_path: Path to content on disk.

    Raises:
        ValueError: If both are None or both are provided.
    """
    if (payload_bytes is None) == (payload_path is None):
        raise ValueError("Must provide exactly one of either payload bytes or path")


def validate_size(size: int, max_size: int) -> None:
    """Validate content/payload size against limit.

    Args:
        size: Content size in bytes.
        max_size: Maximum allowed size in bytes.

    Raises:
        ValueError: If size is negative or exceeds max_size.
    """
    if size > max_size:
        raise ValueError(f"Size ({size}) exceeds max_size ({max_size})")
    if size <= 0:
        raise ValueError("Size cannot be negative or empty (size <= 0)")
