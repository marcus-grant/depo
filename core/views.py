from django.conf import settings
from django.shortcuts import render
from django.http import HttpRequest, HttpResponseBadRequest, HttpResponse  # , Http404
from django.template.loader import render_to_string

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


def upload_view(request):
    if request.method == "POST":
        pic_file = request.FILES.get("image")
        if pic_file:
            pic_item = PicItem.ensure(pic_file.read())  # Ensure PicItem
            filename = f"{pic_item.item.code}.{pic_item.format}"
            with open(settings.UPLOAD_DIR / filename, "wb") as f:
                f.write(pic_file.read())  # Write uploaded pic file to disk
            return HttpResponse(f"Uploaded file {filename} successfully!", status=200)
        return HttpResponse("No file uploaded", status=400)

    # Failure case
    return render(request, "upload.html")
