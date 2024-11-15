from django.shortcuts import render

from core.models import Shortcode, ShortcodeManager
from core.shortcode import hash_b32, SHORTCODE_MIN_LEN


# Create your views here.
def web_index(request):
    if request.method == "POST":
        try:
            content = request.POST.get("content")
            shortcode, short_id = ShortcodeManager.gen_shortcode(content)
        except Exception as e:
            return render(request, "index.html", {"error": e})
        # TODO: Implement created and error
        return render(
            request, "index.html", {"shortcode": shortcode, "short_id": short_id}
        )
    else:
        return render(request, "index.html")


def shortcode_details(request, shortcode):
    # TODO: Implement too short shortcode
    # if len(shortcode) < SHORTCODE_MIN_LEN:
    #     return render(request)
    try:
        item = Shortcode.objects.get(id=shortcode)
    except Shortcode.DoesNotExist:
        return render(request, "404.html", {"shortcode": shortcode})
    return render(request, "shortcode-detail.html", {"item": item})
