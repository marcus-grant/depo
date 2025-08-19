"""Test base64 image upload functionality"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from core.tests.fixtures import PNG_BASE64_DATA_URI


class Base64UploadTest(TestCase):
    """Test that base64 images can be uploaded via web endpoint"""

    def setUp(self):
        self.client = Client()
        self.url = reverse("web_upload")
        self.user = User.objects.create_user(username="test", password="test")
        self.client.login(username="test", password="test")

    def test_base64_png_upload(self):
        """Test uploading a base64 PNG data URI"""
        response = self.client.post(self.url, {"content": PNG_BASE64_DATA_URI})

        # Should return 200 with success message
        self.assertEqual(response.status_code, 200)
        self.assertIn(b".png", response.content)  # PNG file was created
        self.assertNotIn(b"error", response.content.lower())  # No errors

