from django.urls import reverse
from django.test import TestCase, Client
from django.contrib.auth.models import User


class UploadFormTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url_index = reverse("index")
        self.user = User.objects.create_user(username="testuser", password="testpass")

    def test_upload_form_basic_markup(self):
        """Test that the upload form contains required elements."""
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(self.url_index)

        markup_checks = [
            ("<textarea", "Missing textarea element"),
            (
                'placeholder="Paste text or link…"',
                "Missing placeholder text",
            ),
            ('id="content"', "Missing content textarea id"),
            ('type="file"', "Missing file input"),
            (
                'accept=".jpg,.jpeg,.png"',
                "Missing file type restrictions",
            ),
            (
                'style="display: none;"',
                "File input should be hidden",
            ),
            ('id="drop-zone"', "Missing drop zone"),
            ('tabindex="0"', "Drop zone should be focusable"),
            ('role="button"', "Drop zone should have button role"),
            ("aria-label=", "Drop zone should have aria-label"),
            ('id="submit-btn"', "Missing submit button"),
            (
                "disabled",
                "Submit button should be disabled by default",
            ),
        ]

        for expect, msg in markup_checks:
            with self.subTest(fragment=expect):
                self.assertContains(response, expect, msg_prefix=msg)

    def test_drag_over_cue_javascript_present(self):
        """Test that JavaScript for drag-over visual cues is present in the page"""
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(self.url_index)

        # Check that JavaScript event handlers are present in the page
        js_checks = [
            ("dragenter", "Missing dragenter event handler"),
            ("dragover", "Missing dragover event handler"),
            ("dragleave", "Missing dragleave event handler"),
            ("drop", "Missing drop event handler"),
            ("drag-over", "Missing drag-over CSS class reference"),
            ("addEventListener", "Missing JavaScript event listeners"),
        ]

        for expect, msg in js_checks:
            with self.subTest(js_fragment=expect):
                self.assertContains(response, expect, msg_prefix=msg)

