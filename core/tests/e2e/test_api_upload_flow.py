"""
E2E tests for API upload flow

Complete user journey testing:
1. POST binary image data to /api/upload/ endpoint
2. Receive shortcode and filename in response
3. Verify file is physically saved to UPLOAD_DIR with correct content
4. GET /{shortcode}/details to retrieve file metadata
5. Verify retrieved metadata matches uploaded file properties

No mocks used - tests real file I/O, database persistence, and HTTP responses.
"""

from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from pathlib import Path
from dataclasses import dataclass
from typing import List

from core.tests.fixtures import PNG_1X1_RED, JPG_1X1_BLK


@dataclass
class UploadTestCase:
    """Data structure defining a complete upload test scenario"""

    name: str
    data: bytes
    filename: str
    ctype: str
    fmt: str
    desc: str
    fail_msg: str
    succeed: bool = True
    status: int = 200
    err_msg: str = ""
    mime: str = ""  # Expected Content-Type for downloads

    def __post_init__(self):
        """Set expected MIME type based on format if not provided"""
        if not self.mime and self.succeed:
            if self.fmt == "png":
                self.mime = "image/png"
            elif self.fmt == "jpg":
                self.mime = "image/jpeg"
            elif self.fmt == "gif":
                self.mime = "image/gif"


@dataclass
class DownloadTestCase:
    """Data structure defining a download test scenario"""

    name: str
    suffix: str = ""  # Append to /raw/{shortcode}, e.g. ".jpg"
    expected_status_code: int = 200
    description: str = ""
    failure_message: str = ""
    should_succeed: bool = True
    expected_error_message: str = ""

    def build_url(self, shortcode: str, format: str) -> str:
        """Build download URL by appending suffix"""
        if self.suffix == ".{format}":
            return f"/raw/{shortcode}.{format}"
        elif self.suffix == ".{wrong_ext}":
            # Use a different extension than the actual format
            wrong_ext = "png" if format == "jpg" else "jpg"
            return f"/raw/{shortcode}.{wrong_ext}"
        else:
            # Direct suffix append (including empty string)
            return f"/raw/{shortcode}{self.suffix}"


# Test scenarios for upload flow
UPLOAD_TEST_CASES: List[UploadTestCase] = [
    UploadTestCase(
        name="png_red",
        data=PNG_1X1_RED,
        filename="red_pixel.png",
        ctype="image/png",
        fmt="png",
        desc="Upload 1x1 red PNG (70 bytes), verify hash filename & persistence",
        fail_msg="Failed PNG upload/retrieve - check header validation & file I/O",
    ),
    UploadTestCase(
        name="jpg_black",
        data=JPG_1X1_BLK,
        filename="black_pixel.jpg",
        ctype="image/jpeg",
        fmt="jpg",
        desc="Upload 1x1 black JPEG (299 bytes), verify processing & metadata",
        fail_msg="Failed JPEG upload/retrieve - check header validation & format detection",
    ),
    UploadTestCase(
        name="empty_reject",
        data=b"",
        filename="empty.png",
        ctype="image/png",
        fmt="",
        desc="Upload empty file (0 bytes), expect 400 rejection",
        fail_msg="Empty file should be rejected with 400 status",
        succeed=False,
        status=400,
        err_msg="No file uploaded",
    ),
    UploadTestCase(
        name="invalid_reject",
        data=b"This is not an image file at all, just plain text pretending to be PNG",
        filename="fake.png",
        ctype="image/png",
        fmt="",
        desc="Upload text file with PNG ext, expect 500 rejection for invalid format",
        fail_msg="Invalid image data should be rejected with 500 status",
        succeed=False,
        status=500,
        err_msg="Invalid upload format",
    ),
]

# Test scenarios for download flow
DOWNLOAD_TEST_CASES: List[DownloadTestCase] = [
    DownloadTestCase(
        name="no_ext",
        suffix="",
    ),
    DownloadTestCase(
        name="correct_ext",
        suffix=".{format}",
    ),
    DownloadTestCase(
        name="wrong_ext",
        suffix=".{wrong_ext}",
        expected_status_code=404,
        should_succeed=False,
    ),
]


@override_settings(UPLOAD_DIR=settings.BASE_DIR / "test_uploads_e2e")
class APIUploadE2ETest(TestCase):
    """
    End-to-end tests for complete API upload and retrieval flow.

    Tests the full user journey from binary upload to file retrieval:
    - Multipart form upload to /api/upload/
    - Hash-based filename generation
    - Physical file persistence to UPLOAD_DIR
    - Database record creation (Item + PicItem)
    - Metadata retrieval via /{shortcode}/details endpoint
    - Content integrity verification (uploaded bytes == saved bytes)
    """

    def setUp(self):
        self.client = Client()
        self.upload_url = reverse("api_upload")
        self.user = User.objects.create_user(username="e2e_test", password="test123")
        self.client.force_login(self.user)
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(exist_ok=True)

    def tearDown(self):
        """Clean up test files and directories"""
        if self.upload_dir.exists():
            for file in self.upload_dir.iterdir():
                if file.is_file():
                    file.unlink()
            self.upload_dir.rmdir()

    def _execute_upload_flow(self, test_case: UploadTestCase):
        """
        Execute complete upload and retrieval flow for a test case.

        Steps:
        1. POST file data to /api/upload/ as multipart form
        2. Verify response with X-Code and X-Format headers
        3. Verify file saved to UPLOAD_DIR/{hash}.{format}
        4. GET /{shortcode}/details to retrieve metadata
        5. Verify shortcode appears in details page
        6. Verify saved content matches uploaded bytes

        Args:
            test_case: UploadTestCase defining file data and expectations

        Raises:
            AssertionError: If any step fails with test_case.fail_msg
        """
        with self.subTest(test_case=test_case.name):
            # Step 1: Upload file via API
            file = SimpleUploadedFile(
                test_case.filename,
                test_case.data,
                content_type=test_case.ctype,
            )
            upload_response = self.client.post(self.upload_url, {"content": file})

            # Verify expected status code
            self.assertEqual(
                upload_response.status_code,
                test_case.status,
                f"{test_case.fail_msg} - Expected {test_case.status}, got {upload_response.status_code}",
            )

            # If this is a failure case, verify error message and return early
            if not test_case.succeed:
                if test_case.err_msg:
                    self.assertIn(
                        test_case.err_msg.encode(),
                        upload_response.content,
                        f"{test_case.fail_msg} - Expected error message '{test_case.err_msg}' not found",
                    )
                return  # Don't proceed for failure cases

            # Step 2: Verify response headers and extract metadata
            self.assertIn(
                "X-Code",
                upload_response,
                f"{test_case.fail_msg} - Missing X-Code header",
            )
            self.assertIn(
                "X-Format",
                upload_response,
                f"{test_case.fail_msg} - Missing X-Format header",
            )

            shortcode = upload_response["X-Code"]
            format_returned = upload_response["X-Format"]
            filename_returned = upload_response.content.decode("utf-8")

            self.assertEqual(
                format_returned,
                test_case.fmt,
                f"{test_case.fail_msg} - Wrong format in X-Format header",
            )
            self.assertTrue(
                filename_returned.endswith(f".{test_case.fmt}"),
                f"{test_case.fail_msg} - Returned filename has wrong extension",
            )

            # Step 3: Verify physical file persistence
            file_path = self.upload_dir / filename_returned
            self.assertTrue(
                file_path.exists(),
                f"{test_case.fail_msg} - File not saved to disk at {file_path}",
            )

            # Step 4: Retrieve file metadata via shortcode details
            details_url = f"/{shortcode}/details"
            details_response = self.client.get(details_url)
            self.assertEqual(
                details_response.status_code,
                200,
                f"{test_case.fail_msg} - Details page request failed",
            )
            self.assertIn(
                shortcode.encode(),
                details_response.content,
                f"{test_case.fail_msg} - Shortcode not found in details page",
            )

            # Step 5: Test download functionality with different URL patterns
            self._test_download_patterns(shortcode, test_case)

            # Step 6: Verify disk file content integrity
            with open(file_path, "rb") as f:
                saved_data = f.read()
            self.assertEqual(
                saved_data,
                test_case.data,
                f"{test_case.fail_msg} - Saved file content doesn't match uploaded data",
            )

    def _test_download_patterns(self, shortcode: str, upload_test_case: UploadTestCase):
        """
        Test all download URL patterns for a given shortcode.

        Args:
            shortcode: The shortcode to test downloads for
            upload_test_case: The original upload test case for context
        """
        for download_case in DOWNLOAD_TEST_CASES:
            with self.subTest(download_case=download_case.name, shortcode=shortcode):
                # Build URL with suffix
                download_url = download_case.build_url(shortcode, upload_test_case.fmt)

                # Make download request
                download_response = self.client.get(download_url)

                # Verify expected status code
                self.assertEqual(
                    download_response.status_code,
                    download_case.expected_status_code,
                    f"Download {download_case.name} failed - Expected {download_case.expected_status_code}, got {download_response.status_code}",
                )

                # If download should succeed, verify content and headers
                if download_case.should_succeed:
                    # Verify content matches original upload
                    self.assertEqual(
                        download_response.content,
                        upload_test_case.data,
                        f"Download {download_case.name} failed - Downloaded file content doesn't match uploaded data",
                    )

                    # Verify Content-Type header if expected
                    if upload_test_case.mime:
                        self.assertEqual(
                            download_response.get("Content-Type"),
                            upload_test_case.mime,
                            f"Download {download_case.name} failed - Wrong Content-Type header",
                        )

    def test_upload_retrieval_flows(self):
        """Test all upload scenarios using data-driven approach"""
        for test_case in UPLOAD_TEST_CASES:
            self._execute_upload_flow(test_case)
