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


def is_base64_image_format(content: str) -> bool:
    """Check if content is a base64-encoded image string"""
    for prefix in IMAGE_URI_PREFIXES:
        if content.startswith(prefix):
            return True
    return False


def is_within_base64_size_limit(content: str) -> bool:
    """Check if base64 content is within size limit"""
    max__size = getattr(settings, "DEPO_MAX_BASE64_SIZE", 8 * 1024 * 1024)
    if len(content) > max__size:
        return False
    return True
