# core/views/index.py
import logging

from django.http import HttpRequest, HttpResponseBadRequest
from django.shortcuts import render

from core.models.link import LinkItem

# TODO: Standardize name in settings & make sure program name used
logger = logging.getLogger("depo." + __name__)

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
