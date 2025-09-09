from typing import Optional, Union
from urllib.parse import urlparse
from django.conf import settings

IMAGE_URI_PREFIXES = ["data:image/png;base64", "data:image/jpeg;base64"]  # noqa


def file_empty(file_data: Union[bytes, None]) -> bool:
    """Check if file data is empty"""
    return file_data is None or file_data == b""


def file_too_big(file_data: bytes) -> bool:
    """Check if file data exceeds maximum size"""
    return len(file_data) > settings.MAX_UPLOAD_SIZE


# TODO: Handle cases where we want text or ie SVG where it's XML text
# TODO: Add module simply to store magic byte constants
def file_type(upload_bytes: bytes) -> Optional[str]:
    """Validate file type by checking magic bytes"""
    if b"\xff\xd8\xff" in upload_bytes:
        return "jpg"
    if b"\x89PNG\r\n\x1a\n" in upload_bytes:
        return "png"
    if b"GIF89a" in upload_bytes or b"GIF87a" in upload_bytes:
        return "gif"
    return None


def looks_like_url(text: Optional[str]) -> bool:
    """Check if text looks like a URL"""
    if not text or not isinstance(text, str):
        return False

    text = text.strip()

    try:
        parsed = urlparse(text)
        if parsed.scheme:
            return True
        parsed_with_https = urlparse(f"https://{text}")
        if (
            parsed_with_https.netloc
            and "." in parsed_with_https.netloc
            and " " not in text
        ):
            netloc = parsed_with_https.netloc
            if len(netloc) < 100 and not any(
                char in netloc for char in [" ", "\t", "\n"]
            ):
                return True
        return False
    except Exception:
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
