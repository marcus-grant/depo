from django.http import HttpResponse


def raw_download_view(request, shortcode):
    return HttpResponse(b"raw_download")