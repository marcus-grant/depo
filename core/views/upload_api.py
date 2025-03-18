# core/views/upload_api.py
# TODO: Differentiate between PicItem & LinkItem
# TODO: Log all potential outcomes of this view
from pathlib import Path

from django.conf import settings
from rest_framework.views import APIView
from rest_framework.renderers import BaseRenderer
from rest_framework.response import Response
from rest_framework import status

from core.models.pic import PicItem


class PlainTextRenderer(BaseRenderer):
    media_type = "text/plain"
    format = "txt"
    charset = "utf-8"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        if isinstance(data, bytes):
            return data.decode(self.charset)
        return str(data)


class UploadAPIView(APIView):
    renderer_classes = [PlainTextRenderer]
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        uploaded_file = request.FILES.get("content")
        # Check for both no file provided and empty file using size property.
        if not uploaded_file or uploaded_file.size == 0:
            return Response("No file uploaded", status=status.HTTP_400_BAD_REQUEST)

        # Now it is safe to read the file.
        file_bytes = uploaded_file.read()

        try:
            picitem = PicItem.ensure(file_bytes)
        except Exception:
            return Response(
                "Error processing file", status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        filename = f"{picitem.item.code}.{picitem.format}"
        response = Response(filename, status=status.HTTP_200_OK)
        response["X-Code"] = picitem.item.code
        response["X-Format"] = picitem.format
        return response

