from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch, mock_open
from django.test import TestCase, override_settings

from core.util.files import save_upload


class TestSaveUpload(TestCase):
    """Unit tests for save_upload function"""

    @override_settings(UPLOAD_DIR="/tmp/test_uploads")
    def test_save_new_file_success(self):
        """Test saving a new file that doesn't exist yet"""
        with TemporaryDirectory() as temp_dir:
            with override_settings(UPLOAD_DIR=temp_dir):
                filename = "test.jpg"
                file_data = b"test file content"

                result = save_upload(filename, file_data)

                file_path = Path(temp_dir) / filename
                self.assertTrue(result)  # Should return True when file is saved
                self.assertTrue(file_path.exists())
                self.assertEqual(file_path.read_bytes(), file_data)

    def test_file_already_exists(self):
        """Test behavior when file already exists"""
        with TemporaryDirectory() as temp_dir:
            with override_settings(UPLOAD_DIR=temp_dir):
                filename = "existing.jpg"
                file_path = Path(temp_dir) / filename
                original_data = b"original content"
                new_data = b"new content"

                # Create the file first
                file_path.write_bytes(original_data)

                result = save_upload(filename, new_data)

                # Verify file wasn't overwritten  
                self.assertIs(result, False)  # Should return exactly False
                self.assertEqual(file_path.read_bytes(), original_data)

    def test_file_write_error(self):
        """Test handling of file write errors"""
        with TemporaryDirectory() as temp_dir:
            with override_settings(UPLOAD_DIR=temp_dir):
                filename = "error.jpg"
                file_path = Path(temp_dir) / filename
                file_data = b"test content"

                # Mock open to raise an IOError
                with patch("builtins.open", mock_open()) as mock_file:
                    mock_file.side_effect = IOError("Disk full")

                    with self.assertRaises(IOError):
                        save_upload(filename, file_data)

                    # Verify file wasn't created
                    self.assertFalse(file_path.exists())
