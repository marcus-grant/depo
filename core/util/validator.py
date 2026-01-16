from typing import Optional, Type, Union
from urllib.parse import urlparse
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile

import core.util.types as types


IMAGE_URI_PREFIXES = ["data:image/png;base64", "data:image/jpeg;base64"]  # noqa


def content_empty(content: Optional[types.Content]) -> bool:
    """Check if content is empty"""
    if content is None:
        return True
    is_inmem_file = isinstance(content, InMemoryUploadedFile)
    if is_inmem_file and getattr(content, "size", 0) == 0:
        return True
    if len(content) == 0:  # could only be bytes or str here
        return True
    return False  # Here, content can only be non-empty


def content_too_big(content: Optional[types.Content]) -> bool:
    """Check if content data exceeds maximum size"""
    if content is None:
        return False
    is_inmem_file = isinstance(content, InMemoryUploadedFile)
    if is_inmem_file and getattr(content, "size", 0) > settings.MAX_UPLOAD_SIZE:
        return True
    if len(content) > settings.MAX_UPLOAD_SIZE:  # could only be bytes or str
        return True
    return False


# TODO: Move into validator as second pass validation
def is_within_base64_size_limit(content: str) -> bool:
    """Check if base64 content is within size limit"""
    max__size = getattr(settings, "DEPO_MAX_BASE64_SIZE", 8 * 1024 * 1024)
    if len(content) > max__size:
        return False
    return True


def valid_base64_format(base64_str: str) -> bool:
    """Validate if string is valid base64 format (data URI or plain base64)"""
    import base64
    import re

    # Extract base64 data from data URI if present
    if base64_str.startswith("data:"):
        # Extract the base64 part after the comma
        parts = base64_str.split(",", 1)
        if len(parts) != 2:
            return False
        base64_data = parts[1]
    else:
        base64_data = base64_str

    # Check if string contains only valid base64 characters
    base64_pattern = re.compile(r"^[A-Za-z0-9+/]*={0,2}$")
    if not base64_pattern.match(base64_data):
        return False

    # Try to decode to verify it's valid base64
    try:
        base64.b64decode(base64_data)
        return True
    except Exception:
        return False
