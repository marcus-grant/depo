# core/tests/util/test_content.py
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.test import TestCase
from io import BytesIO
from unittest.mock import MagicMock, patch

# from core.util.content import classify_type as classify_content_type
# from core.util.content import Base64ConversionResult
import core.util.content as content
import core.tests.fixtures as fixtures


class TestBase64ConversionResult(TestCase):
    """Unit tests for Base64ConversionResult dataclass"""

    def test_success_result_creation(self):
        """Test creating a successful conversion result"""
        file_data = b"test_file_data"
        result = content.Base64ConversionResult(success=True, file_data=file_data)
        self.assertTrue(result.success)
        self.assertEqual(result.file_data, file_data)
        self.assertIsNone(result.error_type)

    def test_failure_result_creation(self):
        """Test creating a failed conversion result"""
        result = content.Base64ConversionResult(
            success=False, error_type="base64_decode_error"
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error_type, "base64_decode_error")
        self.assertIsNone(result.file_data)

    def test_default_values(self):
        """Test that dataclass uses correct default values"""
        result = content.Base64ConversionResult(success=True)
        self.assertTrue(result.success)
        self.assertIsNone(result.file_data)
        self.assertIsNone(result.error_type)


class TestDecodeDataUri(TestCase):
    """Unit tests for decode_data_uri function"""

    def test_valid_png_conversion_success(self):
        """Test successful conversion of valid PNG data URI"""
        uri_data = fixtures.PNG_BASE64_DATA_URI
        result = content.decode_data_uri(uri_data)
        self.assertTrue(result.success)
        self.assertIsNotNone(result.file_data)
        self.assertIsNone(result.error_type)

    def test_invalid_format_returns_error(self):
        """Test that unsupported document format returns proper error"""
        invalid_content = "data:application/msword;base64,0M8R4KGxGuEAAAAAAAAAAAAA"
        result = content.decode_data_uri(invalid_content)
        self.assertFalse(result.success)
        self.assertEqual(result.error_type, "not_base64_image")
        self.assertIsNone(result.file_data)

    @patch("core.util.content.validator.is_within_base64_size_limit")
    def test_calls_size_validator_with_content(self, mock):
        """Test that size validator is called with correct content"""
        mock.return_value = True
        result = content.decode_data_uri(fixtures.PNG_BASE64_DATA_URI)
        mock.assert_called_once_with(fixtures.PNG_BASE64_DATA_URI)
        self.assertTrue(result.success)

    @patch("core.util.content.validator.is_base64_image_format")
    def test_calls_format_validator_with_content(self, mock):
        """Test that format validator is called with correct content"""
        mock.return_value = True
        content.decode_data_uri(fixtures.PNG_BASE64_DATA_URI)
        mock.assert_called_once_with(fixtures.PNG_BASE64_DATA_URI)

    @patch("core.util.content.convert_base64_to_file")
    def test_calls_conversion_function_with_content(self, mock):
        """Test that base64 conversion function is called with correct content"""
        # Mock the conversion to return a file-like object
        mock_file = InMemoryUploadedFile(
            file=BytesIO(b"test data"),
            field_name="image",
            name="test.png",
            content_type="image/png",
            size=9,
            charset=None,
        )
        mock.return_value = mock_file
        content.decode_data_uri(fixtures.PNG_BASE64_DATA_URI)
        mock.assert_called_once_with(fixtures.PNG_BASE64_DATA_URI)

    @patch("core.util.content.convert_base64_to_file")
    def test_base64_decode_error_handling(self, mock):
        """Test that base64 decode errors are handled correctly"""
        mock.side_effect = ValueError("Invalid base-64 data: some error")
        result = content.decode_data_uri(fixtures.PNG_BASE64_DATA_URI)
        self.assertFalse(result.success)
        self.assertEqual(result.error_type, "base64_decode_error")
        self.assertIsNone(result.file_data)

    @patch("core.util.content.convert_base64_to_file")
    def test_mime_type_mismatch_error_handling(self, mock):
        """Test that MIME type mismatch errors are handled correctly"""
        err_msg = "MIME type mismatch: claimed image/jpeg but actual format is png"
        mock.side_effect = ValueError(err_msg)
        result = content.decode_data_uri(fixtures.PNG_BASE64_DATA_URI)
        self.assertFalse(result.success)
        self.assertEqual(result.error_type, "mime_type_mismatch")
        self.assertIsNone(result.file_data)


class TestConvertBase64ToFile(TestCase):
    """Tests for the convert_base64_to_file function"""

    def test_convert_png_data_uri(self):
        """Test converting PNG data URI to InMemoryUploadedFile"""
        result = content.convert_base64_to_file(fixtures.PNG_BASE64_DATA_URI)
        self.assertIsInstance(result, InMemoryUploadedFile)
        self.assertEqual(result.name, "clipboard.png")
        self.assertEqual(result.content_type, "image/png")

    def test_unsupported_format_raises_error(self):
        """Test that unsupported data URI format raises ValueError"""
        bad_uri = "data:application/msword;base64,0M8R4KGxGuEAAAAAAAAAAAAA"
        with self.assertRaises(ValueError) as cm:
            content.convert_base64_to_file(bad_uri)
        self.assertIn("Unsupported data URI format", str(cm.exception))

    def test_invalid_base64_raises_error(self):
        """Test that invalid base64 data raises ValueError"""
        bad_uri = "data:image/png;base64,InvalidBase64Data!@#$"
        with self.assertRaises(ValueError) as cm:
            content.convert_base64_to_file(bad_uri)
        self.assertIn("Invalid base-64 data", str(cm.exception))


class ReadContentIfFile(TestCase):
    """Tests core.util.content.read_content_if_file function"""

    def setUp(self):
        self.test_strs = ["Hello, World!", "", " I LOVE YOU 200%💖"]
        self.test_bytes = [b"\xde\xad\xbe\xef", b"\x00\xffABCDEFGHIJKLMNOPQRSTUVWXYZ"]
        self.test_bytes += [fixtures.PNG_DATA, fixtures.JPEG_DATA, b""]
        self.test_ctypes = ["application/octet-stream"] * 2
        self.test_ctypes += ["image/png", "image/jpeg", "application/octet-stream"]

    def _gen_inmem_file(self, data: bytes, ctype: str) -> InMemoryUploadedFile:
        return InMemoryUploadedFile(
            file=BytesIO(data),
            field_name="file",
            name="testfile.bin",
            content_type=ctype,
            size=len(data),
            charset=None,
        )

    def test_str_input(self):
        """Test that given string input, it returns the same string"""
        for s in self.test_strs:
            with self.subTest(s=s):
                self.assertEqual(content.read_content_if_file(s), s)

    def test_bytes_input(self):
        """Test that bytes input returns same bytes"""
        for b in self.test_bytes:
            with self.subTest(b=b):
                self.assertEqual(content.read_content_if_file(b), b)

    def test_inmemfile_input(self):
        """Test that bytes in InMemoryUploadedFile are read and returned"""
        test_fn = content.read_content_if_file
        test_gen = self._gen_inmem_file
        for i in range(len(self.test_bytes)):
            with self.subTest(case=i):
                file = test_gen(self.test_bytes[i], self.test_ctypes[i])
                self.assertEqual(test_fn(file), self.test_bytes[i])

    @patch("django.core.files.uploadedfile.InMemoryUploadedFile.seek")
    @patch("django.core.files.uploadedfile.InMemoryUploadedFile.read")
    def test_inmemfile_seeks_reads(self, mock_read, mock_seek):
        """Test that InMemoryUploadedFile is seeked to start then read"""
        for i in range(len(self.test_bytes)):
            with self.subTest(i=i):
                file = self._gen_inmem_file(self.test_bytes[i], self.test_ctypes[i])
                mock_read.return_value = self.test_bytes[i]
                result = content.read_content_if_file(file)
                self.assertEqual(result, self.test_bytes[i])
                self.assertEqual(mock_seek.call_count, 2)
                mock_read.assert_called_once_with()
                mock_seek.reset_mock()
                mock_read.reset_mock()
