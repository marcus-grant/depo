# core/util/classifier.py
"""Content classification utilities - separate from content processing or validation"""

from django.core.files.uploadedfile import InMemoryUploadedFile
from dataclasses import dataclass
from typing import Optional, Dict, List
from urllib.parse import urlparse

import core.util.types as types

# TODO: May want to dynamically import PIL here to validate images more thoroughly


@dataclass
class ContentClass:
    ctype: Optional[types.CTypes] = None
    b64: bool = False
    ext: Optional[types.ValidExtensions] = None


MAGIC_BYTES_PIC: Dict[types.ValidExtensions, List[bytes]] = {
    "png": [b"\x89PNG\r\n\x1a\n"],
    "jpg": [b"\xff\xd8\xff\xe0", b"\xff\xd8\xff\xe1", b"\xff\xd8\xff\xdb"],
    "gif": [b"GIF8"],
}


def _classify_pic_format(content: bytes) -> Optional[types.ValidExtensions]:
    """Checks the magic bytes of the content to classify picture format"""
    for ext, magic_bytes_list in MAGIC_BYTES_PIC.items():
        if any(content.startswith(magic) for magic in magic_bytes_list):
            return ext
    return None


def _classify_content_bytes(content: bytes) -> ContentClass:
    """Classify uploaded bytes content ContentClass() means invalid content type"""
    # Try to detect magic bytes for valid picture file types
    if extension := _classify_pic_format(content):
        return ContentClass(ctype="pic", ext=extension)
    # Other byte content types should be added here...
    return ContentClass()  # None means this is not valid content


def _valid_netloc_format(netloc: str) -> bool:
    """Check for invalid netloc patterns"""
    if netloc.startswith(".") or netloc.endswith("."):
        return False
    # Check for double dots
    if ".." in netloc:
        return False
    # Validate port if present
    if ":" in netloc:
        host, port = netloc.rsplit(":", 1)
        try:
            port_num = int(port)
            if port_num < 1 or port_num > 65535:
                return False
        except ValueError:
            return False  # Non-numeric port
    return True


def is_url(text: str) -> bool:
    """Check if text looks like a valid web URL"""
    text = text.strip()
    if not text or " " in text:  # Reject any spaces
        return False
    try:
        parsed = urlparse(text)
        # Check for explicit http/https scheme
        if parsed.scheme and parsed.scheme.lower() in ["http", "https"]:
            if not parsed.netloc:
                return False
            return _valid_netloc_format(parsed.netloc)
        # Try adding https:// for domain-only format
        parsed_with_https = urlparse(f"https://{text}")
        if not parsed_with_https.netloc or "." not in parsed_with_https.netloc:
            return False
        return _valid_netloc_format(parsed_with_https.netloc)
    except Exception:
        return False


# Base64 URI prefixes with their corresponding formats
BASE64_URI_PREFIXES: Dict[types.ValidExtensions, List[str]] = {
    "png": ["data:image/png;base64,"],
    "jpg": ["data:image/jpeg;base64,", "data:image/jpg;base64,"],
    "gif": ["data:image/gif;base64,"],
}


def is_base64(content: str) -> bool:
    """Check if content follows data URI base64 pattern (ignores MIME type)"""
    # Check first ~48 characters for the pattern, avoid scanning entire string
    prefix = content[:48]
    return prefix.startswith("data:") and ";base64," in prefix


def _classify_base64_image(content: str) -> ContentClass:
    """Classify base64 image content - final classifier in the chain"""
    prefix_portion = content[:48]
    for ext, prefixes in BASE64_URI_PREFIXES.items():
        if any(prefix_portion.startswith(prefix) for prefix in prefixes):
            return ContentClass(ctype="pic", b64=True, ext=ext)
    # It's base64 but not a recognized image format
    return ContentClass(b64=True)


def _classify_content_base64(content: str) -> ContentClass:
    """Classify base64 content - handles images, future: PDFs, etc."""
    # Try image classification first
    image_result = _classify_base64_image(content)
    if image_result.ctype:  # If it found a valid image type
        return image_result
    # Fallback for unrecognized base64 content
    return ContentClass(ctype=None, b64=True, ext=None)


def _classify_content_string(content: str) -> ContentClass:
    """Classify string content - can be base64 images, URLs, or text"""
    # TODO: Check for base64 image data URIs first
    # TODO: Default to plain text
    if is_url(content):
        return ContentClass(ctype="url")
    if is_base64(content):
        return _classify_content_base64(content)
    return ContentClass(ctype="txt")


def classify_content(content: types.Content) -> ContentClass:
    """Classify content so long as it's a types.Content type.
    Returns the ContentClass dataclass so caller knows what to do with content."""
    if isinstance(content, bytes):
        return _classify_content_bytes(content)  # Uploaded bytes
    if isinstance(content, InMemoryUploadedFile):
        content.seek(0)
        content_bytes = content.read()
        content.seek(0)
        return _classify_content_bytes(content_bytes)
    return ContentClass()  # Default means invalid content type
