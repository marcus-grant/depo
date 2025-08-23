"""Simple focused test for API upload endpoint"""

from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from pathlib import Path
from core.models.item import Item
from core.models.pic import PicItem
from core.tests.fixtures import PNG_DATA, JPEG_DATA


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
        self.assertEqual(
            self.upload_dir,
            expected_dir,
            f"Settings override failed: {self.upload_dir} != {expected_dir}",
        )

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
        filename = response.content.decode("utf-8")
        file_path = self.upload_dir / filename

        # Verify file exists
        self.assertTrue(file_path.exists())

        # Verify file content matches
        with open(file_path, "rb") as f:
            saved_data = f.read()
        self.assertEqual(saved_data, PNG_DATA)
