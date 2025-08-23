# core/tests/views/test_logout.py
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User


class LogoutViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.logout_url = reverse("logout")
        self.index_url = reverse("index")
        
        # Create test user
        self.username = "testuser"
        self.password = "testpass123"
        self.user = User.objects.create_user(
            username=self.username, password=self.password
        )
    
    def test_logout_redirects_to_index(self):
        """Test that logout redirects to index page"""
        # First login the user
        self.client.login(username=self.username, password=self.password)
        
        # Verify user is logged in
        self.assertTrue("_auth_user_id" in self.client.session)
        
        # Logout and follow redirect
        response = self.client.post(self.logout_url, follow=True)
        
        # Should redirect to index page
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, self.index_url)
        
        # Verify user is logged out
        self.assertFalse("_auth_user_id" in self.client.session)
    
    def test_logout_get_request_not_allowed(self):
        """Test that GET request to logout returns 405 Method Not Allowed"""
        # Login first
        self.client.login(username=self.username, password=self.password)
        
        # Try GET request to logout (what happens when using a link)
        response = self.client.get(self.logout_url)
        
        # Should return 405 Method Not Allowed
        self.assertEqual(response.status_code, 405)