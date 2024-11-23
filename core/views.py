from django.shortcuts import render
from django.http import HttpRequest, HttpResponseBadRequest  # , Http404
from django.template.loader import render_to_string

from core.models import Item
# from core.shortcode import hash_b32, SHORTCODE_MIN_LEN


# TODO: Properly handle 404s with context containing shortcode
# def handler_404(request, exception=None):
#     ctx = {"shortcode": request.GET.get("shortcode", "unknown")}
#     return render(request, "404.html", ctx, status=404)


# Create your views here.
def web_index(req: HttpRequest):
    if req.method == "POST":
        content = req.POST.get("content")
        if not content:
            props = {"error": "Content is required"}
            return HttpResponseBadRequest(render(req, "index.html", props))
        try:
            item = Item.ensure(content)
        except Exception as e:
            return render(req, "index.html", {"error": e})
        # TODO: Implement created and error
        return render(req, "index.html", {"item": item})
    else:
        return render(req, "index.html")


def shortcode_details(request, shortcode: str):
    item = Item.search_shortcode(shortcode)
    # TODO: Figure out how to handle custom 404s
    # if not item:
    #     raise Http404
    ctx = {"item": item}
    return render(request, "shortcode-details.html", ctx)
