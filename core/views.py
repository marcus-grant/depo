from django.shortcuts import render
from django.http import HttpRequest

from core.models import Shortcode
# from core.shortcode import hash_b32, SHORTCODE_MIN_LEN


# Create your views here.
def web_index(req: HttpRequest):
    if req.method == "POST":
        try:
            content = req.POST.get("content")
            shortcode = Shortcode.generate(content)
        except Exception as e:
            return render(req, "index.html", {"error": e})
        # TODO: Implement created and error
        return render(req, "index.html", {"shortcode": shortcode})
    else:
        return render(req, "index.html")


def shortcode_details(request, short_id: str):
    # TODO: Implement too short shortcode
    # if len(shortcode) < SHORTCODE_MIN_LEN:
    #     return render(request)
    try:
        shortcode = Shortcode.lookup_shortcode(short_id)
    except Exception as e:
        return render(request, "404.html", {"short_id": short_id, "error": e})
    return render(request, "shortcode-details.html", {"shortcode": shortcode})
