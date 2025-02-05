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
        return HttpResponse("Method not allowed", status=405)

    # POST case
    pic_file = request.FILES.get("image")
    if pic_file:
        file_data = pic_file.read()
        if file_data == "" or file_data == b"" or file_data is None:
            return HttpResponse("Empty file uploaded", status=400)

        pic_type = validate_upload_bytes(file_data)
        if not pic_type:
            return HttpResponse("File type not allowed", status=400)

        pic_item = PicItem.ensure(file_data)  # Ensure PicItem
        filename = f"{pic_item.item.code}.{pic_item.format}"
        try:
            with open(settings.UPLOAD_DIR / filename, "wb") as f:
                f.write(file_data)  # Write uploaded pic file to disk
        except Exception as e:
            return HttpResponse(f"Error saving file: {str(e)}", status=500)
        return HttpResponse(f"Uploaded file {filename} successfully!", status=200)

    # No file uploaded
    return HttpResponse("No file uploaded", status=400)
