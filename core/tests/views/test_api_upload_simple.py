"""Simple focused test for API upload endpoint"""

from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from pathlib import Path
from core.models.item import Item
from core.models.pic import PicItem

# Test data - minimal valid image files
PNG_DATA = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x00\x01\x00\x00\x00\x00IEND\xaeB`\x82"
JPEG_DATA = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04\x04\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05\x12!1A\x06\x13Qa\x07\"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R\xd1\xf0$3br\x82\t\n\x16\x17\x18\x19\x1a%&'()*456789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xfb\xd5N\xe1\x18\xd2I\xfd\xd7\xc7&\xff\xd9"


class SimpleAPIUploadTest(TestCase):
    """Test basic API upload functionality"""

    def setUp(self):
        self.client = Client()
        self.url = reverse("api_upload")  # /api/upload/
        self.user = User.objects.create_user(username="test", password="test")
        self.client.force_login(self.user)

    def test_png_upload(self):
        """Test uploading a PNG file via API"""
        file = SimpleUploadedFile("test.png", PNG_DATA, content_type="image/png")

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
        file = SimpleUploadedFile("photo.jpg", JPEG_DATA, content_type="image/jpeg")

        response = self.client.post(self.url, {"content": file})

        self.assertEqual(response.status_code, 200)
        self.assertIn(b".jpg", response.content)
        self.assertEqual(response["X-Format"], "jpg")

    def test_no_file_returns_error(self):
        """Test that missing file returns 400 error"""
        response = self.client.post(self.url, {})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, b"No file uploaded")


@override_settings(UPLOAD_DIR=settings.BASE_DIR / "test_uploads_e2e")
class APIUploadE2ETest(TestCase):
    """Test end-to-end upload flow including file persistence"""
    
    def setUp(self):
        self.client = Client()
        self.url = reverse("api_upload")
        self.user = User.objects.create_user(username="test", password="test")
        self.client.force_login(self.user)
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(exist_ok=True)
        
        # Verify settings override is working
        expected_dir = settings.BASE_DIR / "test_uploads_e2e"
        self.assertEqual(self.upload_dir, expected_dir, f"Settings override failed: {self.upload_dir} != {expected_dir}")
    
    def tearDown(self):
        """Clean up test files"""
        if self.upload_dir.exists():
            for file in self.upload_dir.iterdir():
                file.unlink()
            self.upload_dir.rmdir()
    
    def test_file_saved_to_disk(self):
        """Test that uploaded file is actually saved to disk"""
        file = SimpleUploadedFile("test.png", PNG_DATA, content_type="image/png")
        
        response = self.client.post(self.url, {"content": file})
        
        self.assertEqual(response.status_code, 200)
        
        # Extract filename from response
        filename = response.content.decode('utf-8')
        file_path = self.upload_dir / filename
        
        # Verify file exists
        self.assertTrue(file_path.exists())
        
        # Verify file content matches
        with open(file_path, 'rb') as f:
            saved_data = f.read()
        self.assertEqual(saved_data, PNG_DATA)

