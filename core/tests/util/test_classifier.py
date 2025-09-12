# core/tests/util/test_classifier.py
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.test import TestCase
from unittest.mock import patch, MagicMock

from core.util.classifier import (
    ContentClass,
    classify_content,
    _classify_content_bytes,
    _classify_pic_format,
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
