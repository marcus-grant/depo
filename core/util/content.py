import base64
from dataclasses import dataclass
from enum import Enum
import logging
from io import BytesIO
from typing import Optional, Union

from django.core.files.uploadedfile import InMemoryUploadedFile

import core.util.validator as validator
import core.util.types as types

logger = logging.getLogger("depo." + __name__)


@dataclass
class Base64ConversionResult:
    """Result of base64 to bytes conversion"""

    data: Optional[bytes] = None
    error: Optional[str] = None
    mime: Optional[str] = None


def read_content_if_file(content: types.Content) -> Union[bytes, str]:
    """Simply seeks & reads if InMemoryUPloadedFile, otherwise returns str or bytes as is"""
    if isinstance(content, InMemoryUploadedFile):
        content.seek(0)
        content_bytes = content.read()
        content.seek(0)  # Reset for potential future reads
        return content_bytes
    return content


# def convert_base64_to_file(content: str) -> InMemoryUploadedFile:
#     """Convert base-64 data URI to InMemoryUploadedFile with security validation"""
#     # Extract content type and base-64 data
#     if content.startswith("data:image/png;base64,"):
#         claimed_type = "image/png"
#         filename = "clipboard.png"
#         b64_data = content[22:]  # Remove "data:image/png;base64," prefix
#     elif content.startswith("data:image/jpeg;base64,"):
#         claimed_type = "image/jpeg"
#         filename = "clipboard.jpg"
#         b64_data = content[23:]  # Remove "data:image/jpeg;base64," prefix
#     elif content.startswith("data:image/jpg;base64,"):
#         claimed_type = "image/jpeg"
#         filename = "clipboard.jpg"
#         b64_data = content[22:]  # Remove "data:image/jpg;base64," prefix
#     else:
#         raise ValueError("Unsupported data URI format")
#
#     # Decode base-64 data
#     try:
#         file_data = base64.b64decode(b64_data)
#     except Exception as e:
#         raise ValueError(f"Invalid base-64 data: {e}")
#
#     # Security hardening: Verify MIME type matches actual image data using Pillow
#     try:
#         from PIL import Image  # Import here since this is an optional dependency
#
#         image = Image.open(BytesIO(file_data))
#         actual_format = image.format.lower() if image.format else None
#
#         # Map claimed type to expected format
#         expected_format = None
#         if claimed_type == "image/png":
#             expected_format = "png"
#         elif claimed_type in ["image/jpeg", "image/jpg"]:
#             expected_format = "jpeg"
#
#         # Verify match
#         if actual_format != expected_format:
#             msg = f"MIME type mismatch detected: claimed {claimed_type} but actual format is {actual_format}"
#             logger.warning(msg)
#             raise ValueError(msg)
#
#         msg = "Base-64 image validation successful: "
#         msg += f"{actual_format}, size: {len(file_data)} bytes"
#         logger.info(msg)
#
#     except ImportError:
#         # CRITICAL: Pillow not available - this is a security issue on production
#         msg = "Pillow not available for image validation - cannot verify MIME types securely"
#         logger.critical(msg)
#         msg = "Image validation unavailable - server configuration error"
#         raise ValueError(msg)
#     except Exception as e:
#         logger.error(f"Image validation failed: {e}")
#         raise ValueError(f"Invalid image data: {e}")
#
#     # Create InMemoryUploadedFile
#     file_obj = BytesIO(file_data)
#     uploaded_file = InMemoryUploadedFile(
#         file=file_obj,
#         field_name="image",
#         name=filename,
#         content_type=claimed_type,
#         size=len(file_data),
#         charset=None,
#     )
#
#     return uploaded_file
#
#
# def decode_data_uri(content: str) -> "Base64ConversionResult":
#     """Convert base64 string to bytes with validation"""
#     if not validator.is_base64_image_format(content):
#         return Base64ConversionResult(success=False, error_type="not_base64_image")
#     if not validator.is_within_base64_size_limit(content):
#         return Base64ConversionResult(success=False, error_type="base64_too_large")
#
#     try:
#         file_data = convert_base64_to_file(content)
#     except ValueError as e:
#         error_msg = str(e)
#         if "Invalid base-64 data" in error_msg:
#             err_type = "base64_decode_error"
#             return Base64ConversionResult(success=False, error_type=err_type)
#         else:
#             err_type = "mime_type_mismatch"
#             return Base64ConversionResult(success=False, error_type=err_type)
#     return Base64ConversionResult(success=True, file_data=file_data.read())


def decode_base64(content: str) -> Base64ConversionResult:
    """Decode base64 string to bytes, handling data URIs"""
    if not validator.valid_base64_format(content):
        return Base64ConversionResult(error="invalid_base64")
    try:
        # Handle data URI format: data:mime/type;base64,actual_base64_data
        if content.startswith("data:"):
            # Extract mime type and base64 data
            header, base64_data = content.split(",", 1)
            mime_part = header.split(";")[0].replace("data:", "")
            bytes_data = base64.b64decode(base64_data)
            return Base64ConversionResult(data=bytes_data, mime=mime_part)
        else:
            # Plain base64 string
            bytes_data = base64.b64decode(content)
            return Base64ConversionResult(data=bytes_data)
    except Exception as e:
        return Base64ConversionResult(error=str(e))
