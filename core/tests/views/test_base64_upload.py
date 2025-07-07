"""Test base64 image upload functionality"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User


class Base64UploadTest(TestCase):
    """Test that base64 images can be uploaded via web endpoint"""
    
    def setUp(self):
        self.client = Client()
        self.url = reverse("web_upload")
        self.user = User.objects.create_user(username="test", password="test")
        self.client.login(username="test", password="test")
    
    def test_base64_png_upload(self):
        """Test uploading a base64 PNG data URI"""
        # Tiny 1x1 red pixel PNG
        base64_png = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        
        response = self.client.post(self.url, {"content": base64_png})
        
        # Should return 200 with success message
        self.assertEqual(response.status_code, 200)
        self.assertIn(b".png", response.content)  # PNG file was created
        self.assertNotIn(b"error", response.content.lower())  # No errors