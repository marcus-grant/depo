# core/tests/views/test_upload.py
from datetime import datetime, timedelta, timezone
import os
from unittest.mock import MagicMock, patch

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.urls import reverse
import jwt

from core.user.models import User
from core.user.views import JWT_EXP_DELTA_SECONDS


# TODO: Create base TestCase classes to subtype to reduce duplicate testing code
class UploadViewGETTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.upload_url = reverse("upload")

    def test_upload_page_accessible_via_get(self):
        resp = self.client.get(self.upload_url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "upload.html")

    def test_upload_page_contains_file_input(self):
        resp = self.client.get(self.upload_url)
        self.assertContains(resp, '<input type="file"')

    def test_upload_page_contains_ui_element(self):
        """Upload page should contain:
        - File input for file selection.
        - A div with id="progress" indicating upload progress.
        - A div with id="preview" to show the pic preview."""
        resp = self.client.get(self.upload_url)
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        self.assertIn('<input type="file"', content)
        self.assertIn('id="progress"', content)
        self.assertIn('id="preview"', content)


@override_settings(UPLOAD_DIR=settings.BASE_DIR / "tmp")
class UploadViewPostTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.upload_url = reverse("upload")
        # Ensure temporary upload directory exists
        if not os.path.exists(settings.UPLOAD_DIR):
            os.makedirs(settings.UPLOAD_DIR)

        # Create a dummy test user; this user exists only in the test database.
        self.user = User.objects.create(name="tester", email="test@example.com")
        self.user.set_password("password")
        self.user.save()

        # Generate a JWT token for that user.
        payload = {
            "name": self.user.name,
            "email": self.user.email,
            "exp": datetime.now(timezone.utc)
            + timedelta(seconds=JWT_EXP_DELTA_SECONDS),
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        if isinstance(token, bytes):
            token = token.decode("utf-8")
        self.auth_bearer = f"Bearer {token}"
        self.auth_header = {"HTTP_AUTHORIZATION": f"Bearer {token}"}

        # Initialize the test client.
        self.client = Client()
        self.upload_url = reverse("upload")

    def tearDown(self):
        # Cleanup: remove all files in the directory
        for filename in os.listdir(settings.UPLOAD_DIR):
            file_path = os.path.join(settings.UPLOAD_DIR, filename)
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                os.rmdir(file_path)
        os.rmdir(settings.UPLOAD_DIR)  # Now remove directory

    def mock_ensure_pic(self, mock, code="M0CKHASH", fmt="jpg", size=0):
        dummy = MagicMock()
        dummy.item.code = code
        dummy.format = fmt
        dummy.size = size
        mock.return_value = dummy
        return mock

    def mock_picfile(self, fname, fcontent):
        ctype = ""
        ctype = "image/jpeg" if fname.endswith(".jpg") else ctype
        ctype = "image/jpeg" if fname.endswith(".jpeg") else ctype
        ctype = "image/png" if fname.endswith(".png") else ctype
        ctype = "image/gif" if fname.endswith(".gif") else ctype
        return SimpleUploadedFile(fname, fcontent, content_type=ctype)

    def client_file_upload(self, file, auth=True):
        data = {"content": file}
        headers = {}
        if auth:
            headers["HTTP_AUTHORIZATION"] = self.auth_bearer
        return self.client.post(self.upload_url, data, **headers)

    @patch("core.pic.models.PicItem.ensure")
    def test_ensure_call_with_file_content(self, mock):
        """Ensure should PicItem.ensure called with contents of uploaded file."""
        # Arrange: Dummy PicItem instance & Image file
        mock = self.mock_ensure_pic(mock, code="DUMYHASH", fmt="png")
        upload_file = self.mock_picfile("dummy.png", b"\x89PNG\r\n\x1a\n")
        # Act: POST the file for the upload view to handle
        self.client_file_upload(upload_file)
        # Assert: PicItem.ensure called with exact file contents
        mock.assert_called_once_with(b"\x89PNG\r\n\x1a\n")

    @patch("core.pic.models.PicItem.ensure")
    def test_file_saved_as_hash_filename_fmt_ext(self, mock):
        """Test uploaded pic file saved w/ Item.code & PicItem.format filename."""
        # Arrange: Dummy PicItem & Image file
        mock = self.mock_ensure_pic(mock, code="DUMYHASH", fmt="gif")
        # image_content = b"GIF89a"
        upload_file = self.mock_picfile("dummy.gif", b"GIF89a")
        # Act: Post image
        # self.client.post(self.upload_url, {"image": uploaded_file})
        self.client_file_upload(upload_file)
        # Assert: File should be saved to server FS correctly
        expect_filename = f"{mock().item.code}.{mock().format}"
        expect_filepath = settings.UPLOAD_DIR / expect_filename
        self.assertTrue(expect_filepath.exists())

    @patch("core.pic.models.PicItem.ensure")
    def test_response_contains_model_details(self, mock):
        """Response to upload needs to contain associated model details."""
        # Arrange: Prepare a dummy PicItem & Image file
        mock = self.mock_ensure_pic(mock, code="DUMYHASH", fmt="jpg")
        upload = self.mock_picfile("dummy.jpg", b"\xff\xd8\xff")
        # Act: POST image, capture response
        resp = self.client_file_upload(upload)
        resp_txt = resp.content.decode()
        # Assert: Response has file details
        self.assertIn(mock().item.code, resp_txt)
        self.assertIn(mock().format, resp_txt)

    @patch("core.pic.models.PicItem.ensure")
    def test_upload_accepts_allowed_file_types(self, mock):
        """Upload all valid filetypes, ensure upload approved & ensure called."""
        # Arrange: Prepare a dummy PicItem to simulate normal processing & dummy JPEG
        mock = self.mock_ensure_pic(mock)
        fjpg = self.mock_picfile("t.jpg", b"\xff\xd8\xff")
        fpng = self.mock_picfile("t.png", b"\x89PNG\r\n\x1a\n")
        fgif = self.mock_picfile("t.gif", b"GIF89a")
        # Act: POST the file.
        resp_jpg = self.client_file_upload(fjpg)
        resp_png = self.client_file_upload(fpng)
        resp_gif = self.client_file_upload(fgif)
        self.client_file_upload(fgif)
        # Assert: Check for HTTP 200 and that processing occurred.
        self.assertEqual(resp_jpg.status_code, 200)
        self.assertEqual(resp_png.status_code, 200)
        self.assertEqual(resp_gif.status_code, 200)
        self.assertEqual(mock.call_count, 3)

    @patch("core.pic.models.PicItem.ensure")
    def test_upload_rejects_disallowed_file_types(self, mock):
        """Non accepted filetypes should be rejected"""
        # Arrange: Create a dummy text file.
        x = b"Hello, world!"
        file = SimpleUploadedFile("invalid.xyz", x, content_type="text/plain")
        # Act: POST the file.
        resp = self.client_file_upload(file)
        msg = resp.content.decode().lower()
        # Assert: Expect HTTP 400 and that PicItem.ensure is never called.
        self.assertEqual(resp.status_code, 400)
        self.assertIn("invalid", msg)
        self.assertIn("type", msg)
        self.assertIn("allow", msg)
        mock.assert_not_called()

    @patch("core.pic.models.PicItem.ensure")
    def test_empty_file_upload_returns_error(self, mock):
        """If the uploaded file is empty, view should return HTTP 400, dont call PicItem.ensure"""
        # Arrange: Create an empty file upload.
        empty_file = self.mock_picfile("empty.png", b"")
        # Act: POST the empty file.
        resp = self.client_file_upload(empty_file)
        # Assert: Expect HTTP 400 and ensure PicItem.ensure is not called.
        self.assertEqual(resp.status_code, 400)
        self.assertIn("EMPTY", resp.content.decode().upper())
        mock.assert_not_called()

    @patch("core.pic.models.PicItem.ensure")
    def test_file_write_error_returns_server_error(self, mock):
        """If error occurs during file writing, view should return HTTP 500."""
        # Arrange: Set up a dummy PicItem so processing proceeds.
        mock = self.mock_ensure_pic(mock, code="ERRHASH", fmt="jpg")
        # Create a dummy image file (non-empty).
        upload = self.mock_picfile("dummy.jpg", b"\xff\xd8\xff")
        # Act: POST the file while patching open func simulating saving error.
        with patch("core.views.open", side_effect=OSError("Disk error")):
            resp = self.client_file_upload(upload)
        # Assert: Expect HTTP 500 and an error message mentioning file saving.
        self.assertEqual(resp.status_code, 500)
        self.assertIn("ERROR", resp.content.decode().upper())
        self.assertIn("SAV", resp.content.decode().upper())
        self.assertIn("FILE", resp.content.decode().upper())

    @patch("core.pic.models.PicItem.ensure")
    def test_successful_upload_returns_custom_headers(self, mock):
        """Upload successes should include X-Uploaded-Filename header."""
        # Arrange: Set up a dummy PicItem so that processing works normally.
        mock = self.mock_ensure_pic(mock, code="HEADERHASH", fmt="png")
        upload = self.mock_picfile("test.png", b"\x89PNG\r\n\x1a\n")
        # Act: POST the file with Accept header set to text/plain.
        resp = self.client_file_upload(upload)
        # Assert: 200 OK, plain text type, expected filename in header, msg body
        expected_filename = f"{mock().item.code}.{mock().format}"
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "text/plain")
        self.assertEqual(resp.get("X-Uploaded-Filename"), expected_filename)
        self.assertIn(expected_filename, resp.content.decode())

    @patch("core.pic.models.PicItem.ensure")
    def test_error_upload_returns_custom_error_headers(self, _):
        """X-Error header should be response to bad upload"""
        # Arrange: Create a file with disallowed content.
        # For example, a text file instead of an image.
        upload = SimpleUploadedFile(
            "bad.txt", b"Not an image", content_type="text/plain"
        )
        # Act: POST the file with Accept header set to text/plain.
        resp = self.client_file_upload(upload)
        msg = resp.content.decode().lower()
        # Assert: Status code, content and error headers, and body
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp["Content-Type"], "text/plain")
        self.assertEqual(resp.get("X-Error"), "true")
        self.assertIn("invalid", msg)
        self.assertIn("type", msg)
        self.assertIn("allow", msg)

    @override_settings(MAX_UPLOAD_SIZE=100)
    @patch("core.pic.models.PicItem.ensure")
    def test_upload_rejects_files_exceeding_max_size(self, mock):
        """If upload file exceeds MAX_UPLOAD_SIZE, respond with 400 with message"""
        # Arrange: Create dummy image file with oversized content length
        upload = self.mock_picfile("oversized.jpg", b"A" * 101)
        # Act: POST file
        resp = self.client_file_upload(upload)
        # Assert: Expect HTTP 400 error & message about size
        self.assertEqual(resp.status_code, 400)
        expect = "File size 101 exceeds limit of 100 bytes"
        self.assertIn(expect, resp.content.decode())
        mock.assert_not_called()

    @patch("core.pic.models.PicItem.ensure")
    def test_malicious_filename_is_ignored(self, mock):
        """
        Even if uploaded file has a malicious filename,
        the saved file should use safe, hashed filename from PicItem.ensure.
        """
        # Arrange: Setup a dummy PicItem and dummy upload file w/ malicious filename.
        mock = self.mock_ensure_pic(mock, code="SAFEHASH", fmt="png")
        upload = self.mock_picfile("../../evil.jpg", b"\x89PNG\r\n\x1a\n")
        # Act: POST the file.
        resp = self.client_file_upload(upload)
        # Assert: The file is saved with the safe hashed filename.
        self.assertEqual(resp.status_code, 200)
        self.assertIn("SAFEHASH.png", resp.content.decode())
        self.assertTrue(os.path.exists(settings.UPLOAD_DIR / "SAFEHASH.png"))

    def test_upload_without_auth_token(self):
        """An upload request without Authorization heeader should be rejected."""
        # Arrange: Create a dummy PNG file.
        content = b"\x89PNG\r\n\x1a\n"
        upld_file = SimpleUploadedFile("test.png", content, content_type="image/png")
        # Act: POST the file without any Authorization header.
        resp = self.client.post(self.upload_url, {"content": upld_file})
        # Assert: Expect HTTP 401 & plain text/header messages about auth
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.get("Content-Type"), "text/plain")
        self.assertEqual(resp.get("X-Error"), "true")
        self.assertIn("unauthor", resp.content.decode().lower())


@override_settings(
    UPLOAD_DIR=settings.BASE_DIR / "tmp", MAX_UPLOAD_SIZE=5 * 1024 * 1024
)
class UploadViewLoggingTests(TestCase):
    # TODO: Upload these common setup and teardown methods to a base testclass
    def setUp(self):
        self.client = Client()
        self.upload_url = reverse("upload")
        if not os.path.exists(settings.UPLOAD_DIR):
            os.makedirs(settings.UPLOAD_DIR)
        self.user = User.objects.create(name="tester", email="test@example.com")
        self.user.set_password("password")
        self.user.save()
        payload = {
            "name": self.user.name,
            "email": self.user.email,
            "exp": datetime.now(timezone.utc)
            + timedelta(seconds=JWT_EXP_DELTA_SECONDS),
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        if isinstance(token, bytes):
            token = token.decode("utf-8")
        self.auth_bearer = f"Bearer {token}"
        self.auth_header = {"HTTP_AUTHORIZATION": self.auth_bearer}

    def tearDown(self):
        for filename in os.listdir(settings.UPLOAD_DIR):
            file_path = os.path.join(settings.UPLOAD_DIR, filename)
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                os.rmdir(file_path)
        os.rmdir(settings.UPLOAD_DIR)

    # NOTE: Helper functions of repeat testing tasks
    # NOTE: READ THESE to learn how to use upload views
    def mock_ensure_pic(self, mock, code="L0GHASH7", fmt="png"):
        picitem = MagicMock()
        picitem.item.code = code
        picitem.format = fmt
        mock.return_value = picitem
        return mock

    def mock_file(self, fname, fcontent):
        # Helper:  Create SimpleUploadFile with correct content type
        if fname.endswith(".png"):
            ctype = "image/png"
        elif fname.endswith(".jpg") or fname.endswith(".jpeg"):
            ctype = "image/jpeg"
        elif fname.endswith(".gif"):
            ctype = "image/gif"
        else:
            ctype = "application/octet-stream"
        return SimpleUploadedFile(fname, fcontent, content_type=ctype)

    def client_file_upload(self, file, auth=True):
        data = {"content": file}
        headers = {}
        if auth:
            headers["HTTP_AUTHORIZATION"] = self.auth_bearer
        return self.client.post(self.upload_url, data, **headers)

    @patch("core.pic.models.PicItem.ensure")
    def test_successful_upload_logs_message(self, mock):
        """A successful upload should add an INFO log:
        - "Upload initiated" at start
        - "Upload completed: <filename> in <elapsed> seconds" on success
        """
        # Arrange: Set up dummy PicItem instance
        mock = self.mock_ensure_pic(mock)
        upload = self.mock_file("test.png", b"\x89PNG\r\n\x1a\n")

        # Act: Capture logs during upload request
        with self.assertLogs("depo.core.views", level="INFO") as log_cm:
            resp = self.client_file_upload(upload)
        log_out = " ".join(log_cm.output)

        # Assert: Response should be 200, logs contain upload init & complete
        self.assertEqual(resp.status_code, 200)
        self.assertIn("upload", log_out.lower())
        self.assertIn("init", log_out.lower())
        self.assertIn("complet", log_out.lower())
        self.assertIn(f"{mock().item.code}.{mock().format}", log_out)

    @patch("core.pic.models.PicItem.ensure")
    def test_upload_error_logs_error_message(self, mock):
        """File-save errors(OSError) should error.log with correct message."""
        # Arrange: Setup dummy pic item & dummy image file
        mock = self.mock_ensure_pic(mock)
        upload = self.mock_file("test.png", b"\x89PNG\r\n\x1a\n")

        # Act: Patch open to sim disk-err during POST, capture logs
        with patch("core.views.open", side_effect=OSError("Disk error")):
            with self.assertLogs("depo.core.views", level="ERROR") as log_cm:
                resp = self.client_file_upload(upload)
        log_out = " ".join(log_cm.output)

        # Assert: Response should have 500 status
        self.assertEqual(resp.status_code, 500)
        self.assertIn("error", log_out.lower())
        self.assertIn("save", log_out.lower())

    @patch("core.pic.models.PicItem.ensure")
    def test_empty_file_upload_logs_error(self, mock):
        """Empty file uploads should log err stating the problem."""
        # Arrange: Setup dummy pic item & empty image file
        mock = self.mock_ensure_pic(mock)
        upload = self.mock_file("empty.png", b"")

        # Act: Capture ERROR logs during upload
        with self.assertLogs("depo.core.views", level="ERROR") as log_cm:
            resp = self.client_file_upload(upload)
        log_out = " ".join(log_cm.output)

        # Assert: Response should have 400 status
        self.assertEqual(resp.status_code, 400)
        self.assertIn("error", log_out.lower())
        self.assertIn("empty", log_out.lower())
        self.assertIn("file", log_out.lower())

    @override_settings(MAX_UPLOAD_SIZE=100)
    @patch("core.pic.models.PicItem.ensure")
    def test_upload_logs_error_when_size_excessive(self, mock):
        """File uploads exceeding MAX_UPLOAD_SIZE should log error."""
        # Arrange: Setup dummy pic item & oversized image file
        mock = self.mock_ensure_pic(mock)
        upload = self.mock_file("oversized.jpg", b"A" * 101)
        # Act: Capture ERROR logs during upload
        with self.assertLogs("depo.core.views", level="ERROR") as log_cm:
            resp = self.client_file_upload(upload)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("byte", " ".join(log_cm.output).lower())
        self.assertIn("limit", " ".join(log_cm.output).lower())

    @patch("core.pic.models.PicItem.ensure")
    def test_upload_logs_error_on_invlid_type(self, mock):
        """File uploads of invalid content type should log error."""
        # Arrange: Setup dummy pic item & invalid content type file
        mock = self.mock_ensure_pic(mock)
        upload = self.mock_file("invalid.xyz", b"Invalid content")

        # Act: Capture ERROR logs during upload
        with self.assertLogs("depo.core.views", level="ERROR") as log_cm:
            resp = self.client_file_upload(upload)
        log_out = " ".join(log_cm.output)

        # Assert: Error log made, contains useful info, 400 resp code
        self.assertEqual(resp.status_code, 400)
        self.assertIn("invalid", log_out.lower())
        self.assertIn("type", log_out.lower())
