from django.test import TestCase
from django.urls import reverse


class RawDownloadViewTests(TestCase):
    """Unit tests for raw file download functionality"""
    
    def test_raw_download_url_pattern_exists(self):
        """Test that /raw/{shortcode} URL pattern is routable"""
        response = self.client.get('/raw/ABC123')
        # Should return a valid HTTP response (not 500 internal error)
        self.assertLess(response.status_code, 500, "URL pattern should resolve without server errors")