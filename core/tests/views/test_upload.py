from datetime import timedelta, timezone
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import TestCase, Client, override_settings
from django.urls import reverse

User = get_user_model()

# =============================================================================
# Web Endpoint Tests - GET
# =============================================================================


class WebUploadViewGETTests(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        # Assuming the web upload GET view is named "web_upload" in your urls.
        self.url = reverse("web_upload")
        self.name = "testuser"
        self.email = "test@example.com"
        self.passw = "password"

    def login(self):
        self.user = User.objects.create_user(  # type: ignore
            username=self.name, email=self.email, password=self.passw
        )
        self.client = Client()
        self.client.login(username=self.name, password=self.passw)

    def test_upload_requires_auth(self):
        """Access without authentication should redirect to the login page."""
        resp = self.client.get(self.url)
        # Should not be a normal 200 OK page when not logged in.
        self.assertNotEqual(resp.status_code, 200)
        redirect_url = resp.headers.get("Location")
        self.assertIsNotNone(redirect_url)
        self.assertTrue(redirect_url.startswith("/accounts/login"))  # type: ignore

    def test_upload_view_authenticated(self):
        """A logged-in user should be able to access the upload page via GET."""
        # Log in as a test user.
        self.login()
        # Make a GET request with follow to follow any redirects.
        resp = self.client.get(reverse("web_upload"), follow=True)
        # Check that the response has a 200 status code.
        self.assertEqual(resp.status_code, 200)
        # Check that the correct template is used.
        self.assertTemplateUsed(resp, "upload.html")
        # Get response content as a string.
        content = resp.content.decode()
        # Check that the upload form is present.
        self.assertIn("<form", content)
        self.assertIn('type="file"', content)
        # Ensure that the form contains a csrf token.
        self.assertIn("csrfmiddlewaretoken", content)
        # Ensure that there is a submit button in the form.
        self.assertIn('button type="submit"', content)


# =============================================================================
# Web Endpoint Tests - POST (File Uploads)
# =============================================================================


@override_settings(UPLOAD_DIR=Path(settings.BASE_DIR) / "tmp")
class WebUploadViewPostTests(TestCase):
    """
    These tests simulate browser-based file uploads using session authentication.
    """

    def setUp(self):
        self.client = Client()
        self.upload_url = reverse("web_upload")
        self.upload_dir = Path(settings.UPLOAD_DIR)
        # Ensure the temporary upload directory exists.
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        # Create and log in a test user.
        self.user = User.objects.create_user(  # type: ignore
            username="tester", email="test@example.com", password="password"
        )
        self.client.login(username="tester", password="password")

    def tearDown(self):
        # Remove all files and the temporary directory.
        if self.upload_dir.exists():
            for file in self.upload_dir.iterdir():
                if file.is_file():
                    file.unlink()
                elif file.is_dir():
                    file.rmdir()
            self.upload_dir.rmdir()

    def mock_ensure_pic(self, mock, code="M0CKHASH", fmt="jpg", size=0):
        dummy = MagicMock()
        dummy.item.code = code
        dummy.format = fmt
        dummy.size = size
        mock.return_value = dummy
        return mock

    def mock_picfile(self, fname, fcontent):
        # Determine content type based on file extension.
        fname_lower = fname.lower()
        ctype = ""
        if fname_lower.endswith((".jpg", ".jpeg")):
            ctype = "image/jpeg"
        elif fname_lower.endswith(".png"):
            ctype = "image/png"
        elif fname_lower.endswith(".gif"):
            ctype = "image/gif"
        return SimpleUploadedFile(fname, fcontent, content_type=ctype)

    def client_file_upload(self, file):
        """
        Helper to perform file upload to the web endpoint using session authentication.
        """
        return self.client.post(self.upload_url, {"content": file})

    @patch("core.models.pic.PicItem.ensure")
    def test_ensure_call_with_file_content(self, mock):
        """Verify PicItem.ensure is called with the exact file content."""
        mock = self.mock_ensure_pic(mock, code="DUMYHASH", fmt="png")
        upload_file = self.mock_picfile("dummy.png", b"\x89PNG\r\n\x1a\n")
        self.client_file_upload(upload_file)
        mock.assert_called_once_with(b"\x89PNG\r\n\x1a\n")

    @patch("core.models.pic.PicItem.ensure")
    def test_file_saved_as_hash_filename_fmt_ext(self, mock):
        """Uploaded file should be saved with a filename derived from PicItem.ensure (hash and file format)."""
        mock = self.mock_ensure_pic(mock, code="DUMYHASH", fmt="gif")
        upload_file = self.mock_picfile("dummy.gif", b"GIF89a")
        self.client_file_upload(upload_file)
        expected_filename = f"{mock().item.code}.{mock().format}"
        expected_filepath = self.upload_dir / expected_filename
        self.assertTrue(expected_filepath.exists())

    @patch("core.models.pic.PicItem.ensure")
    def test_response_contains_model_details(self, mock):
        """Response should include model details (e.g., code and file format) in its plain text output."""
        mock = self.mock_ensure_pic(mock, code="DUMYHASH", fmt="jpg")
        upload = self.mock_picfile("dummy.jpg", b"\xff\xd8\xff")
        resp = self.client_file_upload(upload)
        resp_text = resp.content.decode()
        self.assertIn(mock().item.code, resp_text)
        self.assertIn(mock().format, resp_text)

    @patch("core.models.pic.PicItem.ensure")
    def test_upload_accepts_allowed_file_types(self, mock):
        """Allowed file types (jpg, png, gif) should be processed correctly."""
        mock = self.mock_ensure_pic(mock)
        file_jpg = self.mock_picfile("t.jpg", b"\xff\xd8\xff")
        file_png = self.mock_picfile("t.png", b"\x89PNG\r\n\x1a\n")
        file_gif = self.mock_picfile("t.gif", b"GIF89a")
        resp_jpg = self.client_file_upload(file_jpg)
        resp_png = self.client_file_upload(file_png)
        resp_gif = self.client_file_upload(file_gif)
        self.assertEqual(resp_jpg.status_code, 200)
        self.assertEqual(resp_png.status_code, 200)
        self.assertEqual(resp_gif.status_code, 200)
        self.assertEqual(mock.call_count, 3)

    @patch("core.models.pic.PicItem.ensure")
    def test_upload_rejects_disallowed_file_types(self, mock):
        """Files with disallowed file types must be rejected."""
        content = b"Hello, world!"
        file_invalid = SimpleUploadedFile(
            "invalid.xyz", content, content_type="text/plain"
        )
        resp = self.client_file_upload(file_invalid)
        msg = resp.content.decode().lower()
        self.assertEqual(resp.status_code, 400)
        self.assertIn("invalid", msg)
        self.assertIn("type", msg)
        self.assertIn("allow", msg)
        mock.assert_not_called()

    @patch("core.models.pic.PicItem.ensure")
    def test_empty_file_upload_returns_error(self, mock):
        """Uploading an empty file should return a 400 error and not call PicItem.ensure."""
        empty_file = self.mock_picfile("empty.png", b"")
        resp = self.client_file_upload(empty_file)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("EMPTY", resp.content.decode().upper())
        mock.assert_not_called()

    @patch("core.models.pic.PicItem.ensure")
    def test_file_write_error_returns_server_error(self, mock):
        """Simulate a file write error to ensure a 500 error is returned."""
        mock = self.mock_ensure_pic(mock, code="ERRHASH", fmt="jpg")
        upload = self.mock_picfile("dummy.jpg", b"\xff\xd8\xff")
        with patch("core.views.upload.open", side_effect=OSError("Disk error")):
            resp = self.client_file_upload(upload)
        self.assertEqual(resp.status_code, 500)
        resp_text = resp.content.decode().upper()
        self.assertIn("ERROR", resp_text)
        self.assertIn("SAV", resp_text)
        self.assertIn("FILE", resp_text)

    @patch("core.models.pic.PicItem.ensure")
    def test_successful_upload_returns_custom_headers(self, mock):
        """Upon a successful upload, the response HTML should include a success message and detail link."""
        mock = self.mock_ensure_pic(mock, code="HEADERHASH", fmt="png")
        upload = self.mock_picfile("test.png", b"\x89PNG\r\n\x1a\n")
        resp = self.client_file_upload(upload)
        expected_filename = f"{mock().item.code}.{mock().format}"
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "text/html; charset=utf-8")
        content = resp.content.decode()
        # Verify that the HTML contains a success notification with the expected upload message.
        self.assertIn("Uploaded file", content)
        self.assertIn(expected_filename, content)
        # Check for the existence of a detail link leading to the uploaded item's page.
        self.assertRegex(content, r'<a\s[^>]*href="[^"]+"[^>]*>[^<]*</a>')

    @patch("core.models.pic.PicItem.ensure")
    def test_error_upload_returns_notif_info(self, _):
        """Uploads with errors should return an HTML response with error notification."""
        upload = SimpleUploadedFile(
            "bad.txt", b"Not an image", content_type="text/plain"
        )
        resp = self.client.post(self.upload_url, {"content": upload})

        # Ensure we have a 400 status code for error scenarios.
        self.assertEqual(resp.status_code, 400)
        # Response should now be HTML.
        self.assertEqual(resp.get("Content-Type"), "text/html; charset=utf-8")

        content = resp.content.decode().lower()
        # Check that the HTML contains the Bulma error notification.
        self.assertIn("notification is-danger", content)
        # Verify error-relevant messaging is rendered in the HTML.
        self.assertIn("invalid", content)
        self.assertIn("type", content)
        self.assertIn("allow", content)

    @override_settings(MAX_UPLOAD_SIZE=100)
    @patch("core.models.pic.PicItem.ensure")
    def test_upload_rejects_files_exceeding_max_size(self, mock):
        """Files exceeding MAX_UPLOAD_SIZE should be rejected with a 400 error."""
        upload = self.mock_picfile("oversized.jpg", b"A" * 101)
        resp = self.client_file_upload(upload)
        self.assertEqual(resp.status_code, 400)
        expected_msg = "File size 101 exceeds limit of 100 bytes"
        self.assertIn(expected_msg, resp.content.decode())
        mock.assert_not_called()

    @patch("core.models.pic.PicItem.ensure")
    def test_malicious_filename_is_ignored(self, mock):
        """
        Even if an uploaded file has a malicious filename (e.g., with path traversal),
        it should be saved using a safe, hashed filename.
        """
        mock = self.mock_ensure_pic(mock, code="SAFEHASH", fmt="png")
        upload = self.mock_picfile("../../evil.jpg", b"\x89PNG\r\n\x1a\n")
        resp = self.client_file_upload(upload)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("SAFEHASH.png", resp.content.decode())
        self.assertTrue((self.upload_dir / "SAFEHASH.png").exists())

    def test_upload_without_authentication(self):
        """If a user is not authenticated, the upload request should redirect to the login page."""
        content = b"\x89PNG\r\n\x1a\n"
        upload_file = self.mock_picfile("test.png", content)
        self.client.logout()
        resp = self.client.post(self.upload_url, {"content": upload_file})
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/accounts/login/", resp["Location"])


# =============================================================================
# API Endpoint Tests - POST (File Uploads)
# =============================================================================
# The following API tests are for a DRF-based upload endpoint (e.g. /api/upload).
# Right now we are focusing on the web endpoints; the API tests are commented out.
#
# from rest_framework.test import APIClient
#
# @override_settings(UPLOAD_DIR=Path(settings.BASE_DIR) / "tmp")
# class ApiUploadViewPostTests(TestCase):
#     """
#     These tests simulate API-based file uploads using JWT authentication for future endpoints.
#     Both desirable test cases and error cases here should mirror the functionality of the web endpoint tests.
#     """
#
#     def setUp(self):
#         self.client = APIClient()
#         self.upload_url = reverse("api_upload")
#         self.upload_dir = Path(settings.UPLOAD_DIR)
#         self.upload_dir.mkdir(parents=True, exist_ok=True)
#         self.user = User.objects.create_user(username="tester", email="test@example.com", password="password")
#         # Simulate API authentication (e.g. via JWT) if needed.
#         # For now, assume the endpoint requires a header with a valid token.
#         # token = <generate token using Django's built-in auth if applicable>
#         # self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
#
#     def tearDown(self):
#         if self.upload_dir.exists():
#             for file in self.upload_dir.iterdir():
#                 if file.is_file():
#                     file.unlink()
#                 elif file.is_dir():
#                     file.rmdir()
#             self.upload_dir.rmdir()
#
#     # API tests should mirror tests from WebUploadViewPostTests with adjustments to authentication
#     # and expected responses (e.g., returning JSON or plain text).
#     # For brevity, the API tests are omitted here and will be implemented when the endpoint is ready.
#
# =============================================================================
# End of File
