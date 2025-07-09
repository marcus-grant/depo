from django.http import HttpResponse, Http404
from core.models import Item


def raw_download_view(request, shortcode_with_ext):
    # Parse shortcode and extension
    if '.' in shortcode_with_ext:
        shortcode, ext = shortcode_with_ext.rsplit('.', 1)
    else:
        shortcode = shortcode_with_ext
        ext = None
    
    # Check if shortcode exists
    try:
        item = Item.objects.get(code=shortcode)
    except Item.DoesNotExist:
        raise Http404("Shortcode not found")
    
    return HttpResponse(b"raw_download")