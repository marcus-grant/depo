# core/views/upload_api.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class UploadAPIView(APIView):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        return Response({"message": "Upload successful"}, status=status.HTTP_200_OK)
