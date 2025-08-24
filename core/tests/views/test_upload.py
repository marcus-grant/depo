from datetime import timedelta, timezone
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import TestCase, Client, override_settings
from django.urls import reverse

from core.tests.fixtures import (
    PNG_MAGIC,
    JPEG_MAGIC,
    GIF_MAGIC_89A,
    PNG_BASE64,
    PNG_BASE64_DATA_URI,
)

User = get_user_model()

# =============================================================================
# Web Endpoint Tests - GET
# =============================================================================


class WebUploadViewGETTests(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        # Assuming the web upload GET view is named "web_upload" in your urls.
        self.url = reverse("web_upload")
        self.url_index = reverse("index")
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
        upload_file = self.mock_picfile("dummy.png", PNG_MAGIC)
        self.client_file_upload(upload_file)
        mock.assert_called_once_with(PNG_MAGIC)

    @patch("core.models.pic.PicItem.ensure")
    def test_file_saved_as_hash_filename_fmt_ext(self, mock):
        """Uploaded file should be saved with a filename derived from PicItem.ensure (hash and file format)."""
        mock = self.mock_ensure_pic(mock, code="DUMYHASH", fmt="gif")
        upload_file = self.mock_picfile("dummy.gif", GIF_MAGIC_89A)
        self.client_file_upload(upload_file)
        expected_filename = f"{mock().item.code}.{mock().format}"
        expected_filepath = self.upload_dir / expected_filename
        self.assertTrue(expected_filepath.exists())

    @patch("core.models.pic.PicItem.ensure")
    def test_response_contains_model_details(self, mock):
        """Response should include model details (e.g., code and file format) in its plain text output."""
        mock = self.mock_ensure_pic(mock, code="DUMYHASH", fmt="jpg")
        upload = self.mock_picfile("dummy.jpg", JPEG_MAGIC)
        resp = self.client_file_upload(upload)
        resp_text = resp.content.decode()
        self.assertIn(mock().item.code, resp_text)
        self.assertIn(mock().format, resp_text)

    @patch("core.models.pic.PicItem.ensure")
    def test_upload_accepts_allowed_file_types(self, mock):
        """Allowed file types (jpg, png, gif) should be processed correctly."""
        mock = self.mock_ensure_pic(mock)
        file_jpg = self.mock_picfile("t.jpg", JPEG_MAGIC)
        file_png = self.mock_picfile("t.png", PNG_MAGIC)
        file_gif = self.mock_picfile("t.gif", GIF_MAGIC_89A)
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

    @patch("core.views.upload.file_type")
    def test_file_type_validator_called_for_invalid_file(self, mock_file_type):
        """Verify file_type validator is called and returns None for invalid file data"""
        mock_file_type.return_value = None
        invalid_file = SimpleUploadedFile("bad.txt", b"Not an image", content_type="text/plain")
        resp = self.client_file_upload(invalid_file)
        mock_file_type.assert_called_once_with(b"Not an image")
        self.assertEqual(resp.status_code, 400)

    @patch("core.models.pic.PicItem.ensure")
    def test_empty_file_upload_returns_error(self, mock):
        """Uploading an empty file should return a 400 error and not call PicItem.ensure."""
        empty_file = self.mock_picfile("empty.png", b"")
        resp = self.client_file_upload(empty_file)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("EMPTY", resp.content.decode().upper())
        mock.assert_not_called()

    @patch("core.views.upload.file_empty")
    def test_file_empty_validator_called_for_empty_file(self, mock_file_empty):
        """Verify file_empty validator is called with empty file data"""
        mock_file_empty.return_value = True
        empty_file = self.mock_picfile("empty.png", b"")
        resp = self.client_file_upload(empty_file)
        mock_file_empty.assert_called_once_with(b"")
        self.assertEqual(resp.status_code, 400)

    @patch("core.models.pic.PicItem.ensure")
    def test_file_write_error_returns_server_error(self, mock):
        """Simulate a file write error to ensure a 500 error is returned."""
        mock = self.mock_ensure_pic(mock, code="ERRHASH", fmt="jpg")
        upload = self.mock_picfile("dummy.jpg", JPEG_MAGIC)
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
        upload = self.mock_picfile("test.png", PNG_MAGIC)
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

    @override_settings(MAX_UPLOAD_SIZE=100)
    @patch("core.views.upload.file_too_big")
    def test_file_too_big_validator_called_for_oversized_file(self, mock_file_too_big):
        """Verify file_too_big validator is called with oversized file data"""
        mock_file_too_big.return_value = True
        upload = self.mock_picfile("oversized.jpg", b"A" * 101)
        resp = self.client_file_upload(upload)
        mock_file_too_big.assert_called_once_with(b"A" * 101, 100)
        self.assertEqual(resp.status_code, 400)

    @patch("core.models.pic.PicItem.ensure")
    def test_malicious_filename_is_ignored(self, mock):
        """
        Even if an uploaded file has a malicious filename (e.g., with path traversal),
        it should be saved using a safe, hashed filename.
        """
        mock = self.mock_ensure_pic(mock, code="SAFEHASH", fmt="png")
        upload = self.mock_picfile("../../evil.jpg", PNG_MAGIC)
        resp = self.client_file_upload(upload)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("SAFEHASH.png", resp.content.decode())
        self.assertTrue((self.upload_dir / "SAFEHASH.png").exists())

    def test_upload_without_authentication(self):
        """If a user is not authenticated, the upload request should redirect to the login page."""
        content = PNG_MAGIC
        upload_file = self.mock_picfile("test.png", content)
        self.client.logout()
        resp = self.client.post(self.upload_url, {"content": upload_file})
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/accounts/login/", resp["Location"])

    def test_base64_image_detection_flag_set_for_png(self):
        """Test that base-64 PNG data URIs set request.is_base64_image flag"""
        from unittest.mock import patch

        # Test with a minimal base-64 PNG data URI
        base64_png = PNG_BASE64_DATA_URI

        # Mock the view to capture the request object
        with patch(
            "core.views.upload.web_upload_view",
            wraps=__import__("core.views.upload").views.upload.web_upload_view,
        ) as mock_view:

            def capture_request(request):
                # Check that the flag is set correctly
                self.assertTrue(hasattr(request, "is_base64_image"))
                self.assertTrue(request.is_base64_image)
                # Call the original function
                return mock_view.__wrapped__(request)

            mock_view.side_effect = capture_request

            # POST the base-64 image as content (not file upload)
            resp = self.client.post(self.upload_url, {"content": base64_png})

    def test_base64_image_detection_flag_false_for_text(self):
        """Test that regular text content doesn't set the base-64 image flag"""
        from unittest.mock import patch

        text_content = "https://example.com"

        # Mock the view to capture the request object
        with patch(
            "core.views.upload.web_upload_view",
            wraps=__import__("core.views.upload").views.upload.web_upload_view,
        ) as mock_view:

            def capture_request(request):
                # Check that the flag is set correctly
                self.assertTrue(hasattr(request, "is_base64_image"))
                self.assertFalse(request.is_base64_image)
                # Call the original function
                return mock_view.__wrapped__(request)

            mock_view.side_effect = capture_request

            # POST regular text content
            resp = self.client.post(self.upload_url, {"content": text_content})

    def test_base64_png_converted_to_uploaded_file(self):
        """Test that base-64 PNG data is converted to InMemoryUploadedFile"""
        import base64
        from unittest.mock import patch

        # Test with a minimal base-64 PNG data URI
        base64_png = PNG_BASE64_DATA_URI

        # Decode to get expected bytes
        expected_bytes = base64.b64decode(PNG_BASE64)

        with patch("core.views.upload.upload_view_post") as mock_post:

            def capture_request(request):
                # Check that base-64 was converted to file
                self.assertTrue(hasattr(request, "is_base64_image"))
                self.assertTrue(request.is_base64_image)
                self.assertIn("content", request.FILES)

                uploaded_file = request.FILES["content"]
                self.assertEqual(uploaded_file.name, "clipboard.png")
                self.assertEqual(uploaded_file.content_type, "image/png")
                self.assertEqual(uploaded_file.read(), expected_bytes)

                # Return a mock response
                from django.http import HttpResponse

                return HttpResponse("OK")

            mock_post.side_effect = capture_request

            # POST the base-64 image
            resp = self.client.post(self.upload_url, {"content": base64_png})

    def test_base64_jpeg_converted_to_uploaded_file(self):
        """Test that base-64 JPEG data is converted to InMemoryUploadedFile"""
        import base64
        from unittest.mock import patch

        # Test with a minimal base-64 JPEG data URI (just the JPEG header)
        jpeg_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF"
        jpeg_b64 = base64.b64encode(jpeg_bytes).decode()
        base64_jpeg = f"data:image/jpeg;base64,{jpeg_b64}"

        with patch("core.views.upload.upload_view_post") as mock_post:

            def capture_request(request):
                # Check that base-64 was converted to file
                self.assertTrue(hasattr(request, "is_base64_image"))
                self.assertTrue(request.is_base64_image)
                self.assertIn("content", request.FILES)

                uploaded_file = request.FILES["content"]
                self.assertEqual(uploaded_file.name, "clipboard.jpg")
                self.assertEqual(uploaded_file.content_type, "image/jpeg")
                self.assertEqual(uploaded_file.read(), jpeg_bytes)

                # Return a mock response
                from django.http import HttpResponse

                return HttpResponse("OK")

            mock_post.side_effect = capture_request

            # POST the base-64 image
            resp = self.client.post(self.upload_url, {"content": base64_jpeg})

    @override_settings(MAX_UPLOAD_SIZE=50)
    def test_base64_image_respects_size_limits(self):
        """Test that base-64 images are rejected when exceeding MAX_UPLOAD_SIZE"""
        import base64

        # Create a valid PNG that's larger than 50 bytes
        # Use a real PNG and add padding to make it larger
        small_png = base64.b64decode(PNG_BASE64)
        # Add extra data to make it > 50 bytes when base64 encoded
        large_image_bytes = small_png + b"A" * 30  # Will make the base64 string longer
        large_b64 = base64.b64encode(large_image_bytes).decode()
        base64_large = f"data:image/png;base64,{large_b64}"

        # POST the oversized base-64 image
        resp = self.client.post(self.upload_url, {"content": base64_large})

        # Should return 400 error - either size limit or validation error
        self.assertEqual(resp.status_code, 400)
        # The corrupted PNG will fail validation before size check
        resp_text = resp.content.decode()
        self.assertTrue(
            "File size" in resp_text or "Invalid image data" in resp_text,
            f"Expected size or validation error, got: {resp_text}",
        )

    def test_base64_image_respects_type_validation(self):
        """Test that base-64 images flow through existing type validation"""
        import base64
        from unittest.mock import patch

        # Create a valid PNG with proper magic bytes
        png_bytes = base64.b64decode(PNG_BASE64)
        png_b64 = base64.b64encode(png_bytes).decode()
        base64_png = f"data:image/png;base64,{png_b64}"

        with patch("core.models.pic.PicItem.ensure") as mock_ensure:
            # Mock successful PicItem creation
            mock_pic = mock_ensure.return_value
            mock_pic.item.code = "TESTHASH"
            mock_pic.format = "png"

            # POST the base-64 image
            resp = self.client.post(self.upload_url, {"content": base64_png})

            # Should call PicItem.ensure with the decoded bytes
            self.assertEqual(resp.status_code, 200)
            mock_ensure.assert_called_once_with(png_bytes)

    def test_base64_invalid_type_rejected(self):
        """Test that base-64 images with invalid magic bytes are rejected"""
        import base64

        # Create invalid image data (no proper magic bytes)
        invalid_bytes = b"not_an_image_at_all"
        invalid_b64 = base64.b64encode(invalid_bytes).decode()
        base64_invalid = f"data:image/png;base64,{invalid_b64}"

        # POST the invalid base-64 image
        resp = self.client.post(self.upload_url, {"content": base64_invalid})

        # Should return 400 error for invalid file type
        self.assertEqual(resp.status_code, 400)
        resp_text = resp.content.decode().lower()
        self.assertIn("invalid", resp_text)
        self.assertIn("image", resp_text)

    def test_server_side_classification_base64_image(self):
        """Test that server-side classification returns 'image' for base-64 images"""
        import base64
        from unittest.mock import patch

        # Create a valid PNG
        png_bytes = base64.b64decode(PNG_BASE64)
        png_b64 = base64.b64encode(png_bytes).decode()
        base64_png = f"data:image/png;base64,{png_b64}"

        with patch("core.views.upload.classify_type") as mock_classify:
            # POST the base-64 image
            resp = self.client.post(self.upload_url, {"content": base64_png})

            # Should call classify_content_type with request
            mock_classify.assert_called_once()
            call_args = mock_classify.call_args[0]
            request = call_args[0]

            # Verify request has base-64 image flag and files
            self.assertTrue(request.is_base64_image)
            self.assertIn("content", request.FILES)

    def test_server_side_classification_regular_file(self):
        """Test that server-side classification returns 'image' for regular file uploads"""
        from unittest.mock import patch

        # Create a regular file upload
        upload_file = self.mock_picfile("test.png", PNG_MAGIC)

        with patch("core.views.upload.classify_type") as mock_classify:
            # POST the regular file
            resp = self.client_file_upload(upload_file)

            # Should call classify_content_type with request
            mock_classify.assert_called_once()
            call_args = mock_classify.call_args[0]
            request = call_args[0]

            # Verify request has files but not base-64 flag
            self.assertFalse(getattr(request, "is_base64_image", False))
            self.assertIn("content", request.FILES)

    def test_server_side_classification_url_content(self):
        """Test that server-side classification returns 'url' for URL content"""
        from unittest.mock import patch

        url_content = "https://example.com"

        with patch("core.views.upload.classify_type") as mock_classify:
            # Mock the classification function to return 'url'
            mock_classify.return_value = "url"

            # POST URL content (will fail at upload stage but classification happens first)
            resp = self.client.post(self.upload_url, {"content": url_content})

            # Should call classify_content_type
            mock_classify.assert_called_once()

    def test_server_side_classification_text_content(self):
        """Test that server-side classification returns 'text' for plain text"""
        from unittest.mock import patch

        text_content = "Hello world, this is plain text"

        with patch("core.views.upload.classify_type") as mock_classify:
            # Mock the classification function to return 'text'
            mock_classify.return_value = "text"

            # POST text content (will fail at upload stage but classification happens first)
            resp = self.client.post(self.upload_url, {"content": text_content})

            # Should call classify_content_type
            mock_classify.assert_called_once()


# =============================================================================
# Security Hardening Tests
# =============================================================================


@override_settings(UPLOAD_DIR=Path(settings.BASE_DIR) / "tmp")
class SecurityHardeningTests(TestCase):
    """Tests for security hardening checks on base-64 uploads"""

    def setUp(self):
        self.client = Client()
        self.upload_url = reverse("web_upload")
        self.upload_dir = Path(settings.UPLOAD_DIR)
        # Ensure the temporary upload directory exists.
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        # Create and log in a test user
        self.user = User.objects.create_user(
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

    @override_settings(DEPO_MAX_BASE64_SIZE=8 * 1024 * 1024)  # 8MB limit for base-64
    def test_base64_string_over_limit_rejected(self):
        """Test that base-64 strings over DEPO_MAX_BASE64_SIZE are rejected before decode"""
        import base64

        # Create a string that when base-64 encoded exceeds 8MB
        # Base-64 encoding increases size by ~33%, so we need original data of about 6MB
        large_data = b"A" * (6 * 1024 * 1024)  # 6MB of data
        large_b64 = base64.b64encode(large_data).decode()
        large_base64_uri = f"data:image/png;base64,{large_b64}"

        # Verify the encoded string is over the limit
        from django.conf import settings

        self.assertGreater(len(large_base64_uri), settings.DEPO_MAX_BASE64_SIZE)

        # POST the oversized base-64 string
        resp = self.client.post(self.upload_url, {"content": large_base64_uri})

        # Should return 400 error with specific message
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Image too large", resp.content.decode())

    def test_mime_type_mismatch_rejected(self):
        """Test that MIME type mismatch between header and actual data is rejected"""
        import base64

        # Create a PNG image but label it as JPEG
        png_bytes = PNG_MAGIC + b"dummy_png_data"
        png_b64 = base64.b64encode(png_bytes).decode()
        # Deliberately mislabel as JPEG
        mislabeled_uri = f"data:image/jpeg;base64,{png_b64}"

        # POST the mislabeled image
        resp = self.client.post(self.upload_url, {"content": mislabeled_uri})

        # Should return 400 error with validation message
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Invalid image data", resp.content.decode())

    def test_valid_image_passes_hardening_checks(self):
        """Test that valid images pass all hardening checks"""
        import base64
        from unittest.mock import patch

        # Create a minimal valid PNG (1x1 transparent pixel)
        # This is a real, minimal PNG file that Pillow can process
        png_bytes = base64.b64decode(PNG_BASE64)
        png_b64 = base64.b64encode(png_bytes).decode()
        valid_uri = f"data:image/png;base64,{png_b64}"

        # Verify it's under size limit
        from django.conf import settings

        self.assertLess(
            len(valid_uri), getattr(settings, "DEPO_MAX_BASE64_SIZE", 8 * 1024 * 1024)
        )

        with patch("core.models.pic.PicItem.ensure") as mock_ensure:
            # Mock successful PicItem creation
            mock_pic = mock_ensure.return_value
            mock_pic.item.code = "VALIDHASH"
            mock_pic.format = "png"

            # POST the valid image
            resp = self.client.post(self.upload_url, {"content": valid_uri})

            # Should succeed
            self.assertEqual(resp.status_code, 200)
            mock_ensure.assert_called_once_with(png_bytes)

    def test_malformed_base64_rejected(self):
        """Test that malformed base-64 data is rejected with proper error"""
        # Create malformed base-64 data (invalid characters)
        malformed_uri = "data:image/png;base64,This_is_not_valid_base64!@#$%"

        # POST the malformed data
        resp = self.client.post(self.upload_url, {"content": malformed_uri})

        # Should return 400 error
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Invalid image data", resp.content.decode())


# =============================================================================
# Feature Flag Tests
# =============================================================================


@override_settings(UPLOAD_DIR=Path(settings.BASE_DIR) / "tmp")
class FeatureFlagTests(TestCase):
    """Tests for DEPO_ALLOW_BASE64_IMAGES feature flag"""

    def setUp(self):
        self.client = Client()
        self.upload_url = reverse("web_upload")
        self.upload_dir = Path(settings.UPLOAD_DIR)
        # Ensure the temporary upload directory exists.
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        # Create and log in a test user
        self.user = User.objects.create_user(
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

    @override_settings(DEPO_ALLOW_BASE64_IMAGES=False)
    def test_base64_disabled_returns_404(self):
        """Test that setting DEPO_ALLOW_BASE64_IMAGES=False returns 404 for base-64 uploads"""
        import base64

        # Create a valid PNG
        png_bytes = base64.b64decode(PNG_BASE64)
        png_b64 = base64.b64encode(png_bytes).decode()
        base64_png = f"data:image/png;base64,{png_b64}"

        # POST the base-64 image
        resp = self.client.post(self.upload_url, {"content": base64_png})

        # Should return 404 when feature is disabled
        self.assertEqual(resp.status_code, 404)
        self.assertIn("Feature not available", resp.content.decode())

    @override_settings(DEPO_ALLOW_BASE64_IMAGES=True)
    def test_base64_enabled_allows_upload(self):
        """Test that setting DEPO_ALLOW_BASE64_IMAGES=True allows base-64 uploads"""
        import base64
        from unittest.mock import patch

        # Create a valid PNG
        png_bytes = base64.b64decode(PNG_BASE64)
        png_b64 = base64.b64encode(png_bytes).decode()
        base64_png = f"data:image/png;base64,{png_b64}"

        with patch("core.models.pic.PicItem.ensure") as mock_ensure:
            # Mock successful PicItem creation
            mock_pic = mock_ensure.return_value
            mock_pic.item.code = "TESTHASH"
            mock_pic.format = "png"

            # POST the base-64 image
            resp = self.client.post(self.upload_url, {"content": base64_png})

            # Should succeed when feature is enabled
            self.assertEqual(resp.status_code, 200)
            mock_ensure.assert_called_once_with(png_bytes)

    def test_base64_default_enabled(self):
        """Test that base-64 uploads are enabled by default (when setting not specified)"""
        import base64
        from unittest.mock import patch

        # Create a valid PNG
        png_bytes = base64.b64decode(PNG_BASE64)
        png_b64 = base64.b64encode(png_bytes).decode()
        base64_png = f"data:image/png;base64,{png_b64}"

        with patch("core.models.pic.PicItem.ensure") as mock_ensure:
            # Mock successful PicItem creation
            mock_pic = mock_ensure.return_value
            mock_pic.item.code = "DEFAULTHASH"
            mock_pic.format = "png"

            # POST the base-64 image (without explicit setting)
            resp = self.client.post(self.upload_url, {"content": base64_png})

            # Should succeed by default
            self.assertEqual(resp.status_code, 200)
            mock_ensure.assert_called_once_with(png_bytes)

    @override_settings(DEPO_ALLOW_BASE64_IMAGES=False)
    def test_regular_file_uploads_unaffected_by_flag(self):
        """Test that regular file uploads work regardless of DEPO_ALLOW_BASE64_IMAGES setting"""
        from unittest.mock import patch

        # Create a regular PNG file upload
        png_content = PNG_MAGIC
        upload_file = SimpleUploadedFile(
            "test.png", png_content, content_type="image/png"
        )

        with patch("core.models.pic.PicItem.ensure") as mock_ensure:
            # Mock successful PicItem creation
            mock_pic = mock_ensure.return_value
            mock_pic.item.code = "FILEHASH"
            mock_pic.format = "png"

            # POST regular file upload
            resp = self.client.post(self.upload_url, {"content": upload_file})

            # Should succeed even when base-64 is disabled
            self.assertEqual(resp.status_code, 200)
            mock_ensure.assert_called_once_with(png_content)


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
