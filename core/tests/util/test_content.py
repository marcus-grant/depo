from django.test import TestCase
from unittest.mock import MagicMock

# from core.util.content import classify_type as classify_content_type
# from core.util.content import Base64ConversionResult
import core.util.content as content


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
