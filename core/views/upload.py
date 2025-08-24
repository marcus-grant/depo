# core/views/upload.py
import base64
import logging
import time
from io import BytesIO
from pathlib import Path
from typing import Optional

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.shortcuts import redirect, render

from core.models.pic import PicItem
from core.util.content import classify_type

logger = logging.getLogger("depo." + __name__)

# TODO: Read picture byte stream as chunks instead

# TODO: Reference theses constant messages in the response function
ACCEPT_EXTS = ".jpg,.jpeg,.png,.gif"
MSG_EXIST = "File already exists"
MSG_EMPTY = "Empty file uploaded"
MSG_INVALID = "Invalid or unknown filetype, not allowed"





def convert_base64_to_file(content: str) -> InMemoryUploadedFile:
    """Convert base-64 data URI to InMemoryUploadedFile with security validation"""
    # Extract content type and base-64 data
    if content.startswith("data:image/png;base64,"):
        claimed_type = "image/png"
        filename = "clipboard.png"
        b64_data = content[22:]  # Remove "data:image/png;base64," prefix
    elif content.startswith("data:image/jpeg;base64,"):
        claimed_type = "image/jpeg"
        filename = "clipboard.jpg"
        b64_data = content[23:]  # Remove "data:image/jpeg;base64," prefix
    elif content.startswith("data:image/jpg;base64,"):
        claimed_type = "image/jpeg"
        filename = "clipboard.jpg"
        b64_data = content[22:]  # Remove "data:image/jpg;base64," prefix
    else:
        raise ValueError("Unsupported data URI format")

    # Decode base-64 data
    try:
        file_data = base64.b64decode(b64_data)
    except Exception as e:
        raise ValueError(f"Invalid base-64 data: {e}")

    # Security hardening: Verify MIME type matches actual image data using Pillow
    try:
        from PIL import Image

        image = Image.open(BytesIO(file_data))
        actual_format = image.format.lower() if image.format else None

        # Map claimed type to expected format
        expected_format = None
        if claimed_type == "image/png":
            expected_format = "png"
        elif claimed_type in ["image/jpeg", "image/jpg"]:
            expected_format = "jpeg"

        # Verify match
        if actual_format != expected_format:
            logger.warning(
                f"MIME type mismatch detected: claimed {claimed_type} but actual format is {actual_format}"
            )
            raise ValueError(
                f"MIME type mismatch: claimed {claimed_type} but actual format is {actual_format}"
            )

        logger.info(
            f"Base-64 image validation successful: {actual_format}, size: {len(file_data)} bytes"
        )

    except ImportError:
        # CRITICAL: Pillow not available - this is a security issue on production
        logger.critical(
            "Pillow not available for image validation - cannot verify MIME types securely"
        )
        raise ValueError("Image validation unavailable - server configuration error")
    except Exception as e:
        logger.error(f"Image validation failed: {e}")
        raise ValueError(f"Invalid image data: {e}")

    # Create InMemoryUploadedFile
    file_obj = BytesIO(file_data)
    uploaded_file = InMemoryUploadedFile(
        file=file_obj,
        field_name="image",
        name=filename,
        content_type=claimed_type,
        size=len(file_data),
        charset=None,
    )

    return uploaded_file


# TODO: Move file byte validation to separate module
# Should include all upload validations and potentially determining filetype
# TODO: Handle cases where we want text or ie SVG where it's XML text
def validate_upload_bytes(upload_bytes: bytes) -> Optional[str]:
    if b"\xff\xd8\xff" in upload_bytes:
        return "jpg"
    if b"\x89PNG\r\n\x1a\n" in upload_bytes:
        return "png"
    if b"GIF89a" in upload_bytes or b"GIF87a" in upload_bytes:
        return "gif"
    return None


# TODO: Logging should be moved out to own module and/or midware
def process_file_upload(file_data: bytes) -> dict:
    """Extract core upload processing logic for reuse"""
    if not file_data or file_data == b"":
        return {"success": False, "message": MSG_EMPTY, "status": 400}

    if len(file_data) > settings.MAX_UPLOAD_SIZE:
        msg = f"File size {len(file_data)} exceeds limit of {settings.MAX_UPLOAD_SIZE} bytes"
        return {"success": False, "message": msg, "status": 400}

    pic_type = validate_upload_bytes(file_data)
    if not pic_type:
        return {"success": False, "message": MSG_INVALID, "status": 400}

    pic_item = PicItem.ensure(file_data)
    fname = f"{pic_item.item.code}.{pic_item.format}"
    fpath = Path(settings.UPLOAD_DIR) / fname

    if fpath.exists():
        return {
            "success": True,
            "message": MSG_EXIST,
            "item": pic_item,
            "filename": fname,
        }

    try:
        with open(fpath, "wb") as f:
            f.write(file_data)
        msg = f"Uploaded file {fname} successfully!"
        return {"success": True, "message": msg, "item": pic_item, "filename": fname}
    except OSError as e:
        logger.error(f"Error during upload file save: {e}")
        return {
            "success": False,
            "message": "Error during upload file save",
            "status": 500,
            "filename": fname,
        }


@login_required
def upload_view_post(req):
    time_start = time.time()
    logger.info("Upload initiated")
    pic_file = req.FILES.get("content")

    if not pic_file:
        return upload_response(req, msg="No file uploaded", err=True, stat=400)

    file_data = pic_file.read()
    result = process_file_upload(file_data)

    if not result["success"]:
        logger.error(result["message"])
        messages.error(req, result["message"])
        return upload_response(
            req, msg=result["message"], err=True, stat=result.get("status", 400)
        )

    time_elapsed = time.time() - time_start
    fname = result["filename"]
    logger.info(f"Upload completed: {fname} in {time_elapsed:.2f}seconds")
    return upload_response(req, msg=result["message"], stat=200, fname=fname)


# TODO: Handle pasting an image/binary data into textbox from clipboard
@login_required  # TODO: Do we need to block GET requests from non-users?
def web_upload_view(request):
    method = request.method
    if method == "GET":
        return render(request, "upload.html")  # GET case
    if method == "POST":
        # Detect base-64 image payloads in POST content
        content = request.POST.get("content", "")
        request.is_base64_image = (
            content.startswith("data:image/png;base64,")
            or content.startswith("data:image/jpeg;base64,")
            or content.startswith("data:image/jpg;base64,")
        )

        # Convert base-64 images to uploaded files
        if request.is_base64_image:
            # Feature flag check for safe rollout
            if not getattr(settings, "DEPO_ALLOW_BASE64_IMAGES", True):
                return upload_response(
                    request, msg="Feature not available", err=True, stat=404
                )
            logger.info(
                f"Base-64 image upload detected, content length: {len(content)} bytes"
            )

            # Security hardening: Check size before decode
            max_base64_size = getattr(settings, "DEPO_MAX_BASE64_SIZE", 8 * 1024 * 1024)
            if len(content) > max_base64_size:
                logger.warning(
                    f"Base-64 upload rejected: size {len(content)} exceeds limit {max_base64_size}"
                )
                return upload_response(
                    request, msg="Image too large", err=True, stat=400
                )

            try:
                uploaded_file = convert_base64_to_file(content)
                # Inject the file into request.FILES with the expected key
                request.FILES["content"] = uploaded_file
                # Log successful clipboard image save per spec
                logger.info(
                    '{"event":"clipboard_image_saved","bytes":%d}', uploaded_file.size
                )
            except ValueError as e:
                # Log malformed base-64 error per spec
                if "Invalid base-64 data" in str(e):
                    logger.warning('{"event":"clipboard_image_error","reason":"DecodeError"}')
                else:
                    logger.warning('{"event":"clipboard_image_error","reason":"ValidationError"}')
                return upload_response(
                    request, msg=f"Invalid image data: {e}", err=True, stat=400
                )

        # Classify content type for analytics/routing
        content_type = classify_type(request)
        # Store classification for potential future use
        request.content_classification = content_type

        return upload_view_post(request)
    return upload_response(f"Method ({method}) not allowed", err=True, stat=405)


# TODO: Consider separating out API & Web Views to own graphs of modules/urls
# TODO: Test in isolation, have calling view mock test this func
# TODO: Move headers out to separate module, standardize & document
# TODO: Status should be a positional arg
def upload_response(req, msg=None, err=False, fname=None, stat=200):
    """
    Renders an HTML template to show the result of an upload.
    """
    context = {
        "message": msg,
        "error": err,
        "filename": fname,
        "shortcode": fname.split(".")[0] if fname else None,
        "accept_exts": ACCEPT_EXTS,
    }
    # Note: This now renders the result using an HTML template instead of plain text.
    return render(req, "upload.html", context, status=stat)
