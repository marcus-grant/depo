from django.test import TestCase, override_settings

import core.util.validator as validator
import core.tests.fixtures as fixtures


def _create_test_data(content: bytes) -> dict:
    """Creates test data in three types.Content datatypes"""
    return {
        "bytes": content,
        "str": content.decode("utf-8", errors="ignore"),
        "file": fixtures.create_inmem_file(content),
    }


class TestFileEmpty(TestCase):
    """Unit tests for file_empty function"""

    def test_none(self):
        """Test that None values return True"""
        self.assertTrue(validator.content_empty(None))

    def test_empty_content(self):
        """Test that empty byte strings return True"""
        for dtype, data in _create_test_data(b"").items():
            with self.subTest(f"Testing with data type: {dtype}"):
                self.assertTrue(validator.content_empty(data))

    def test_with_valid_content(self):
        """Test that content data types with content return False"""
        for dtype, data in _create_test_data(b"This is non-empty content").items():
            with self.subTest(f"Testing with data type: {dtype}"):
                self.assertFalse(validator.content_empty(data))


class TestContentTooBig(TestCase):
    """Unit tests for content_too_big function"""

    @override_settings(MAX_UPLOAD_SIZE=100)
    def test_none_always_false(self):
        """None is a possible input and empty content, should always be False"""
        self.assertFalse(validator.content_too_big(None))

    @override_settings(MAX_UPLOAD_SIZE=100)
    def test_empta_data(self):
        """Empty data types (b"", "", inmem.size=0) should always return False"""
        tests_input = _create_test_data(b"")
        for dtype, data in tests_input.items():
            with self.subTest(f"Testing with data type: {dtype}"):
                self.assertFalse(validator.content_too_big(data))

    @override_settings(MAX_UPLOAD_SIZE=100)
    def test__with_undersized_data(self):
        """Test that files smaller than max size return False"""
        tests_input = _create_test_data(b"tiny data")
        for dtype, data in tests_input.items():
            with self.subTest(f"Testing with data type: {dtype}"):
                self.assertFalse(validator.content_too_big(data))

    @override_settings(MAX_UPLOAD_SIZE=100)
    def test_oversied_data(self):
        """Test that data larger than max size return True"""
        tests_input = _create_test_data(b"A" * 101)
        for dtype, data in tests_input.items():
            with self.subTest(f"Testing with data type: {dtype}"):
                self.assertTrue(validator.content_too_big(data))

    @override_settings(MAX_UPLOAD_SIZE=100)
    def test_data_at_limit(self):
        """Test that data exactly at max size return False"""
        tests_input = _create_test_data(b"A" * 100)
        for dtype, data in tests_input.items():
            with self.subTest(f"Testing with data type: {dtype}"):
                self.assertFalse(validator.content_too_big(data))


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
