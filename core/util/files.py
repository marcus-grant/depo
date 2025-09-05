"""File I/O utility functions for handling uploads"""

from pathlib import Path
from typing import Tuple

from django.conf import settings


def save_upload(filename: str, file_data: bytes) -> bool:
    """
    Save uploaded file data to disk if it doesn't already exist.

    Args:
        filename: Name of file to save
        file_data: File content as bytes

    Returns:
        bool: True if file was saved, False if file already exists

    Raises:
        OSError: If file cannot be written
    """
    file_path = Path(settings.UPLOAD_DIR) / filename

    if file_path.exists():
        return False

    with open(file_path, "wb") as f:
        f.write(file_data)
    return True
