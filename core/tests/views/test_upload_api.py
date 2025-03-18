# core/tests/views/test_upload_api.py
from django.conf import settings
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from pathlib import Path
from rest_framework.test import APITestCase
import logging


class UploadAPITest(TestCase):
    @override_settings(UPLOAD_ROOT=Path("uploads"))
    def setUp(self):
        self.client = Client()
        self.url = reverse("api_upload")  # match 'name' in urls.py
        self.upload_dir = Path(settings.UPLOAD_ROOT)
        self.upload_dir.mkdir(exist_ok=True)
        # Suppress "Method Not Allowed" logging messages during tests
        logging.getLogger("django.request").setLevel(logging.CRITICAL)

    def tearDown(self):
        # Clean-up temporary upload directory
        if self.upload_dir.exists():
            for file in self.upload_dir.iterdir():
                if file.is_file():
                    file.unlink()
                elif file.is_dir():
                    file.rmdir()
            self.upload_dir.rmdir

    def test_temp_upload_dir(self):
        """Ensure temp upload directory exists."""
        self.assertTrue(self.upload_dir.exists())

    def test_post_request_returns_200(self):
        """Ensure 200 from post request to API upload view."""
        self.assertEqual(self.client.post(self.url).status_code, 200)

    def test_get_request_returns_405(self):
        """Ensure 405 from get request to API upload view."""
        self.assertEqual(self.client.get(self.url).status_code, 405)

    def test_put_request_returns_405(self):
        """Ensure 405 from put request to API upload view."""
        self.assertEqual(self.client.put(self.url, {}).status_code, 405)

    def test_delete_request_returns_405(self):
        """Ensure 405 from delete request to API upload view."""
        self.assertEqual(self.client.delete(self.url).status_code, 405)
