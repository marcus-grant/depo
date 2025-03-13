# core/views/upload.py
import logging
import time
from typing import Optional

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render

from core.models.pic import PicItem

logger = logging.getLogger("depo." + __name__)

# TODO: Read picture byte stream as chunks instead

# TODO: Reference theses constant messages in the response function
ACCEPT_EXTS = ".jpg,.jpeg,.png,.gif"
MSG_EXIST = "File already exists"
MSG_EMPTY = "Empty file uploaded"
MSG_INVALID = "Invalid or unknown filetype, not allowed"


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
@login_required
def upload_view_post(req):
    time_start = time.time()
    logger.info("Upload initiated")
    pic_file = req.FILES.get("content")
    if not pic_file:
        return upload_response(req, msg="No file uploaded", err=True, stat=400)

    file_data = pic_file.read()
    if file_data == "" or file_data == b"" or file_data is None:
        logger.error("Empty file uploaded")
        return upload_response(req, msg="Empty file uploaded", err=True, stat=400)

    if len(file_data) > settings.MAX_UPLOAD_SIZE:
        msg = f"File size {len(file_data)}"
        msg += f" exceeds limit of {settings.MAX_UPLOAD_SIZE} bytes"
        logger.error(msg)
        return upload_response(req, msg=msg, err=True, stat=400)

    pic_type = validate_upload_bytes(file_data)
    if not pic_type:
        msg = "Invalid or unknown filetype, not allowed"
        logger.error(msg)
        return upload_response(req, msg=msg, err=True, stat=400)

    pic_item = PicItem.ensure(file_data)  # Ensure PicItem
    fname = f"{pic_item.item.code}.{pic_item.format}"
    fpath = settings.UPLOAD_DIR / fname
    if fpath.exists():
        return upload_response(req, msg="File already exists", fname=fname, stat=409)
    try:
        with open(fpath, "wb") as f:
            f.write(file_data)  # Write uploaded pic file to disk
    except OSError as e:
        msg = "Error during upload file save"
        logger.error(f"{msg}: {e}")
        return upload_response(req, msg=msg, err=True, stat=500, fname=fname)

    time_elapsed = time.time() - time_start
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
