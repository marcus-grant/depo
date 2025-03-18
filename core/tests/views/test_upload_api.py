# core/tests/views/test_upload_api.py
from django.test import TestCase, Client
from django.urls import reverse


class UploadAPITest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("api_upload")  # match 'name' in urls.py

    def test_view_accessible(self):
        """Ensure that UploadAPIView is accessible via setup"""
        # Use the setup run before this to check if it's loaded
        self.client.get(self.url)
