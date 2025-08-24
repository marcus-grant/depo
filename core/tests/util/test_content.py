from django.test import TestCase
from unittest.mock import MagicMock

from core.util.content import classify_type as classify_content_type


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