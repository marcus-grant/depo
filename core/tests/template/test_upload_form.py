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

    def test_file_picker_click_functionality(self):
        """Test that JavaScript for file picker click/keypress is present"""
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(self.url_index)

        # Check that click and keypress event handlers are present
        picker_checks = [
            ("click", "Missing click event handler for file picker"),
            ("keydown", "Missing keydown event handler for file picker"),
            ("Enter", "Missing Enter key detection"),
            ("file-input", "Missing file input reference"),
            (".click()", "Missing programmatic click call"),
        ]

        for expect, msg in picker_checks:
            with self.subTest(picker_fragment=expect):
                self.assertContains(response, expect, msg_prefix=msg)

    def test_drag_drop_event_handling(self):
        """Test that drag-and-drop events call preventDefault and stopPropagation"""
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(self.url_index)

        # Check that preventDefault and stopPropagation are called in event handlers
        event_checks = [
            ("preventDefault", "Missing preventDefault() calls in drag events"),
            ("stopPropagation", "Missing stopPropagation() calls in drag events"),
            ("e.preventDefault", "Missing event.preventDefault() pattern"),
            ("e.stopPropagation", "Missing event.stopPropagation() pattern"),
        ]

        for expect, msg in event_checks:
            with self.subTest(event_fragment=expect):
                self.assertContains(response, expect, msg_prefix=msg)
