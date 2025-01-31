from django.shortcuts import render
from django.http import HttpRequest, HttpResponseBadRequest  # , Http404
from django.template.loader import render_to_string

from core.models import Item
from core.link.models import LinkItem


# TODO: Properly handle 404s with context containing shortcode
# def handler_404(request, exception=None):
#     ctx = {"shortcode": request.GET.get("shortcode", "unknown")}
#     return render(request, "404.html", ctx, status=404)


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
    # TODO: Figure out how to handle custom 404s
    # if not item:
    #     raise Http404
    # TODO: Change to handle new context methods
    # TODO: Fix get_child and maybe consider having subitems handle search themselves
    link = item.get_child()
    ctx = link.context()
    return render(request, "shortcode-details.html", ctx)


def upload_view(request):
    return render(request, "upload.html")
