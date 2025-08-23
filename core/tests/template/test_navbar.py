# core/tests/template/test_navbar.py
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from bs4 import BeautifulSoup


class NavbarTemplateTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.index_url = reverse("index")
        
    def test_navbar_shows_login_when_not_authenticated(self):
        """Test that navbar shows login button when user is not authenticated"""
        # Make request as anonymous user
        response = self.client.get(self.index_url)
        self.assertEqual(response.status_code, 200)
        
        # Parse HTML
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Find navbar
        navbar = soup.find("nav", class_="navbar")
        self.assertIsNotNone(navbar, "Navbar should be present")
        
        # Look for login link/button in navbar
        login_links = navbar.find_all("a", href=lambda x: x and "/accounts/login" in x)
        
        self.assertTrue(
            len(login_links) > 0,
            "Navbar should contain a login link when user is not authenticated"
        )
        
        # Verify logout is NOT present
        logout_links = navbar.find_all("a", href=lambda x: x and "/accounts/logout" in x)
        self.assertEqual(
            len(logout_links), 0,
            "Navbar should not contain logout link when user is not authenticated"
        )

    def test_navbar_shows_logout_when_authenticated(self):
        """Test that navbar shows logout button when user is authenticated"""
        # Create and login user
        user = User.objects.create_user(username="testuser", password="testpass")
        self.client.login(username="testuser", password="testpass")
        
        # Make request as authenticated user
        response = self.client.get(self.index_url)
        self.assertEqual(response.status_code, 200)
        
        # Parse HTML
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Find navbar
        navbar = soup.find("nav", class_="navbar")
        self.assertIsNotNone(navbar, "Navbar should be present")
        
        # Look for logout form in navbar
        logout_forms = navbar.find_all("form", action=lambda x: x and "/accounts/logout" in x)
        
        self.assertTrue(
            len(logout_forms) > 0,
            "Navbar should contain a logout form when user is authenticated"
        )
        
        # Verify form has POST method
        logout_form = logout_forms[0]
        self.assertEqual(logout_form.get("method"), "post", "Logout form should use POST method")
        
        # Verify form has CSRF token
        csrf_input = logout_form.find("input", {"name": "csrfmiddlewaretoken"})
        self.assertIsNotNone(csrf_input, "Logout form should have CSRF token")
        
        # Verify login is NOT present
        login_links = navbar.find_all("a", href=lambda x: x and "/accounts/login" in x)
        self.assertEqual(
            len(login_links), 0,
            "Navbar should not contain login link when user is authenticated"
        )