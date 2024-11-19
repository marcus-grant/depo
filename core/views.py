from django.shortcuts import render
from django.http import HttpRequest, HttpResponseBadRequest

from core.models import Item
# from core.shortcode import hash_b32, SHORTCODE_MIN_LEN


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
    # TODO: Implement too short shortcode
    # if len(shortcode) < SHORTCODE_MIN_LEN:
    #     return render(request)
    try:
        item = Item.lookup_shortcode_item(shortcode)
    except Exception as e:
        props = {"shortcode": shortcode, "error": e}
        return render(request, "404.html", props)
    props = {"shortcode": shortcode, "item": item}
    return render(request, "shortcode-details.html", props)
