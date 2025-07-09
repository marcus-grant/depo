from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from core.models import Item, PicItem
import hashlib


class RawDownloadViewTests(TestCase):
    """Unit tests for raw file download functionality"""

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
        # Create test data explicitly
        item = Item.objects.create(code="TESTCODE", hash="REMAININGHASH", ctype="pic")

        pic_item = PicItem.objects.create(
            item=item,
            format="png",
            size=70,  # Size of a minimal PNG
        )

        # Make request
        response = self.client.get("/raw/TESTCODE")

        # Assert success
        self.assertEqual(response.status_code, 200)

    def test_download_nonexistent_shortcode_returns_404(self):
        """Test that downloading with invalid shortcode returns 404"""
        # Make request for non-existent shortcode
        response = self.client.get("/raw/DOESNOTEXIST")

        # Assert 404
        self.assertEqual(response.status_code, 404)
    
    def test_download_with_correct_extension(self):
        """Test that downloading with shortcode + correct extension works"""
        # Create test data
        item = Item.objects.create(code="TESTCODE", hash="REMAININGHASH", ctype="pic")
        pic_item = PicItem.objects.create(
            item=item,
            format="png",
            size=70,
        )
        
        # Test with correct extension
        response = self.client.get("/raw/TESTCODE.png")
        self.assertEqual(response.status_code, 200)
        
        # Test without extension still works
        response_no_ext = self.client.get("/raw/TESTCODE")
        self.assertEqual(response_no_ext.status_code, 200)
    
    def test_download_returns_actual_file_content(self):
        """Test that downloading returns the actual file bytes"""
        # Create test image data
        test_image = b'\x89PNG\r\n\x1a\n' + b'\x00' * 20  # Minimal PNG header
        
        # We need to create the file on disk for the view to serve
        # This is where we need to understand how files are stored...

