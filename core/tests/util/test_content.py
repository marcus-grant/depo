from django.test import TestCase
from unittest.mock import MagicMock
import base64

from core.util.content import classify_type as classify_content_type, convert_base64_to_file


class TestConvertBase64ToFile(TestCase):
    """Unit tests for convert_base64_to_file function"""

    def test_convert_png_data_uri(self):
        """Test converting PNG data URI to InMemoryUploadedFile"""

        # Minimal PNG data (1x1 transparent pixel)
        png_bytes = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAI9jU8cXgAAAABJRU5ErkJggg=="
        )
        png_b64 = base64.b64encode(png_bytes).decode()
        data_uri = f"data:image/png;base64,{png_b64}"

        result = convert_base64_to_file(data_uri)

        self.assertEqual(result.name, "clipboard.png")
        self.assertEqual(result.content_type, "image/png")
        self.assertEqual(result.size, len(png_bytes))

    def test_unsupported_format_raises_error(self):
        """Test that unsupported data URI format raises ValueError"""

        unsupported_uri = "data:text/plain;base64,SGVsbG8gV29ybGQ="

        with self.assertRaises(ValueError) as cm:
            convert_base64_to_file(unsupported_uri)

        self.assertIn("Unsupported data URI format", str(cm.exception))

    def test_invalid_base64_raises_error(self):
        """Test that invalid base64 data raises ValueError"""

        invalid_uri = "data:image/png;base64,InvalidBase64Data!@#$"

        with self.assertRaises(ValueError) as cm:
            convert_base64_to_file(invalid_uri)

        self.assertIn("Invalid base-64 data", str(cm.exception))


class TestClassifyType(TestCase):
    """Unit tests for classify_type function"""

    def test_classify_content_type_base64_image(self):
        """Test classification returns 'image' for base-64 images"""

        # Mock request with base-64 image flag
        request = MagicMock()
        request.is_base64_image = True
        request.FILES = {}
        request.POST.get.return_value = ""

        result = classify_content_type(request)
        self.assertEqual(result, "image")

    def test_classify_content_type_uploaded_file(self):
        """Test classification returns 'image' for file uploads"""

        # Mock request with uploaded file
        request = MagicMock()
        request.is_base64_image = False
        request.FILES = {"content": MagicMock()}
        request.POST.get.return_value = ""

        result = classify_content_type(request)
        self.assertEqual(result, "image")

    def test_classify_content_type_url(self):
        """Test classification returns 'url' for URL-like content"""

        # Mock request with URL content
        request = MagicMock()
        request.is_base64_image = False
        request.FILES = {}
        request.POST.get.return_value = "https://example.com"

        result = classify_content_type(request)
        self.assertEqual(result, "url")

    def test_classify_content_type_text(self):
        """Test classification returns 'text' for plain text content"""

        # Mock request with text content
        request = MagicMock()
        request.is_base64_image = False
        request.FILES = {}
        request.POST.get.return_value = "Hello world, this is plain text"

        result = classify_content_type(request)
        self.assertEqual(result, "text")

