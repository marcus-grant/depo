"""Simple focused test for API upload endpoint"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile


class SimpleAPIUploadTest(TestCase):
    """Test basic API upload functionality"""

    def setUp(self):
        self.client = Client()
        self.url = reverse("api_upload")  # /api/upload/
        self.user = User.objects.create_user(username="test", password="test")
        self.client.force_login(self.user)

    def test_png_upload(self):
        """Test uploading a PNG file via API"""
        # Minimal PNG file
        png_data = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x00\x01\x00\x00\x00\x00IEND\xaeB`\x82"
        file = SimpleUploadedFile("test.png", png_data, content_type="image/png")

        response = self.client.post(self.url, {"content": file})

        # API returns plain text with filename
        self.assertEqual(response.status_code, 200)
        self.assertIn(b".png", response.content)
        # Check headers
        self.assertIn("X-Code", response)
        self.assertIn("X-Format", response)
        self.assertEqual(response["X-Format"], "png")

    def test_jpeg_upload(self):
        """Test uploading a JPEG file via API"""
        # Minimal JPEG (1x1 pixel)
        jpeg_data = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04\x04\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05\x12!1A\x06\x13Qa\x07\"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R\xd1\xf0$3br\x82\t\n\x16\x17\x18\x19\x1a%&'()*456789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xfb\xd5N\xe1\x18\xd2I\xfd\xd7\xc7&\xff\xd9"
        file = SimpleUploadedFile("photo.jpg", jpeg_data, content_type="image/jpeg")

        response = self.client.post(self.url, {"content": file})

        self.assertEqual(response.status_code, 200)
        self.assertIn(b".jpg", response.content)
        self.assertEqual(response["X-Format"], "jpg")

    def test_no_file_returns_error(self):
        """Test that missing file returns 400 error"""
        response = self.client.post(self.url, {})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, b"No file uploaded")

