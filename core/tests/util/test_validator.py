from django.test import TestCase

from core.util.validator import looks_like_url, file_type, file_empty, file_too_big, file_type_invalid


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


class TestFileTooBig(TestCase):
    """Unit tests for file_too_big function"""

    def test_file_too_big_with_small_file(self):
        """Test that files smaller than max size return False"""
        file_data = b"small file"
        max_size = 100
        result = file_too_big(file_data, max_size)
        self.assertFalse(result)

    def test_file_too_big_with_oversized_file(self):
        """Test that files larger than max size return True"""
        file_data = b"A" * 101
        max_size = 100
        result = file_too_big(file_data, max_size)
        self.assertTrue(result)

    def test_file_too_big_at_exact_limit(self):
        """Test that files exactly at max size return False"""
        file_data = b"A" * 100
        max_size = 100
        result = file_too_big(file_data, max_size)
        self.assertFalse(result)


class TestFileTypeInvalid(TestCase):
    """Unit tests for file_type_invalid function"""

    def test_file_type_invalid_with_valid_jpg(self):
        """Test that valid JPEG files return False"""
        jpeg_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF"
        result = file_type_invalid(jpeg_bytes)
        self.assertFalse(result)

    def test_file_type_invalid_with_invalid_file(self):
        """Test that invalid file types return True"""
        invalid_bytes = b"Not an image file"
        result = file_type_invalid(invalid_bytes)
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


class TestFileType(TestCase):
    """Unit tests for file_type function"""

    def test_file_type_jpg_bytes(self):
        """Test that JPEG magic bytes are detected"""
        
        jpeg_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF"
        
        result = file_type(jpeg_bytes)
        
        self.assertEqual(result, "jpg")

    def test_file_type_png_bytes(self):
        """Test that PNG magic bytes are detected"""
        
        png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
        
        result = file_type(png_bytes)
        
        self.assertEqual(result, "png")

