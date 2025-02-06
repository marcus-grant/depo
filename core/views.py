from django.conf import settings
from django.shortcuts import render
from django.http import HttpRequest, HttpResponseBadRequest, HttpResponse  # , Http404
from django.template.loader import render_to_string
from typing import Optional

from core.models import Item
from core.link.models import LinkItem
from core.pic.models import PicItem


# TODO: Read picture byte stream as chunks instead
# TODO: Properly handle 404s with context containing shortcode
# def handler_404(request, exception=None):
#     ctx = {"shortcode": request.GET.get("shortcode", "unknown")}
#     return render(request, "404.html", ctx, status=404)
# TODO: Figure out how to handle custom 404s in all major views
# if not item:
#     raise Http404
# TODO: Centralize all error messages with documented messages/codes


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
def validate_upload_bytes(upload_bytes: bytes) -> Optional[str]:
    if b"\xff\xd8\xff" in upload_bytes:
        return "jpg"
    if b"\x89PNG\r\n\x1a\n" in upload_bytes:
        return "png"
    if b"GIF89a" in upload_bytes or b"GIF87a" in upload_bytes:
        return "gif"
    return None


def upload_view(request):
    if request.method == "GET":
        return render(request, "upload.html")  # GET case

    if request.method != "POST":  # Neither GET nor POST case, bad method
        return upload_response("Method not allowed", err=True, stat=405)

    # POST case
    pic_file = request.FILES.get("image")
    if pic_file:
        file_data = pic_file.read()
        if file_data == "" or file_data == b"" or file_data is None:
            return upload_response("Empty file uploaded", err=True, stat=400)

        pic_type = validate_upload_bytes(file_data)
        if not pic_type:
            return upload_response("File type not allowed", err=True, stat=400)

        pic_item = PicItem.ensure(file_data)  # Ensure PicItem
        # TODO: Once ctype/format handling extracted, move file saving with it
        filename = f"{pic_item.item.code}.{pic_item.format}"
        try:
            with open(settings.UPLOAD_DIR / filename, "wb") as f:
                f.write(file_data)  # Write uploaded pic file to disk
        except Exception as e:
<<<<<<< HEAD
            msg = "Error saving file"
            return upload_response(msg, err=True, stat=500, filename=filename)

        msg = f"Uploaded file {filename} successfully!"
        return upload_response(msg, stat=200, filename=filename)
=======
            return HttpResponse(f"Error saving file: {str(e)}", status=500)
        return HttpResponse(f"Uploaded file {filename} successfully!", status=200)
>>>>>>> e239dce06cb08d131230acafee3c9cc4a2a69b12

    # No file uploaded
    return upload_response("No file uploaded", stat=400)


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
