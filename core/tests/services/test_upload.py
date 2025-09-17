from django.test import TestCase
from django.conf import settings
from unittest.mock import patch

from core.services.upload import handle_file_upload, UploadResult
from core.util.classifier import ContentClass

MODSTR = "core.services.upload"


def _upld_res(success, err, item) -> UploadResult:
    return UploadResult(success=success, error_type=err, item=item)


def _class(ctype, b64, ext):
    """Alias factory to shorten expected value generation"""
    return ContentClass(ctype=ctype, b64=b64, ext=ext)


class TestHandleFileUpload(TestCase):
    """Unit tests for handle_file_upload service function"""

    @patch(f"{MODSTR}.content_empty", return_value=True)
    def test_handle_file_upload_with_empty_file(self, mock_file_empty):
        """Test that empty files return appropriate error"""
        expect = _upld_res(False, "empty_file", None)
        result = handle_file_upload(b"")
        mock_file_empty.assert_called_once_with(b"")
        self.assertEqual(result, expect)

    @patch(f"{MODSTR}.content_too_big", return_value=True)
    def test_handle_file_upload_with_oversized_file(self, mock_file_too_big):
        """Test that oversized files return appropriate error"""
        expect = _upld_res(False, "file_too_big", None)
        result = handle_file_upload(b"ABCD")
        mock_file_too_big.assert_called_once_with(b"ABCD")
        self.assertEqual(result, expect)

    @patch(f"{MODSTR}.classify_content", return_value=_class(None, None, None))
    def test_handle_file_upload_with_invalid_file_type(self, mock_classify):
        """Test that files with invalid type return appropriate error"""
        expect = _upld_res(False, "invalid_content_type", None)
        result = handle_file_upload(b"Not an image file")
        mock_classify.assert_called_once_with(b"Not an image file")
        self.assertEqual(result, expect)

    @patch("core.services.upload.save_upload")
    @patch("core.services.upload.PicItem")
    def test_handle_file_upload_with_valid_file(self, mock_pic_item, mock_save_upload):
        """Test that valid files are processed successfully"""
        # Set up mocks
        mock_instance = mock_pic_item.ensure.return_value
        mock_instance.filename = "test123.jpg"

        file_data = b"\xff\xd8\xff\xe0"  # JPEG magic bytes

        result = handle_file_upload(file_data)

        # Verify all steps were called
        mock_pic_item.ensure.assert_called_once_with(file_data)
        mock_save_upload.assert_called_once_with(mock_instance.filename, file_data)

        # Verify result
        self.assertTrue(result.success)
        self.assertEqual(result.error_type, "")
        self.assertEqual(result.item, mock_instance)

    # TODO: Verify functionality as refactor continues & refactor tests themselves

    # @patch("core.services.upload.save_upload")
    # @patch("core.services.upload.PicItem")
    # def test_handle_file_upload_with_storage_error(
    #     self, mock_pic_item, mock_save_upload
    # ):
    #     """Test that storage errors are handled properly"""
    #     # Set up mocks
    #     mock_instance = mock_pic_item.ensure.return_value
    #     mock_instance.filename = "test123.jpg"
    #     mock_save_upload.side_effect = OSError("Disk full")

    #     file_data = b"\xff\xd8\xff\xe0"  # JPEG magic bytes

    #     result = handle_file_upload(file_data)

    #     # Verify all steps were called
    #     mock_pic_item.ensure.assert_called_once_with(file_data)
    #     mock_save_upload.assert_called_once_with(mock_instance.filename, file_data)

    #     # Verify result
    #     self.assertFalse(result.success)
    #     self.assertEqual(result.error_type, "storage_error")
    #     self.assertIsNone(result.item)

    # @patch("core.services.upload.logger")
    # @patch("core.services.upload.save_upload")
    # @patch("core.services.upload.PicItem")
    # def test_service_logs_successful_save(
    #     self, mock_pic_item, mock_save_upload, mock_logger
    # ):
    #     """Test that service logs when file is saved successfully"""
    #     # Set up mocks
    #     mock_instance = mock_pic_item.ensure.return_value
    #     mock_instance.filename = "test123.jpg"
    #     mock_save_upload.return_value = True  # File was saved

    #     file_data = b"\xff\xd8\xff\xe0"  # JPEG magic bytes

    #     handle_file_upload(file_data)

    #     # Verify logging contains expected keywords
    #     mock_logger.info.assert_called_once()
    #     call_args = mock_logger.info.call_args[0][0]
    #     self.assertIn("test123.jpg", call_args)
    #     self.assertIn("saved", call_args.lower())

    # @patch("core.services.upload.logger")
    # @patch("core.services.upload.save_upload")
    # @patch("core.services.upload.PicItem")
    # def test_service_logs_file_exists(
    #     self, mock_pic_item, mock_save_upload, mock_logger
    # ):
    #     """Test that service logs when file already exists"""
    #     # Set up mocks
    #     mock_instance = mock_pic_item.ensure.return_value
    #     mock_instance.filename = "existing.jpg"
    #     mock_save_upload.return_value = False  # File already exists

    #     file_data = b"\xff\xd8\xff\xe0"  # JPEG magic bytes

    #     handle_file_upload(file_data)

    #     # Verify logging contains expected keywords
    #     mock_logger.info.assert_called_once()
    #     call_args = mock_logger.info.call_args[0][0]
    #     self.assertIn("existing.jpg", call_args)
    #     self.assertIn("exists", call_args.lower())

    # @patch("core.services.upload.logger")
    # @patch("core.services.upload.save_upload")
    # @patch("core.services.upload.PicItem")
    # def test_service_logs_storage_error(
    #     self, mock_pic_item, mock_save_upload, mock_logger
    # ):
    #     """Test that service logs when storage error occurs"""
    #     # Set up mocks
    #     mock_instance = mock_pic_item.ensure.return_value
    #     mock_instance.filename = "error.jpg"
    #     mock_save_upload.side_effect = OSError("Disk full")

    #     file_data = b"\xff\xd8\xff\xe0"  # JPEG magic bytes

    #     handle_file_upload(file_data)

    #     # Verify logging contains expected keywords
    #     mock_logger.error.assert_called_once()
    #     call_args = mock_logger.error.call_args[0][0]
    #     self.assertIn("error.jpg", call_args)
    #     self.assertIn("failed", call_args.lower())
