# core/tests/views/test_upload_api.py
from django.conf import settings
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
import logging
from pathlib import Path
from rest_framework.test import APITestCase
from unittest.mock import MagicMock, patch


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

    def mock_picfile(self, fname, fcontent):
        """Helper to create a SimpleUploadedFile with an appropriate content type based on extension."""
        fname_lower = fname.lower()
        ctype = ""
        if fname_lower.endswith((".jpg", ".jpeg")):
            ctype = "image/jpeg"
        elif fname_lower.endswith(".png"):
            ctype = "image/png"
        elif fname_lower.endswith(".gif"):
            ctype = "image/gif"
        else:
            ctype = "application/octet-stream"
        return SimpleUploadedFile(fname, fcontent, content_type=ctype)

    def pic_mock(self, code="DUMYHASH", fmt="png", size=0):
        """Create a dummy MagicMock object simulating a PicItem.ensure return value."""
        dummy = MagicMock()
        dummy.item.code = code
        dummy.format = fmt
        dummy.size = size
        return dummy

    def client_file_upload(self, content):
        """Helper to perform file upload to API endpoint."""
        return self.client.post(self.url, {"content": content}, format="multipart")

    def test_temp_upload_dir(self):
        """Ensure temp upload directory exists."""
        self.assertTrue(self.upload_dir.exists())

    def test_get_request_returns_405(self):
        """Ensure 405 from get request to API upload view."""
        self.assertEqual(self.client.get(self.url).status_code, 405)

    def test_put_request_returns_405(self):
        """Ensure 405 from put request to API upload view."""
        self.assertEqual(self.client.put(self.url, {}).status_code, 405)

    def test_delete_request_returns_405(self):
        """Ensure 405 from delete request to API upload view."""
        self.assertEqual(self.client.delete(self.url).status_code, 405)

    @patch("core.models.pic.PicItem.ensure")
    def test_ensure_called_with_file_content(self, mock_ensure):
        """Verify that PicItem.ensure is called with the exact file content uploaded and the response carries details in headers and body text."""
        picitem = self.pic_mock()
        mock_ensure.return_value = picitem
        upload_file = self.mock_picfile("dummy.png", b"\x89PNG\r\n\x1a\n")
        resp = self.client_file_upload(upload_file)

        # Verify ensure was called with the file content.
        mock_ensure.assert_called_once_with(b"\x89PNG\r\n\x1a\n")

        # Verify that the response is successful and non-JSON.
        self.assertEqual(resp.status_code, 200)
        # Expect headers to include model details.
        self.assertEqual(resp.get("X-Code"), picitem.item.code)
        self.assertEqual(resp.get("X-Format"), picitem.format)
        # Check body text includes the details.
        content = resp.content.decode()
        self.assertEqual(content, f"{picitem.item.code}.{picitem.format}")

    @patch("core.models.pic.PicItem.ensure")
    def test_error_processing_file(self, mock_ensure):
        """Verify that if an exception occurs during file processing, a 500 error is returned."""
        # Force PicItem.ensure to raise an Exception.
        mock_ensure.side_effect = Exception("Processing error")
        upload_file = self.mock_picfile("dummy.png", b"\x89PNG\r\n\x1a\n")
        resp = self.client_file_upload(upload_file)

        self.assertEqual(resp.status_code, 500)
        self.assertEqual(resp.content.decode(), "Error processing file")
