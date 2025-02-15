import logging
import os
import time
from typing import Optional

from django.conf import settings
from django.shortcuts import render
from django.http import HttpRequest, HttpResponseBadRequest, HttpResponse  # , Http404

from core.models import Item
from core.user.models import jwt_required
from core.link.models import LinkItem
from core.pic.models import PicItem

# TODO: Standardize name in settings & make sure program name used
logger = logging.getLogger("depo." + __name__)

# TODO: Read picture byte stream as chunks instead
# TODO: Properly handle 404s with context containing shortcode
# def handler_404(request, exception=None):
#     ctx = {"shortcode": request.GET.get("shortcode", "unknown")}
#     return render(request, "404.html", ctx, status=404)
# TODO: Figure out how to handle custom 404s in all major views
# if not item:
#     raise Http404
# TODO: Centralize all error messages with documented messages/codes
# TODO: Add logging
# TODO: Add file read streaming to reduce RAM usage
# Also test this properly with gigabyte or larger mock files
# TODO: Ensure end to end testing exists see TDD cycles 8, 9 and 10


# TODO: Split into separate functions
def web_index(req: HttpRequest):
    if req.method == "POST":
        content = req.POST.get("content")
        if not content:
            props = {"error": "Content is required"}
            return HttpResponseBadRequest(render(req, "index.html", props))
        try:
            link = LinkItem.ensure(content)
            item = link.item
        except Exception as e:
            return render(req, "index.html", {"error": e})
        # TODO: Implement created and error
        return render(req, "index.html", {"item": item})
    else:
        return render(req, "index.html")


def shortcode_details(request, shortcode: str):
    item = Item.search_shortcode(shortcode)
    if not item:
        raise ValueError(f"Item with shortcode '{shortcode}' not found.")
    # TODO: Change to handle new context methods
    # TODO: Fix get_child and maybe consider having subitems handle search themselves
    link = item.get_child()
    ctx = link.context()
    return render(request, "shortcode-details.html", ctx)


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
@jwt_required
def upload_view_post(request):
    time_start = time.time()
    logger.info("Upload initiated")
    pic_file = request.FILES.get("content")
    if not pic_file:
        return upload_response("No file uploaded", stat=400)

    file_data = pic_file.read()
    if file_data == "" or file_data == b"" or file_data is None:
        logger.error("Empty file uploaded")
        return upload_response("Empty file uploaded", err=True, stat=400)

    if len(file_data) > settings.MAX_UPLOAD_SIZE:
        msg = f"File size {len(file_data)} exceeds limit of {settings.MAX_UPLOAD_SIZE} bytes"
        logger.error(msg)
        return upload_response(msg, err=True, stat=400)

    pic_type = validate_upload_bytes(file_data)
    if not pic_type:
        msg = "Invalid or unknown filetype, not allowed"
        logger.error(msg)
        return upload_response(msg, err=True, stat=400)

    pic_item = PicItem.ensure(file_data)  # Ensure PicItem
    filename = f"{pic_item.item.code}.{pic_item.format}"
    try:
        with open(settings.UPLOAD_DIR / filename, "wb") as f:
            f.write(file_data)  # Write uploaded pic file to disk
    except OSError as e:
        msg = "Error during upload file save"
        logger.error(f"{msg}: {e}")
        return upload_response(msg, err=True, stat=500, filename=filename)

    time_elapsed = time.time() - time_start
    logger.info(f"Upload completed: {filename} in {time_elapsed:.2f}seconds")
    msg = f"Uploaded file {filename} successfully!"
    return upload_response(msg, stat=200, filename=filename)


# TODO: Handle pasting an image/binary data into textbox from clipboard
def upload_view(request):
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
def upload_response(msg, stat, err=False, filename=None):
    """
    Returns a plain text HttpResponse and, if the client accepts plain text,
    attaches additional headers with details.
    """
    resp = HttpResponse(msg, status=stat, content_type="text/plain")
    if filename:
        resp["X-Uploaded-Filename"] = filename
    if err:
        resp["X-Error"] = "true"
    return resp
