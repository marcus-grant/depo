# core/tests/views/test_upload_api.py
from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
import logging
from pathlib import Path
from unittest.mock import MagicMock, patch


# TODO: Offload filesaving to submodule, simplifying testing to mocks
class UploadAPITest(TestCase):
    @override_settings(UPLOAD_DIR=settings.BASE_DIR / "testupload")
    def setUp(self):
        self.client = Client()
        self.url = reverse("api_upload")  # match 'name' in urls.py
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(exist_ok=True)
        self.user = User.objects.create_user(username="tester", password="pass")
        self.client.force_login(self.user)
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

    def test_unauthenticated_401_response(self):
        self.client.logout()
        resp = self.client.post(self.url)
        self.assertEqual(self.client.post(self.url).status_code, 401)
        self.assertIn("X-Error", resp.headers)
        self.assertEqual(resp.get("X-Error"), "Unauthorized")
        self.assertEqual(resp.content, b"Unauthorized, need to authenticate request")

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
        self.assertEqual(resp.content.decode(), "Invalid upload format")

    @patch("core.models.pic.PicItem.ensure")
    def test_empty_file_upload(self, mock_ensure):
        """Verify that uploading an empty file returns a 400 error and
        does not call PicItem.ensure."""
        upload_file = self.mock_picfile("empty.png", b"")
        resp = self.client_file_upload(upload_file)
        # Verify that PicItem.ensure was not called.
        mock_ensure.assert_not_called()
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content.decode(), "No file uploaded")

    @patch("core.models.pic.PicItem.ensure")
    def test_no_file_upload(self, mock_ensure):
        """No file upload should provided should have same effect as empty file."""
        resp = self.client.post(self.url)
        mock_ensure.assert_not_called()
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content.decode(), "No file uploaded")

    @override_settings(UPLOAD_DIR=settings.BASE_DIR / "testupload")
    @patch("core.models.pic.PicItem.ensure")
    def test_valid_file_upload(self, mock_ensure):
        """Verify a valid file upload returns a 200 response with
        proper details and correctly saved file with expected contents."""
        # Create a dummy PicItem return value.
        expected_pic = self.pic_mock(code="VALID123", fmt="png", size=1024)
        mock_ensure.return_value = expected_pic
        testpath = settings.BASE_DIR / "testupload"

        # Create a valid file upload.
        valid_file = self.mock_picfile("valid.png", b"somecontent")
        resp = self.client_file_upload(valid_file)
        filename = f"{expected_pic.item.code}.{expected_pic.format}"
        filepath = testpath / filename

        # Verify PicItem.ensure was called and expected filename & content saved
        mock_ensure.assert_called_once_with(b"somecontent")
        self.assertTrue(filepath.exists(), "Test file wasn't saved")
        self.assertEqual(filepath.read_bytes(), b"somecontent")

        # Check that the response is correct.
        self.assertEqual(resp.status_code, 200)
        expected_filename = f"{expected_pic.item.code}.{expected_pic.format}"
        self.assertEqual(resp.content.decode(), expected_filename)
        self.assertEqual(resp.get("X-Code"), expected_pic.item.code)
        self.assertEqual(resp.get("X-Format"), expected_pic.format)

    @patch("core.models.pic.PicItem.ensure")
    @patch("builtins.open", side_effect=Exception("Filesystem error"))
    def test_filesystem_error_during_save(self, mock_open, mock_ensure):
        """Simulate a filesystem error during file save and verify a 500 error response."""
        # Set up a dummy PicItem return value.
        expected_pic = self.pic_mock(code="FAIL123", fmt="png", size=1024)
        mock_ensure.return_value = expected_pic

        # Create a valid file upload.
        file_content = b"valid file content"
        valid_file = self.mock_picfile("valid.png", file_content)
        resp = self.client_file_upload(valid_file)

        # Verify that open was attempted and raised an exception.
        mock_open.assert_called()

        # Verify that we returned a 500 error.
        self.assertEqual(resp.status_code, 500)
        self.assertEqual(resp.content.decode(), "Error saving file: Filesystem error")

    @override_settings(UPLOAD_DIR=settings.BASE_DIR / "testupload")
    @patch("core.models.pic.PicItem.ensure")
    def test_idempotency_with_headers_and_files(self, mock_ensure):
        """Assert that duplicate uploads return X-Duplicate header."""
        # Create a dummy PicItem return value.
        expected_pic = self.pic_mock(code="DUPE1234", fmt="png", size=10)
        mock_ensure.return_value = expected_pic
        testpath = settings.BASE_DIR / "testupload"

        # Create a valid file upload.
        valid_file = self.mock_picfile("valid.png", b"somecontent")
        resp = self.client_file_upload(valid_file)
        filepath = testpath / f"{expected_pic.item.code}.{expected_pic.format}"

        # Assert first file exists and response does not contain X-Duplicate header.
        self.assertTrue(filepath.exists(), "Test file wasn't saved")
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn("X-Duplicate", resp)
        # Now assert 200, X-Duplicate head and no extra files created on 2nd upload.
        num_files = len(list(testpath.iterdir()))
        valid_file = self.mock_picfile("valid.png", b"somecontent")
        resp = self.client_file_upload(valid_file)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get("X-Duplicate"), "true")
        self.assertEqual(len(list(testpath.iterdir())), num_files)
