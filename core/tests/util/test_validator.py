from django.core.files.uploadedfile import InMemoryUploadedFile
from django.test import TestCase, override_settings
from io import BytesIO

import core.util.validator as validator
import core.tests.fixtures as fixtures


class TestFileEmpty(TestCase):
    """Unit tests for file_empty function"""

    def test_file_empty_with_content(self):
        """Test that files with content return False"""
        result = validator.file_empty(b"some file content")
        self.assertFalse(result)

    def test_file_empty_with_empty_bytes(self):
        """Test that empty byte strings return True"""
        result = validator.file_empty(b"")
        self.assertTrue(result)

    def test_file_empty_with_none(self):
        """Test that None values return True"""
        result = validator.file_empty(None)
        self.assertTrue(result)


class TestContentTooBig(TestCase):
    """Unit tests for content_too_big function"""

    def _create_test_data(self, content: bytes) -> dict:
        return {
            "bytes": content,
            "str": content.decode("utf-8", errors="ignore"),
            "file": fixtures.create_inmem_file(content),
        }

    @override_settings(MAX_UPLOAD_SIZE=100)
    def test_none_always_false(self):
        """None is a possible input and empty content, should always be False"""
        self.assertFalse(validator.content_too_big(None))

    @override_settings(MAX_UPLOAD_SIZE=100)
    def test_empta_data(self):
        """Empty data types (b"", "", inmem.size=0) should always return False"""
        tests_input = self._create_test_data(b"")
        for dtype, data in tests_input.items():
            with self.subTest(f"Testing with data type: {dtype}"):
                self.assertFalse(validator.content_too_big(data))

    @override_settings(MAX_UPLOAD_SIZE=100)
    def test__with_undersized_data(self):
        """Test that files smaller than max size return False"""
        tests_input = self._create_test_data(b"tiny data")
        for dtype, data in tests_input.items():
            with self.subTest(f"Testing with data type: {dtype}"):
                self.assertFalse(validator.content_too_big(data))

    @override_settings(MAX_UPLOAD_SIZE=100)
    def test_oversied_data(self):
        """Test that data larger than max size return True"""
        tests_input = self._create_test_data(b"A" * 101)
        for dtype, data in tests_input.items():
            with self.subTest(f"Testing with data type: {dtype}"):
                self.assertTrue(validator.content_too_big(data))

    @override_settings(MAX_UPLOAD_SIZE=100)
    def test_data_at_limit(self):
        """Test that data exactly at max size return False"""
        tests_input = self._create_test_data(b"A" * 100)
        for dtype, data in tests_input.items():
            with self.subTest(f"Testing with data type: {dtype}"):
                self.assertFalse(validator.content_too_big(data))


class TestLooksLikeUrl(TestCase):
    """Unit tests for looks_like_url function"""

    def test_looks_like_url_with_scheme(self):
        """Test URL detection for strings with explicit schemes"""
        self.assertTrue(validator.looks_like_url("https://example.com"))
        self.assertTrue(validator.looks_like_url("http://example.com"))
        self.assertTrue(validator.looks_like_url("ftp://files.example.com"))
        self.assertTrue(validator.looks_like_url("https://sub.domain.com/path"))

    def test_looks_like_url_without_scheme(self):
        """Test URL detection for domain-like strings without schemes"""
        self.assertTrue(validator.looks_like_url("example.com"))
        self.assertTrue(validator.looks_like_url("www.example.com"))
        self.assertTrue(validator.looks_like_url("sub.domain.co.uk"))
        self.assertTrue(validator.looks_like_url("api.service.io"))

    def test_looks_like_url_false_cases(self):
        """Test that non-URL strings return False"""
        self.assertFalse(validator.looks_like_url("Hello world"))
        self.assertFalse(validator.looks_like_url("just text"))
        self.assertFalse(validator.looks_like_url("no.dots.but.not.a.url really"))
        self.assertFalse(validator.looks_like_url(""))
        self.assertFalse(validator.looks_like_url("   "))
        self.assertFalse(validator.looks_like_url(None))


class TestFileType(TestCase):
    """Unit tests for file_type function"""

    def test_file_type_jpg_bytes(self):
        """Test that JPEG magic bytes are detected"""

        jpeg_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF"

        result = validator.file_type(jpeg_bytes)

        self.assertEqual(result, "jpg")

    def test_file_type_png_bytes(self):
        """Test that PNG magic bytes are detected"""

        png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"

        result = validator.file_type(png_bytes)

        self.assertEqual(result, "png")

    def test_file_type_invalid_bytes(self):
        """Test that invalid file bytes return None"""
        invalid_bytes = b"Not an image file"
        result = validator.file_type(invalid_bytes)
        self.assertIsNone(result)


class TestIsBase64ImageFormat(TestCase):
    """Unit tests for is_base64_image_format function"""

    def test_valid_png_format_returns_true(self):
        """Test that valid PNG data URI format returns True"""
        result = validator.is_base64_image_format(fixtures.PNG_BASE64_DATA_URI)
        self.assertTrue(result)

    def test_valid_jpeg_format_returns_true(self):
        """Test that valid JPEG data URI format returns True"""
        result = validator.is_base64_image_format(fixtures.JPEG_BASE64_DATA_URI)
        self.assertTrue(result)

    def test_unsupported_format_returns_false(self):
        """Test that unsupported data URI format returns False"""
        content = "data:text/plain;base64,SGVsbG8gV29ybGQ="
        result = validator.is_base64_image_format(content)
        self.assertFalse(result)

    def test_no_data_uri_prefix_returns_false(self):
        """Test that content without data URI prefix returns False"""
        result = validator.is_base64_image_format(fixtures.PNG_BASE64)
        self.assertFalse(result)


class TestIsWithinBase64SizeLimit(TestCase):
    """Unit tests for is_within_base64_size_limit function"""

    def test_content_under_limit_returns_true(self):
        """Test that content under size limit returns True"""
        with override_settings(DEPO_MAX_BASE64_SIZE=1024 * 1024):  # 1MB
            content = fixtures.PNG_BASE64_DATA_URI
            result = validator.is_within_base64_size_limit(content)
            self.assertTrue(result)

    @override_settings(DEPO_MAX_BASE64_SIZE=8)  # Very small limit
    def test_content_over_limit_returns_false(self):
        """Test that content over size limit returns False"""
        content = fixtures.PNG_BASE64_DATA_URI
        result = validator.is_within_base64_size_limit(content)
        self.assertFalse(result)

    def test_content_equal_to_limit_returns_true(self):
        """Test that content exactly at size limit returns True"""
        data = fixtures.PNG_BASE64_DATA_URI
        with override_settings(DEPO_MAX_BASE64_SIZE=len(data)):
            result = validator.is_within_base64_size_limit(data)
            self.assertTrue(result)
