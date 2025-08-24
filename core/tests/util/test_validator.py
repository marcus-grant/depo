from django.test import TestCase


class TestLooksLikeUrl(TestCase):
    """Unit tests for looks_like_url function"""

    def test_looks_like_url_with_scheme(self):
        """Test URL detection for strings with explicit schemes"""
        from core.util.validator import looks_like_url

        self.assertTrue(looks_like_url("https://example.com"))
        self.assertTrue(looks_like_url("http://example.com"))
        self.assertTrue(looks_like_url("ftp://files.example.com"))
        self.assertTrue(looks_like_url("https://sub.domain.com/path"))

    def test_looks_like_url_without_scheme(self):
        """Test URL detection for domain-like strings without schemes"""
        from core.util.validator import looks_like_url

        self.assertTrue(looks_like_url("example.com"))
        self.assertTrue(looks_like_url("www.example.com"))
        self.assertTrue(looks_like_url("sub.domain.co.uk"))
        self.assertTrue(looks_like_url("api.service.io"))

    def test_looks_like_url_false_cases(self):
        """Test that non-URL strings return False"""
        from core.util.validator import looks_like_url

        self.assertFalse(looks_like_url("Hello world"))
        self.assertFalse(looks_like_url("just text"))
        self.assertFalse(looks_like_url("no.dots.but.not.a.url really"))
        self.assertFalse(looks_like_url(""))
        self.assertFalse(looks_like_url("   "))
        self.assertFalse(looks_like_url(None))