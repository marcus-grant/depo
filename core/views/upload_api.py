# core/views/upload_api.py
# TODO: Differentiate between PicItem & LinkItem
# TODO: Log all potential outcomes of this view
from pathlib import Path

from django.conf import settings
from rest_framework.views import APIView
from rest_framework.renderers import BaseRenderer
from rest_framework.response import Response
from rest_framework import status

from core.models.item import Item
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
        if not uploaded_file or uploaded_file.size == 0:
            return Response("No file uploaded", status=status.HTTP_400_BAD_REQUEST)

        file_bytes = uploaded_file.read()
        try:
            picitem = PicItem.ensure(file_bytes)
        except Exception:
            stat = status.HTTP_500_INTERNAL_SERVER_ERROR
            return Response("Invalid upload format", status=stat)

        filename = f"{picitem.item.code}.{picitem.format}"
        filepath = settings.UPLOAD_DIR / filename

        # If no duplicate Items were hashed, save the file
        response = Response(filename, status=status.HTTP_200_OK)
        response["X-Code"] = picitem.item.code
        response["X-Format"] = picitem.format
        if filepath.exists():
            response["X-Duplicate"] = "true"
        else:
            try:
                settings.UPLOAD_DIR.mkdir(exist_ok=True)
                with open(filepath, "wb") as f:
                    f.write(file_bytes)
            except Exception as e:
                stat = status.HTTP_500_INTERNAL_SERVER_ERROR
                return Response(f"Error saving file: {e}", status=stat)
        return response
