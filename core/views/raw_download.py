from django.http import HttpResponse, Http404
from django.conf import settings
from pathlib import Path
from core.models import Item, PicItem


def raw_download_view(request, shortcode_with_ext):
    # Parse shortcode and extension
    if "." in shortcode_with_ext:
        shortcode, ext = shortcode_with_ext.rsplit(".", 1)
    else:
        shortcode = shortcode_with_ext
        ext = None

    # Check if shortcode exists
    try:
        item = Item.objects.get(code=shortcode)
    except Item.DoesNotExist:
        raise Http404("Shortcode not found")

    # Get PicItem to determine format
    try:
        pic_item = PicItem.objects.get(item=item)
    except PicItem.DoesNotExist:
        raise Http404("File not found")

    # Read file from disk
    file_path = Path(settings.UPLOAD_DIR) / f"{item.code}.{pic_item.format}"
    if not file_path.exists():
        raise Http404("File not found on disk")

    with open(file_path, "rb") as f:
        content = f.read()

    return HttpResponse(content)

