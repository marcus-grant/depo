from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from pathlib import Path
from core.models import Item, PicItem
import hashlib


class RawDownloadViewTests(TestCase):
    """Unit tests for raw file download functionality"""

    def setUp(self):
        """Set up test data"""
        self.test_code = "TESTCODE"
        self.test_hash = "REMA1N1NGHASH"
        self.test_format = "png"
        self.test_size = 70
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(exist_ok=True)

    def tearDown(self):
        """Clean up test files"""
        # Clean up any test files in upload directory
        if self.upload_dir.exists():
            for file in self.upload_dir.glob(f"{self.test_code}.*"):
                file.unlink()

    def _create_test_item_and_file(self, content=b"test"):
        """Helper to create test Item, PicItem and file on disk"""
        # Create database records
        item = Item.objects.create(
            code=self.test_code, hash=self.test_hash, ctype="pic"
        )
        pic_item = PicItem.objects.create(
            item=item,
            format=self.test_format,
            size=self.test_size,
        )

        # Create file on disk
        test_file = self.upload_dir / f"{item.code}.{pic_item.format}"
        test_file.write_bytes(content)

        return item, pic_item, test_file

    def test_raw_download_url_pattern_exists(self):
        """Test that /raw/{shortcode} URL pattern is routable"""
        response = self.client.get("/raw/ABC123")
        # Should return a valid HTTP response (not 500 internal error)
        self.assertLess(
            response.status_code,
            500,
            "URL pattern should resolve without server errors",
        )

    def test_download_existing_shortcode_returns_200(self):
        """Test that downloading with valid shortcode returns 200"""
        item, pic_item, test_file = self._create_test_item_and_file()

        # Make request
        response = self.client.get(f"/raw/{self.test_code}")

        # Assert success
        self.assertEqual(response.status_code, 200)

    def test_download_with_correct_extension(self):
        """Test that downloading with shortcode + correct extension works"""
        item, pic_item, test_file = self._create_test_item_and_file()

        # Test with correct extension
        response = self.client.get(f"/raw/{self.test_code}.{self.test_format}")
        self.assertEqual(response.status_code, 200)

        # Test without extension still works
        response_no_ext = self.client.get(f"/raw/{self.test_code}")
        self.assertEqual(response_no_ext.status_code, 200)

    def test_download_returns_actual_file_content(self):
        """Test that downloading returns the actual file bytes"""
        # Create test image data
        test_image = b"\x89PNG\r\n\x1a\n" + b"\x00" * 20  # Minimal PNG header

        item, pic_item, test_file = self._create_test_item_and_file(test_image)

        # Make request
        response = self.client.get(f"/raw/{self.test_code}")

        # Assert we get the actual file content
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, test_image)

    def test_download_returns_correct_content_type(self):
        """Test that downloading returns correct Content-Type header"""
        item, pic_item, test_file = self._create_test_item_and_file()

        # Make request
        response = self.client.get(f"/raw/{self.test_code}")

        # Assert correct Content-Type
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], f"image/{self.test_format}")

    def test_download_wrong_extension_returns_404(self):
        """Test that downloading with wrong extension returns 404"""
        item, pic_item, test_file = self._create_test_item_and_file()

        # Request with wrong extension (jpg instead of png)
        wrong_ext = "jpg" if self.test_format == "png" else "png"
        response = self.client.get(f"/raw/{self.test_code}.{wrong_ext}")

        # Assert 404
        self.assertEqual(response.status_code, 404)

    def test_download_nonexistent_shortcode_returns_404(self):
        """Test that downloading with invalid shortcode returns 404"""
        # Make request for non-existent shortcode
        response = self.client.get("/raw/DOESNOTEXIST")

        # Assert 404
        self.assertEqual(response.status_code, 404)
