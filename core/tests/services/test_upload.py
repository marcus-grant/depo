from django.test import TestCase
from django.conf import settings
from unittest.mock import patch

from core.services.upload import handle_file_upload


class TestHandleFileUpload(TestCase):
    """Unit tests for handle_file_upload service function"""

    def test_handle_file_upload_with_empty_file(self):
        """Test that empty files return appropriate error"""
        file_data = b""

        result = handle_file_upload(file_data)

        self.assertFalse(result.success)
        self.assertEqual(result.error_type, "empty_file")
        self.assertIsNone(result.item)

    @patch("core.services.upload.file_type")
    def test_handle_file_upload_with_invalid_file_type(self, mock_file_type):
        """Test that files with invalid type return appropriate error"""
        mock_file_type.return_value = None
        file_data = b"Not an image file"

        result = handle_file_upload(file_data)

        mock_file_type.assert_called_once_with(file_data)
        self.assertFalse(result.success)
        self.assertEqual(result.error_type, "invalid_file_type")
        self.assertIsNone(result.item)

    @patch("core.services.upload.file_too_big")
    def test_handle_file_upload_with_oversized_file(self, mock_file_too_big):
        """Test that oversized files return appropriate error"""
        mock_file_too_big.return_value = True
        file_data = b"A" * (settings.MAX_UPLOAD_SIZE + 1)

        result = handle_file_upload(file_data)

        mock_file_too_big.assert_called_once_with(file_data)
        self.assertFalse(result.success)
        self.assertEqual(result.error_type, "file_too_big")
        self.assertIsNone(result.item)
