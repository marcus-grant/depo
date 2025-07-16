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

        # Login button should be present in the box
        login_button = soup.find("a", class_="button is-link")
        self.assertIsNotNone(login_button, "Login button should be present for guests")
        button_text = login_button.get_text().lower()
        self.assertIn("upload", button_text, "Button should mention upload")
        self.assertIn("login", button_text, "Button should mention login")

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
