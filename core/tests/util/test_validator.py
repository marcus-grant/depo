from django.test import TestCase

from core.util.validator import looks_like_url, validate_upload_bytes, file_empty


class TestFileEmpty(TestCase):
    """Unit tests for file_empty function"""

    def test_file_empty_with_content(self):
        """Test that files with content return False"""
        result = file_empty(b"some file content")
        self.assertFalse(result)

    def test_file_empty_with_empty_bytes(self):
        """Test that empty byte strings return True"""
        result = file_empty(b"")
        self.assertTrue(result)

    def test_file_empty_with_none(self):
        """Test that None values return True"""
        result = file_empty(None)
        self.assertTrue(result)


class TestLooksLikeUrl(TestCase):
    """Unit tests for looks_like_url function"""

    def test_looks_like_url_with_scheme(self):
        """Test URL detection for strings with explicit schemes"""
        self.assertTrue(looks_like_url("https://example.com"))
        self.assertTrue(looks_like_url("http://example.com"))
        self.assertTrue(looks_like_url("ftp://files.example.com"))
        self.assertTrue(looks_like_url("https://sub.domain.com/path"))

    def test_looks_like_url_without_scheme(self):
        """Test URL detection for domain-like strings without schemes"""
        self.assertTrue(looks_like_url("example.com"))
        self.assertTrue(looks_like_url("www.example.com"))
        self.assertTrue(looks_like_url("sub.domain.co.uk"))
        self.assertTrue(looks_like_url("api.service.io"))

    def test_looks_like_url_false_cases(self):
        """Test that non-URL strings return False"""
        self.assertFalse(looks_like_url("Hello world"))
        self.assertFalse(looks_like_url("just text"))
        self.assertFalse(looks_like_url("no.dots.but.not.a.url really"))
        self.assertFalse(looks_like_url(""))
        self.assertFalse(looks_like_url("   "))
        self.assertFalse(looks_like_url(None))


class TestValidateUploadBytes(TestCase):
    """Unit tests for validate_upload_bytes function"""

    def test_validate_jpg_bytes(self):
        """Test that JPEG magic bytes are detected"""
        
        jpeg_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF"
        
        result = validate_upload_bytes(jpeg_bytes)
        
        self.assertEqual(result, "jpg")

    def test_validate_png_bytes(self):
        """Test that PNG magic bytes are detected"""
        
        png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
        
        result = validate_upload_bytes(png_bytes)
        
        self.assertEqual(result, "png")

