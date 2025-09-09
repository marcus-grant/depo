from django.core.files.uploadedfile import InMemoryUploadedFile
from django.test import TestCase
from io import BytesIO
from unittest.mock import MagicMock, patch

# from core.util.content import classify_type as classify_content_type
# from core.util.content import Base64ConversionResult
import core.util.content as content
import core.tests.fixtures as fixtures


class TestClassifyType(TestCase):
    """Unit tests for classify_type function"""

    def test_classify_content_type_base64_image(self):
        """Test classification returns 'image' for base-64 images"""
        # Mock request with base-64 image flag
        request = MagicMock()
        request.is_base64_image = True
        request.FILES = {}
        request.POST.get.return_value = ""

        result = content.classify_type(request)

        self.assertEqual(result, "image")

    def test_classify_content_type_uploaded_file(self):
        """Test classification returns 'image' for file uploads"""
        # Mock request with uploaded file
        request = MagicMock()
        request.is_base64_image = False
        request.FILES = {"content": MagicMock()}
        request.POST.get.return_value = ""

        result = content.classify_type(request)

        self.assertEqual(result, "image")

    def test_classify_content_type_url(self):
        """Test classification returns 'url' for URL-like content"""
        # Mock request with URL content
        request = MagicMock()
        request.is_base64_image = False
        request.FILES = {}
        request.POST.get.return_value = "https://example.com"

        result = content.classify_type(request)

        self.assertEqual(result, "url")

    def test_classify_content_type_text(self):
        """Test classification returns 'text' for plain text content"""
        # Mock request with text content
        request = MagicMock()
        request.is_base64_image = False
        request.FILES = {}
        request.POST.get.return_value = "Hello world, this is plain text"

        result = content.classify_type(request)

        self.assertEqual(result, "text")


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
