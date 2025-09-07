# core/views/upload.py
import logging
import time

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from core.services.upload import handle_file_upload
from core.util.content import classify_type, convert_base64_to_file

logger = logging.getLogger("depo." + __name__)

# TODO: Read picture byte stream as chunks instead

# TODO: Reference theses constant messages in the response function
ACCEPT_EXTS = ".jpg,.jpeg,.png,.gif"
MSG_EMPTY = "Empty file uploaded"
MSG_INVALID = "Invalid or unknown filetype, not allowed"

# Error message mapping for upload results
ERROR_MESSAGES = {
    "empty_file": MSG_EMPTY,
    "file_too_big": lambda size: f"File size {size} exceeds limit of {settings.MAX_UPLOAD_SIZE} bytes",
    "invalid_file_type": MSG_INVALID,
    "storage_error": "Error during upload file save",
}


@login_required
def upload_view_post(req):
    time_start = time.time()
    logger.info("Upload initiated")
    pic_file = req.FILES.get("content")

    if not pic_file:
        return upload_response(req, msg="No file uploaded", err=True, stat=400)

    file_data = pic_file.read()
    result = handle_file_upload(file_data)

    if not result.success:
        # Get appropriate error message
        msg_func = ERROR_MESSAGES.get(result.error_type, "Upload failed")
        msg = msg_func(len(file_data)) if callable(msg_func) else msg_func
        status = 500 if result.error_type == "storage_error" else 400
        
        logger.error(msg)
        messages.error(req, msg)
        return upload_response(req, msg=msg, err=True, stat=status)

    time_elapsed = time.time() - time_start
    fname = result.item.filename
    logger.info(f"Upload completed: {fname} in {time_elapsed:.2f}seconds")
    msg = f"Uploaded file {fname} successfully!"
    return upload_response(req, msg=msg, stat=200, fname=fname)


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
                    logger.warning(
                        '{"event":"clipboard_image_error","reason":"DecodeError"}'
                    )
                else:
                    logger.warning(
                        '{"event":"clipboard_image_error","reason":"ValidationError"}'
                    )
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
