"""File I/O utility functions for handling uploads"""

import logging
from pathlib import Path
from typing import Tuple

logger = logging.getLogger(__name__)


def save_upload(file_path: Path, file_data: bytes) -> None:
    """
    Save uploaded file data to disk if it doesn't already exist.

    Args:
        file_path: Path where file should be saved
        file_data: File content as bytes

    Raises:
        OSError: If file cannot be written
    """
    if file_path.exists():
        logger.info(f"File {file_path.name} already exists, skipping write")
        return

    with open(file_path, "wb") as f:
        f.write(file_data)
