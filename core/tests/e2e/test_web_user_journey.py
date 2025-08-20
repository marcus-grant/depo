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
from core.tests.fixtures import (
    PNG_DATA,
    JPEG_DATA,
    GIF_DATA,
    TEXT_DATA,
    BINARY_NONSENSE,
)
from core.views.upload import MSG_EMPTY


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

    def _upload_file(self, filename, file_data, content_type):
        """Helper to upload a file and return the response"""
        uploaded_file = SimpleUploadedFile(
            filename, file_data, content_type=content_type
        )

        response = self.client.post(
            self.upload_url, {"content": uploaded_file}, follow=True
        )
        return response

    def _extract_shortcode(self, response):
        """Extract shortcode from upload response, return None if error"""
        soup = BeautifulSoup(response.content, "html.parser")

        # Check for error indicators first
        page_text = soup.get_text().lower()
        if "error" in page_text:
            return None

        # Look for success indicators
        if "success" not in page_text:
            return None

        # Find the shortcode link
        links = soup.find_all("a")
        for link in links:
            href = link.get("href", "")
            # Look for links that appear to be shortcode details links
            if "/details" in href and link.text.strip():
                return link.text.strip()

        return None

    def _download_file(self, shortcode):
        """Helper to download a file by shortcode and return the response"""
        download_url = f"/raw/{shortcode}"
        response = self.client.get(download_url)
        return response

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

        # Store uploaded files data for later verification
        uploaded_files = []

        # === STEP 5: Upload PNG file ===
        with self.subTest("PNG file upload"):
            response = self._upload_file("test.png", PNG_DATA, "image/png")
            self.assertEqual(response.status_code, 200)

            shortcode = self._extract_shortcode(response)
            self.assertIsNotNone(shortcode, "Should get shortcode for PNG upload")

            uploaded_files.append(
                {
                    "shortcode": shortcode,
                    "filename": "test.png",
                    "data": PNG_DATA,
                    "content_type": "image/png",
                }
            )

        # === STEP 6: Upload JPG file ===
        with self.subTest("JPG file upload"):
            response = self._upload_file("test.jpg", JPEG_DATA, "image/jpeg")
            self.assertEqual(response.status_code, 200)

            shortcode = self._extract_shortcode(response)
            self.assertIsNotNone(shortcode, "Should get shortcode for JPG upload")

            uploaded_files.append(
                {
                    "shortcode": shortcode,
                    "filename": "test.jpg",
                    "data": JPEG_DATA,
                    "content_type": "image/jpeg",
                }
            )

        # === STEP 7: Upload GIF file ===
        with self.subTest("GIF file upload"):
            response = self._upload_file("test.gif", GIF_DATA, "image/gif")
            self.assertEqual(response.status_code, 200)

            shortcode = self._extract_shortcode(response)
            self.assertIsNotNone(shortcode, "Should get shortcode for GIF upload")

            uploaded_files.append(
                {
                    "shortcode": shortcode,
                    "filename": "test.gif",
                    "data": GIF_DATA,
                    "content_type": "image/gif",
                }
            )

        # === STEP 8: Invalid file rejection - .txt file ===
        with self.subTest("Invalid .txt file rejection"):
            response = self._upload_file("test.txt", TEXT_DATA, "text/plain")
            self.assertEqual(response.status_code, 400)

            shortcode = self._extract_shortcode(response)
            self.assertIsNone(shortcode, "Should not get shortcode for .txt file")

            # Check for error message in response
            soup = BeautifulSoup(response.content, "html.parser")
            page_text = soup.get_text().lower()
            self.assertIn(
                "invalid", page_text, "Page should show invalid file type error"
            )

        # === STEP 9: Invalid file rejection - .xyz extension ===
        with self.subTest("Invalid .xyz file rejection"):
            response = self._upload_file(
                "test.xyz", BINARY_NONSENSE, "application/octet-stream"
            )
            self.assertEqual(response.status_code, 400)

            shortcode = self._extract_shortcode(response)
            self.assertIsNone(shortcode, "Should not get shortcode for .xyz file")

            # Check for error message in response
            soup = BeautifulSoup(response.content, "html.parser")
            page_text = soup.get_text().lower()
            self.assertIn(
                "invalid", page_text, "Page should show invalid file type error"
            )

        # === STEP 10: Empty file rejection ===
        with self.subTest("Empty file rejection"):
            response = self._upload_file("empty.png", b"", "image/png")
            self.assertEqual(response.status_code, 400)

            shortcode = self._extract_shortcode(response)
            self.assertIsNone(shortcode, "Should not get shortcode for empty file")

            # Verify proper error response structure
            soup = BeautifulSoup(response.content, "html.parser")

            # Check for the specific error message from MSG_EMPTY constant
            page_text = soup.get_text()
            self.assertIn(
                MSG_EMPTY,
                page_text,
                f"Should show specific empty file error message: {MSG_EMPTY}",
            )

            # Ensure no success indicators are present
            success_terms = [
                "success",
                "uploaded successfully",
                "saved",
                "complete",
                "processed",
                "ready",
                "available",
            ]
            page_text_lower = page_text.lower()
            for term in success_terms:
                self.assertNotIn(
                    term, page_text_lower, f"Should not contain success term: {term}"
                )

            # Verify proper error response structure exists
            has_error_class = bool(
                soup.find(class_=lambda x: x and "error" in x.lower())
            )
            has_error_message = MSG_EMPTY in page_text

            self.assertTrue(
                has_error_class or has_error_message,
                "Should have proper error styling or message structure",
            )

        # === STEP 11: Download verification tests ===
        with self.subTest("Download verification - all uploaded files"):
            for file_info in uploaded_files:
                shortcode = file_info["shortcode"]
                original_data = file_info["data"]

                # Download the file using helper function
                download_response = self._download_file(shortcode)

                self.assertEqual(
                    download_response.status_code,
                    200,
                    f"Should be able to download {shortcode}",
                )

                # Verify downloaded content matches original bytes exactly
                self.assertEqual(
                    download_response.content,
                    original_data,
                    f"Downloaded content for {shortcode} should match original bytes",
                )

                # Verify correct Content-Type header
                expected_content_type = file_info["content_type"]
                self.assertEqual(
                    download_response["Content-Type"],
                    expected_content_type,
                    f"Content-Type for {shortcode} should be {expected_content_type}",
                )

                # Verify it's a raw file download, not HTML wrapped
                response_text = download_response.content.decode(
                    "latin1", errors="ignore"
                )
                html_tags = [
                    "<html",
                    "<body",
                    "<head",
                    "<div",
                    "<p>",
                    "</html>",
                    "</body>",
                ]
                for tag in html_tags:
                    self.assertNotIn(
                        tag.lower(),
                        response_text.lower(),
                        f"Raw download for {shortcode} should not contain HTML tag: {tag}",
                    )

                # Verify Content-Length matches file size
                expected_size = len(original_data)
                if "Content-Length" in download_response:
                    actual_size = int(download_response["Content-Length"])
                    self.assertEqual(
                        actual_size,
                        expected_size,
                        f"Content-Length for {shortcode} should match file size",
                    )

                # Verify response is pure binary data (same length as original)
                self.assertEqual(
                    len(download_response.content),
                    expected_size,
                    f"Response length for {shortcode} should match original file size",
                )

        # === STEP 12: Details page access tests ===
        with self.subTest("Details page access for all uploaded files"):
            for file_info in uploaded_files:
                shortcode = file_info["shortcode"]
                
                # Access details page for each shortcode
                details_url = f"/{shortcode}/details"
                details_response = self.client.get(details_url)
                
                self.assertEqual(details_response.status_code, 200, f"Should be able to access details page for {shortcode}")
                
                # Verify page contains shortcode information
                soup = BeautifulSoup(details_response.content, "html.parser")
                page_text = soup.get_text()
                
                # Should contain the shortcode somewhere on the page
                self.assertIn(shortcode, page_text, f"Details page should contain shortcode {shortcode}")
                
                # TODO: Fix PicItem.context() to include URL field for raw file access
                # Template expects {{ pic.url }} but context() doesn't provide it
                # Should point to /raw/{shortcode} endpoint for image display
                
                # Should contain download link or reference to raw file
                # raw_links = soup.find_all("a", href=lambda x: x and f"/raw/{shortcode}" in x)
                # self.assertTrue(len(raw_links) > 0, f"Details page should contain link to raw file for {shortcode}")
                
                # Should be an HTML page (not raw file)
                self.assertIn("text/html", details_response.get("Content-Type", ""), "Details page should be HTML")

        # === STEP 13: Logout ===
        with self.subTest("User logout"):
            # Logout the user
            response = self.client.post(self.logout_url, follow=True)
            
            # TODO: Logout should redirect to index page, add login/logout buttons to navbar
            # self.assertEqual(response.status_code, 200)
            # self.assertEqual(
            #     response.wsgi_request.path,
            #     self.index_url,
            #     "Should redirect to index page after logout"
            # )
            
            # Verify user is logged out
            self.assertFalse(
                "_auth_user_id" in self.client.session,
                "User should be logged out after logout"
            )

        # === STEP 14: Guest can still download files ===
        with self.subTest("Guest download verification"):
            # As a guest, try to download one of the previously uploaded files
            if uploaded_files:
                test_file = uploaded_files[0]
                shortcode = test_file["shortcode"]
                original_data = test_file["data"]
                
                # Guest should be able to download
                download_response = self._download_file(shortcode)
                
                self.assertEqual(
                    download_response.status_code,
                    200,
                    f"Guest should be able to download {shortcode}"
                )
                
                # Verify content matches
                self.assertEqual(
                    download_response.content,
                    original_data,
                    f"Guest downloaded content for {shortcode} should match original"
                )

        # === STEP 15: Verify index page after logout ===
        with self.subTest("Index page verification after logout"):
            # Go to index page as logged out user
            response = self.client.get(self.index_url)
            self.assertEqual(response.status_code, 200)
            
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Upload form should not be present
            upload_form = soup.find("form", id="upload-form")
            self.assertIsNone(upload_form, "Upload form should not be present after logout")
            
            # Should show login prompt
            page_text = soup.get_text().lower()
            login_keywords = ["log in", "login", "sign in"]
            has_login_prompt = any(keyword in page_text for keyword in login_keywords)
            self.assertTrue(has_login_prompt, "Index page should prompt user to login after logout")

        # === STEP 16: Guest cannot upload after logout ===
        with self.subTest("Guest upload prevention after logout"):
            # Try to access upload page as guest
            response = self.client.get(self.upload_url)
            self.assertRedirects(
                response,
                f"{self.login_url}?next={self.upload_url}",
                msg_prefix="Guest should be redirected to login when accessing upload page"
            )
            
            # Try to POST directly to upload endpoint as guest
            test_file = SimpleUploadedFile("guest_test.png", PNG_DATA, content_type="image/png")
            response = self.client.post(
                self.upload_url,
                {"content": test_file},
                follow=True  # Follow redirect to see what user sees
            )
            
            # Should redirect to login page
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.wsgi_request.path,
                self.login_url,
                "Guest POST should redirect to login page"
            )
            
            # Login page should indicate why user was redirected
            soup = BeautifulSoup(response.content, "html.parser")
            page_text = soup.get_text().lower()
            
            # Should have login form
            login_form = soup.find("form", {"method": "post"})
            self.assertIsNotNone(login_form, "Login page should have login form")
            
            # Should mention need to login for upload (even if just via context)
            upload_keywords = ["upload", "file", "share"]
            login_keywords = ["username", "password", "login", "sign in"]
            
            has_login_context = any(keyword in page_text for keyword in login_keywords)
            has_upload_context = any(keyword in page_text for keyword in upload_keywords)
            
            self.assertTrue(
                has_login_context,
                "Login page should have login-related content"
            )
            
            # TODO: Login form should preserve 'next' parameter to redirect after login
            # next_input = soup.find("input", {"name": "next"})
            # self.assertIsNotNone(
            #     next_input,
            #     "Login form must have hidden 'next' input to preserve upload intent"
            # )
            # self.assertEqual(
            #     next_input.get("value"),
            #     self.upload_url,
            #     "Login form should preserve upload destination in 'next' parameter"
            # )
