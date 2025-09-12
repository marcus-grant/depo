# core/util/classifier.py
"""Content classification utilities - separate from content processing or validation"""

from django.core.files.uploadedfile import InMemoryUploadedFile
from dataclasses import dataclass
from typing import Optional, Dict, List

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
