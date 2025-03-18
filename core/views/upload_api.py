# core/views/upload_api.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class UploadAPIView(APIView):
    http_method_names = ["post"]
