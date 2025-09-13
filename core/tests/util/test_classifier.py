# core/tests/util/test_classifier.py
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.test import TestCase
from unittest.mock import patch, MagicMock

from core.util.classifier import (
    ContentClass,
    classify_content,
    _classify_content_bytes,
    _classify_pic_format,
    _classify_content_string,
    is_url,
)
import core.tests.fixtures as fixtures


class TestClassifyPicFormat(TestCase):
    """Test _detect_image_format helper function"""

    def test_detects_image_formats(self):
        """Test all supported image format magic numbers"""
        test_cases = [
            (b"\x89PNG\r\n\x1a\n", "png"),
            (b"\xff\xd8\xff\xe0", "jpg"),
            (b"\xff\xd8\xff\xe1", "jpg"),
            (b"\xff\xd8\xff\xdb", "jpg"),
            (b"GIF8", "gif"),
        ]

        for content, expected in test_cases:
            with self.subTest(format=expected, content=content[:4]):
                result = _classify_pic_format(content)
                self.assertEqual(result, expected)

    def test_unrecognized_bytes_returns_none(self):
        """Test that unrecognized bytes return None"""
        content = b"\x00\x01\x02\x03\xde\xad\xbe\xef"
        self.assertIsNone(_classify_pic_format(content))


class TestClassifyContentBytes(TestCase):
    """Test _classify_content_bytes function"""

    def test_returns_empty_content_class_for_empty_bytes(self):
        """Test that empty bytes returns default ContentClass"""
        self.assertEqual(_classify_content_bytes(b""), ContentClass())

    @patch("core.util.classifier._classify_pic_format")
    def test_calls_classify_pic_format(self, mock):
        """Test that _classify_pic_format called with content & gives valid ContentClass"""
        mock.return_value = "png"
        result = _classify_content_bytes(fixtures.PNG_DATA)
        mock.assert_called_once_with(fixtures.PNG_DATA)
        self.assertEqual(result, ContentClass(ctype="pic", ext="png"))


class TestIsUrl(TestCase):
    """Test that various URL schemes are detected correctly"""

    def test_valid_schemes(self):
        """Test browser-accessible URL schemes are detected"""
        valid_urls = [
            "https://example.com",
            "http://example.com",
            "HTTPS://EXAMPLE.COM",  # Case insensitive
            "Http://Example.Com",  # Mixed case
            "  https://example.com  ",  # Whitespace stripped
            "https://example.com\n",  # Trailing newline
            "\t\thttps://example.com\t\n",  # Mixed whitespace
        ]
        for url in valid_urls:
            with self.subTest(url=url):
                self.assertTrue(is_url(url))

    def test_domain_formats(self):
        """Test valid domain formats without schemes"""
        valid_domains = [
            "example.com",
            "example.net",
            "www.example.org",
            "sub.domain.co.uk",
            "api.service.io",
            "cdn.assets.example.edu",  # 3 subdomains (max depth)
            "example.com:8080",  # With port
            "www.example.gov:443",  # www with port
            "blog.company.tech:3000",  # Subdomain with port
            "  example.info  ",  # Whitespace stripped
            "EXAMPLE.COM",  # Case insensitive
            "Sub.Domain.CO.UK",  # Mixed case
        ]
        for domain in valid_domains:
            with self.subTest(domain=domain):
                self.assertTrue(is_url(domain))

    def test_invalid_formats(self):
        """Test that invalid formats return False"""
        invalid_cases = [
            # URLs embedded in text (not standalone)
            "Check out https://example.com for more info",
            "https://example.com is great",
            "Visit example.com today!",
            # Single words / localhost
            "localhost",
            "database",
            "server",
            # Invalid formats
            "example..com",  # Double dots
            "example.com/path with spaces",  # Spaces in path
            ".example.com",  # Leading dot
            "example.com.",  # Trailing dot
            "example",  # No TLD
            "",  # Empty
            "   ",  # Just whitespace
            # Invalid ports
            "example.com:0",  # Port 0
            "example.com:99999",  # Port too high
            "example.com:abc",  # Non-numeric port
        ]

        for invalid_case in invalid_cases:
            with self.subTest(case=invalid_case):
                self.assertFalse(is_url(invalid_case))


class TestClassifyContentString(TestCase):
    """Test _classify_content_string function"""

    def test_classifies_plaintext(self):
        """Test that plain text content is classified as text"""
        content = "This is just plain text content\nHello, World!"
        result = _classify_content_string(content)
        self.assertEqual(result, ContentClass(ctype="txt"))

    @patch("core.util.classifier.is_url")
    def test_classifies_url_content(self, mock_url):
        """Test that URL detection routes correctly to helper"""
        mock_url.return_value = True
        result = _classify_content_string("https://example.com")
        mock_url.assert_called_once_with("https://example.com")
        self.assertEqual(result, ContentClass(ctype="url"))


class TestClassifyContent(TestCase):
    """Test main classify_content function - mock the helpers"""

    @patch("core.util.classifier._classify_content_bytes")
    def test_routes_bytes_content(self, mock):
        """Test that bytes content routes to bytes classifier"""
        mock.return_value = ContentClass(ctype="pic", ext="png")
        result = classify_content(fixtures.PNG_DATA)
        mock.assert_called_once_with(fixtures.PNG_DATA)
        self.assertEqual(result, ContentClass(ctype="pic", ext="png"))

    @patch("core.util.classifier._classify_content_bytes")
    def test_classifies_uploaded_file_content(self, mock_class):
        """Test that InMemoryUploadedFile routes to bytes classifier with proper file handling"""
        mock_class.return_value = ContentClass(ctype="pic", ext="png")
        # Create mock file
        mock_file = MagicMock(spec=InMemoryUploadedFile)
        mock_file.read.return_value = b"\x89PNG\r\n\x1a\n"
        result = classify_content(mock_file)
        # Verify file operations
        mock_file.seek.assert_any_call(0)  # Seek to start
        mock_file.read.assert_called_once()
        mock_file.seek.assert_called_with(0)  # Reset after read
        # Verify bytes classifier called with file content
        mock_class.assert_called_once_with(b"\x89PNG\r\n\x1a\n")
        self.assertEqual(result.ctype, "pic")
