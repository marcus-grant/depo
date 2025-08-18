"""
E2E test for complete web user journey

Single flow test that simulates a real user session:
1. Guest attempts upload (fails)
2. User logs in with wrong then correct credentials
3. User uploads various files (success and failure cases)
4. User downloads uploaded files and verifies content matches original bytes
5. User checks details pages for each upload
6. User logs out
7. Guest attempts upload again (fails)

Uses proper HTML parsing to extract shortcodes and verify page structure.
"""

from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from pathlib import Path
from bs4 import BeautifulSoup


@override_settings(UPLOAD_DIR=settings.BASE_DIR / "test_uploads_web_e2e")
class WebUserJourneyE2ETest(TestCase):
    """
    Complete end-to-end test of web user journey as a single flow.
    Uses BeautifulSoup to parse HTML and verify expected page structure.
    """

    def setUp(self):
        self.client = Client()
        self.upload_url = reverse("web_upload")
        self.login_url = reverse("login")
        self.logout_url = reverse("logout")
        self.index_url = reverse("index")

        # Create test user
        self.username = "testuser"
        self.password = "testpass123"
        self.user = User.objects.create_user(
            username=self.username, password=self.password
        )

        # Setup upload directory
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(exist_ok=True)

    def tearDown(self):
        """Clean up test files and directories"""
        if self.upload_dir.exists():
            for file in self.upload_dir.iterdir():
                if file.is_file():
                    file.unlink()
            self.upload_dir.rmdir()

    def _verify_guest_index_page(self):
        """Verify index page for guest user - no upload form, login button present"""
        response = self.client.get(self.index_url)
        self.assertEqual(response.status_code, 200)

        soup = BeautifulSoup(response.content, "html.parser")

        # Upload form should not be present for guests
        upload_form = soup.find("form", id="upload-form")
        self.assertIsNone(upload_form, "Upload form should not be present for guests")

        # Look for login prompt - could be a button, link, or text
        page_text = soup.get_text().lower()

        # Check for login-related text
        login_keywords = ["log in", "login", "sign in", "authenticate"]
        upload_keywords = ["upload", "share", "file"]

        has_login_prompt = any(keyword in page_text for keyword in login_keywords)
        has_upload_context = any(keyword in page_text for keyword in upload_keywords)

        self.assertTrue(has_login_prompt, "Page should prompt user to login")
        self.assertTrue(
            has_upload_context, "Page should mention file upload functionality"
        )

        # Also check for any clickable login element (button or link)
        login_elements = []
        for tag in ["a", "button"]:
            elements = soup.find_all(tag)
            for elem in elements:
                elem_text = elem.get_text().lower()
                if any(keyword in elem_text for keyword in login_keywords):
                    login_elements.append(elem)

        self.assertTrue(
            len(login_elements) > 0,
            "Page should have at least one clickable login element",
        )

        return soup

    def test_complete_user_journey(self):
        """Complete user journey from guest to authenticated user and back."""

        # === STEP 1: Verify guest index page ===
        with self.subTest("Guest index page verification"):
            self._verify_guest_index_page()

        # === STEP 2: Guest attempts upload (should be redirected to login) ===
        with self.subTest("Guest upload redirect to login"):
            response = self.client.get(self.upload_url)
            self.assertRedirects(
                response,
                f"{self.login_url}?next={self.upload_url}",
                msg_prefix="Guest should be redirected to login for upload page",
            )

        # === STEP 3: Login with wrong credentials ===
        with self.subTest("Failed login attempt"):
            response = self.client.post(
                self.login_url,
                {
                    "username": self.username,
                    "password": "wrongpassword",
                    "next": self.upload_url,
                },
            )
            self.assertEqual(response.status_code, 200)

            # Verify error message is shown
            soup = BeautifulSoup(response.content, "html.parser")

            # Look for any element containing login-related error text
            page_text = soup.get_text().lower()
            error_indicators = ["invalid", "incorrect", "wrong", "failed", "error"]
            login_indicators = ["username", "password", "login", "log in"]

            # Check if we have both error and login context
            has_error_context = any(
                indicator in page_text for indicator in error_indicators
            )
            has_login_context = any(
                indicator in page_text for indicator in login_indicators
            )

            self.assertTrue(
                has_error_context and has_login_context,
                f"Page should show login error. Found error context: {has_error_context}, login context: {has_login_context}",
            )

            # Verify user is still not logged in
            self.assertFalse(
                "_auth_user_id" in self.client.session,
                "User should not be logged in after failed attempt",
            )

        # === STEP 4: Login with correct credentials ===
        with self.subTest("Successful login"):
            response = self.client.post(
                self.login_url,
                {
                    "username": self.username,
                    "password": self.password,
                    "next": self.upload_url,
                },
                follow=True,
            )

            # Should redirect to upload page after successful login
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.wsgi_request.path,
                self.upload_url,
                "Should redirect to upload page after login",
            )

            # Verify user is logged in
            self.assertTrue(
                "_auth_user_id" in self.client.session,
                "User should be logged in after successful attempt",
            )

            # Verify upload form is now visible
            soup = BeautifulSoup(response.content, "html.parser")
            upload_form = soup.find(
                "form", {"method": "post", "enctype": "multipart/form-data"}
            )
            self.assertIsNotNone(
                upload_form, "Upload form should be visible for authenticated users"
            )
