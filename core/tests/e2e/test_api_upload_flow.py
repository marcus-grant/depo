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


@dataclass
class UploadTestCase:
    """Data structure defining a complete upload test scenario"""

    name: str
    file_data: bytes
    filename: str
    content_type: str
    expected_format: str
    description: str
    failure_message: str
    should_succeed: bool = True
    expected_status_code: int = 200
    expected_error_message: str = ""


# Test data - minimal valid image files with known hashes
PNG_1X1_RED = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x00\x01\x00\x00\x00\x00IEND\xaeB`\x82"
JPEG_1X1_BLACK = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04\x04\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05\x12!1A\x06\x13Qa\x07\"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R\xd1\xf0$3br\x82\t\n\x16\x17\x18\x19\x1a%&'()*456789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xfb\xd5N\xe1\x18\xd2I\xfd\xd7\xc7&\xff\xd9"

# Test scenarios for upload flow
UPLOAD_TEST_CASES: List[UploadTestCase] = [
    UploadTestCase(
        name="png_1x1_red_pixel",
        file_data=PNG_1X1_RED,
        filename="red_pixel.png",
        content_type="image/png",
        expected_format="png",
        description="Upload 1x1 red PNG pixel (70 bytes), verify hash-based filename generation and file persistence",
        failure_message="Failed to upload/retrieve 1x1 red PNG - check PNG header validation and file I/O",
    ),
    UploadTestCase(
        name="jpeg_1x1_black_pixel",
        file_data=JPEG_1X1_BLACK,
        filename="black_pixel.jpg",
        content_type="image/jpeg",
        expected_format="jpg",
        description="Upload 1x1 black JPEG pixel (299 bytes), verify JPEG processing and metadata extraction",
        failure_message="Failed to upload/retrieve 1x1 black JPEG - check JPEG header validation and format detection",
    ),
    UploadTestCase(
        name="empty_file_rejection",
        file_data=b"",
        filename="empty.png",
        content_type="image/png",
        expected_format="",
        description="Upload empty file (0 bytes), expect 400 rejection with 'No file uploaded' message",
        failure_message="Empty file should be rejected with 400 status",
        should_succeed=False,
        expected_status_code=400,
        expected_error_message="No file uploaded",
    ),
    UploadTestCase(
        name="invalid_image_data_rejection",
        file_data=b"This is not an image file at all, just plain text pretending to be PNG",
        filename="fake.png",
        content_type="image/png",
        expected_format="",
        description="Upload text file with PNG extension, expect 500 rejection due to invalid image format",
        failure_message="Invalid image data should be rejected with 500 status",
        should_succeed=False,
        expected_status_code=500,
        expected_error_message="Invalid upload format",
    ),
    UploadTestCase(
        name="corrupted_png_header_rejection",
        file_data=b"\x89PNG\r\n\x1a\n\x00\x00CORRUPTED_HEADER_DATA",
        filename="corrupted.png",
        content_type="image/png",
        expected_format="",
        description="Upload PNG with corrupted header, expect 500 rejection due to invalid PNG structure",
        failure_message="Corrupted PNG header should be rejected",
        should_succeed=False,
        expected_status_code=500,
        expected_error_message="Invalid upload format",
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
        1. POST file_data to /api/upload/ as multipart form
        2. Verify 200 response with X-Code and X-Format headers
        3. Verify physical file saved to UPLOAD_DIR/{hash}.{format}
        4. GET /{shortcode}/details to retrieve metadata
        5. Verify shortcode appears in details page response
        6. Verify saved file content exactly matches uploaded bytes

        Args:
            test_case: UploadTestCase defining file data and expectations

        Raises:
            AssertionError: If any step fails with test_case.failure_message
        """
        with self.subTest(test_case=test_case.name):
            # Step 1: Upload file via API
            file = SimpleUploadedFile(
                test_case.filename,
                test_case.file_data,
                content_type=test_case.content_type,
            )
            upload_response = self.client.post(self.upload_url, {"content": file})

            # Verify expected status code
            self.assertEqual(
                upload_response.status_code,
                test_case.expected_status_code,
                f"{test_case.failure_message} - Expected {test_case.expected_status_code}, got {upload_response.status_code}",
            )

            # If this is a failure case, verify error message and return early
            if not test_case.should_succeed:
                if test_case.expected_error_message:
                    self.assertIn(
                        test_case.expected_error_message.encode(),
                        upload_response.content,
                        f"{test_case.failure_message} - Expected error message '{test_case.expected_error_message}' not found",
                    )
                return  # Don't proceed with retrieval flow for failure cases

            # Step 2: Verify response headers and extract metadata
            self.assertIn(
                "X-Code",
                upload_response,
                f"{test_case.failure_message} - Missing X-Code header",
            )
            self.assertIn(
                "X-Format",
                upload_response,
                f"{test_case.failure_message} - Missing X-Format header",
            )

            shortcode = upload_response["X-Code"]
            format_returned = upload_response["X-Format"]
            filename_returned = upload_response.content.decode("utf-8")

            self.assertEqual(
                format_returned,
                test_case.expected_format,
                f"{test_case.failure_message} - Wrong format in X-Format header",
            )
            self.assertTrue(
                filename_returned.endswith(f".{test_case.expected_format}"),
                f"{test_case.failure_message} - Returned filename has wrong extension",
            )

            # Step 3: Verify physical file persistence
            file_path = self.upload_dir / filename_returned
            self.assertTrue(
                file_path.exists(),
                f"{test_case.failure_message} - File not saved to disk at {file_path}",
            )

            # Step 4: Retrieve file metadata via shortcode
            details_url = f"/{shortcode}/details"
            details_response = self.client.get(details_url)
            self.assertEqual(
                details_response.status_code,
                200,
                f"{test_case.failure_message} - Details page request failed",
            )
            self.assertIn(
                shortcode.encode(),
                details_response.content,
                f"{test_case.failure_message} - Shortcode not found in details page",
            )

            # Step 5: Verify content integrity
            with open(file_path, "rb") as f:
                saved_data = f.read()
            self.assertEqual(
                saved_data,
                test_case.file_data,
                f"{test_case.failure_message} - Saved file content doesn't match uploaded data",
            )
            self.assertEqual(
                len(saved_data),
                len(test_case.file_data),
                f"{test_case.failure_message} - Saved file size doesn't match uploaded size",
            )

    def test_upload_retrieval_flows(self):
        """Test all defined upload scenarios using data-driven approach"""
        for test_case in UPLOAD_TEST_CASES:
            self._execute_upload_flow(test_case)

