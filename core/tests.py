# core/tests
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
from django.db import models
from django.http import response
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
import os

from core.util.shortcode import hash_b32, SHORTCODE_MIN_LEN, SHORTCODE_MAX_LEN
from core.models import Item, ItemContext
from core.link.models import LinkItem

### Model tests ###


class ItemSchemaTest(TestCase):
    def test_shortcode_field_names_types(self):
        """Test that the Item entity has the expected fields"""
        # Get actual field instances in lists
        fields = Item._meta.get_fields()
        field_names = [field.name for field in fields]

        # Define expected results
        expected_fields = {
            "code": models.CharField,
            "hash": models.CharField,
            "ctype": models.CharField,
            "btime": models.DateTimeField,
            "mtime": models.DateTimeField,
        }

        # Assert that field names are present and have the right types
        for expect_field_name, expect_field_type in expected_fields.items():
            with self.subTest(field_name=expect_field_name):
                self.assertIn(expect_field_name, field_names)
                field = Item._meta.get_field(expect_field_name)
                self.assertIsInstance(field, expect_field_type)

    def test_code_field_constraints(self):
        """Test that the id field has the expected constraints & atrributes"""
        code_field = Item._meta.get_field("code")
        self.assertTrue(getattr(code_field, "primary_key", False))
        self.assertEqual(getattr(code_field, "max_length", None), SHORTCODE_MAX_LEN)

    def test_hash_field_constraints(self):
        """Test that the hash field has the expected constraints & atrributes"""
        code_field = Item._meta.get_field("code")
        self.assertTrue(getattr(code_field, "primary_key", None))
        self.assertEqual(getattr(code_field, "max_length", None), SHORTCODE_MAX_LEN)

    def test_ctypes_field_constraints(self):
        """Test that the ctype field has the expected constraints & atrributes"""
        expect_choices = [
            ("xyz", "Mock type, DNE"),
            ("url", "URL"),
            ("txt", "Text"),
            ("pic", "Picture"),
        ]
        ctype_field = Item._meta.get_field("ctype")
        self.assertEqual(getattr(ctype_field, "max_length", None), 3)
        self.assertEqual(getattr(ctype_field, "choices", None), Item.CONTENT_TYPES)
        actual_choices = getattr(ctype_field, "choices", [])
        self.assertCountEqual(actual_choices, expect_choices)
        for choice in actual_choices:
            self.assertIn(choice, expect_choices)

    def test_btime_field_constraints(self):
        """Test that the btime field has the expected constraints & atrributes"""
        btime_field = Item._meta.get_field("btime")
        self.assertTrue(getattr(btime_field, "auto_now_add", False))

    def test_mtime_field_constraints(self):
        """Test that the mtime field has the expected constraints & atrributes"""
        mtime_field = Item._meta.get_field("mtime")
        self.assertTrue(getattr(mtime_field, "auto_now", False))


class ItemSearchShortcodeTest(TestCase):
    def test_success(self):
        """Test search_shortcode returns the correct item."""
        # Create an item to search for
        Item.objects.create(code="123456", hash="ABC", ctype="xyz")
        Item.objects.create(code="123456Z", hash="ABC", ctype="xyz")
        Item.objects.create(code="ZZZZZZ", hash="ABC", ctype="xyz")

        # Search for the item
        found_item1 = Item.search_shortcode("123456")
        found_item2 = Item.search_shortcode("123456Z")
        found_item3 = Item.search_shortcode("ZZZZZZ")

        # Ensure the item was found
        if not found_item1:
            raise Exception("Item 123456 not found")
        if not found_item2:
            raise Exception("Item 123456Z not found")
        if not found_item3:
            raise Exception("Item ZZZZZZ not found")

        # Assert that the item was found
        self.assertEqual(found_item1.code, "123456")
        self.assertEqual(found_item2.code, "123456Z")
        self.assertEqual(found_item3.code, "ZZZZZZ")
        self.assertEqual(found_item1.hash, found_item2.hash)
        self.assertEqual(found_item3.hash, found_item1.hash)
        self.assertEqual(found_item3.hash, "ABC")

    def test_failure(self):
        """Test search_shortcode returns None when item not found."""
        # Search for an item that doesn't exist
        found_item = Item.search_shortcode("D0ESN0T3X1ST")
        # Assert that the item was not found
        self.assertIsNone(found_item)


class ItemGetChildTest(TestCase):
    def test_returns_subclass(self):
        """Test that Item.get_child returns the correct subclass"""
        url = "https://google.com"
        link_item = LinkItem.ensure(url)
        item = Item.objects.get(pk=link_item.pk)
        child = item.get_child()
        self.assertIsInstance(child, LinkItem)
        self.assertEqual(child.pk, link_item.pk)
        self.assertTrue(getattr(child, "item", None))
        self.assertEqual(getattr(child, "url", None), link_item.url)

    def test_returns_item_when_no_subclass(self):
        """Test Item.get_child returns self if no subclass exists"""
        item = Item.objects.create(code="F00BAR", hash="BAZ", ctype="xyz")
        child = item.get_child()
        self.assertEqual(child, item)
        self.assertEqual(child.pk, item.pk)
        self.assertEqual(getattr(child, "ctype", None), "xyz")


class ItemEnsureTest(TestCase):
    GOOG_URL = "https://google.com"
    GOOG_H32 = "RGY6JE5M99DVYMWA5032GVYC"
    CONT_B32 = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"

    def test_creates(self):
        """Assert that ensure creates an item if none of that hash exists."""
        # First assert no items exist
        self.assertFalse(Item.objects.exists())
        # Use ensure to create an item
        Item.ensure(self.GOOG_URL)
        # Assert that the item was created
        self.assertEqual(Item.objects.count(), 1)

    def test_fields_assigned(self):
        """Test ensure assigns fields correctly."""
        item = Item.ensure(self.GOOG_URL)
        # Create timestamp to compare with Item's btime & mtime fields
        now = datetime.now(timezone.utc)
        self.assertEqual(item.code + item.hash, self.GOOG_H32)
        self.assertEqual(item.ctype, "url")
        self.assertLessEqual((now - item.btime).total_seconds(), 1)
        self.assertLessEqual((now - item.mtime).total_seconds(), 1)

    def test_idempotency(self):
        """Test ensure is idempotent, doesnt create duplicate items in backend."""
        # Call ensure first time
        code1 = self.GOOG_H32[:SHORTCODE_MIN_LEN]
        hash1 = self.GOOG_H32[SHORTCODE_MIN_LEN:]
        item1 = Item.objects.create(code=code1, hash=hash1, ctype="xyz")
        self.assertEqual(item1.code + item1.hash, self.GOOG_H32)
        # Call ensure second time
        item2 = Item.ensure(self.GOOG_URL)
        # Compare id, url, and shortcodes of both items
        self.assertEqual(item2.code, item1.code)
        self.assertEqual(item2.hash, item1.hash)
        self.assertEqual(item2.pk, item1.pk)
        # Ensure only one item was created in the backend
        self.assertEqual(Item.objects.count(), 1)

    def test_shortcode_collision(self):
        """Assert that codes starting at the same prefix are unique by
        adding more hash characters."""
        COUNT_B32 = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
        PREFIX = COUNT_B32[:SHORTCODE_MIN_LEN]
        HASH1, EX1 = f"{PREFIX}000", f"{PREFIX}"
        HASH2, EX2 = f"{PREFIX}001", f"{PREFIX}0"
        HASH3, EX3 = f"{PREFIX}002", f"{PREFIX}00"
        HASH4, EX4 = f"{PREFIX}003", f"{PREFIX}003"
        HASH5, EX5 = f"{PREFIX}004", f"{PREFIX}004"
        HASHES = [HASH1, HASH2, HASH3, HASH4, HASH5]
        EXS = [EX1, EX2, EX3, EX4, EX5]
        # Patch hash_b32 to return these values
        # Without patching it's really hard to find collisions to test
        with patch("core.models.hash_b32") as mock_h32:
            for i, hash in enumerate(HASHES):
                mock_h32.return_value = hash
                with self.subTest(i=i, hash=hash, expect=EXS[i]):
                    content = f"https://example{i}.com"
                    item = Item.ensure(content, ctype="xyz")
                    self.assertEqual(item.code, EXS[i])
                    self.assertEqual(item.hash, hash[len(EXS[i]) :])

        # Finally assert that non collision works normally
        content = "https://google.com"
        full_hash = "RGY6JE5M99DVYMWA5032GVYC"
        exp_code = full_hash[:SHORTCODE_MIN_LEN]
        exp_hash = full_hash[SHORTCODE_MIN_LEN:]
        item = Item.ensure(content, ctype="url")
        self.assertEqual(item.code, exp_code)
        self.assertEqual(item.hash, exp_hash)

    def test_raises_with_invalid_type(self):
        """Test that ensure raises TypeError with invalid ctype."""
        with self.assertRaises(TypeError):
            Item.ensure("https://google.com", ctype="invalid")  # type: ignore


class ItemContextTest(TestCase):
    def test_context(self):
        """Test that the context method returns the expected dictionary."""
        item = Item.objects.create(code="F00BAR", hash="BAZ", ctype="xyz")
        now = f"{datetime.now(timezone.utc):%Y-%m-%dT%H:%M}"
        ctx = item.context()
        # Check for all expected keys
        self.assertIn("code", ctx)
        self.assertIn("hash", ctx)
        self.assertIn("ctype", ctx)
        self.assertIn("btime", ctx)
        self.assertIn("mtime", ctx)
        # Check for expected values
        self.assertEqual(ctx["code"], "F00BAR")
        self.assertEqual(ctx["hash"], "F00BARBAZ")
        self.assertEqual(ctx["ctype"], "xyz")
        self.assertIn(now, ctx["btime"])
        self.assertIn(now, ctx["mtime"])


### View Tests ###


class WebIndexViewTest(TestCase):
    def test_get_request_renders_index(self):
        """Test root GET request renders index.html"""
        resp = self.client.get(reverse("web_index"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "index.html")
        self.assertNotContains(resp, "error")
        self.assertNotContains(resp, "shortcode is: <strong>")

    def test_root_post_request_creates_item(self):
        """Test root POST request creates an item"""
        url = "https://www.google.com"
        resp = self.client.post(reverse("web_index"), {"content": url})
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "index.html")

        # Check response contents against Item contents
        shortcode = hash_b32(url)[:SHORTCODE_MIN_LEN]
        pattern_href = f'href="[^"]*{shortcode}/details"'
        self.assertContains(resp, f"{shortcode}</strong>")
        self.assertRegex(resp.content.decode(), pattern_href)

    # NOTE: I can't think of a case where this will happen
    # def test_post_no_content(self):
    #     """Test POST request missing content"""
    #     # breakpoint()
    #     resp = self.client.post(reverse("web_index"))
    #     breakpoint()
    #     self.assertEqual(resp.status_code, 400)
    #     self.assertTemplateUsed(resp, "index.html")
    #     self.assertContains(resp, "Content is required")


class ShortcodeDetailsViewTest(TestCase):
    def setUp(self):
        self.link = LinkItem.ensure("https://google.com")

    # TODO: Need to figure out how to deal with 404
    # def test_non_existent_shortcode(self):
    #     """Test failed shortcode lookup renders 404-lookup.html"""
    #     resp = self.client.get(reverse("shortcode_details", args=["noExist"]))
    #     self.assertEqual(resp.status_code, 404)
    #     # Because HttPResponseNotFound cant be tested against template use,
    #     # Check for a commented out string with a test marker
    #     self.assertContains(resp, "404-lookup.html", status_code=404)
    #     self.assertContains(resp, "testMarker", status_code=404)

    def test_valid_shortcode_renders_details(self):
        """Test valid shortcode form request renders details page content"""
        shortcode = self.link.item.code
        resp = self.client.get(reverse("shortcode_details", args=[shortcode]))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "shortcode-details.html")
        self.assertContains(resp, shortcode)
        self.assertContains(resp, self.link.url)


class UploadViewGETTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.upload_url = reverse("upload")

    def test_upload_page_accessible_via_get(self):
        resp = self.client.get(self.upload_url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "upload.html")

    def test_upload_page_contains_file_input(self):
        resp = self.client.get(self.upload_url)
        self.assertContains(resp, '<input type="file"')


@override_settings(UPLOAD_DIR=settings.BASE_DIR / "tmp")
class UploadViewPostTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.upload_url = reverse("upload")
        # Ensure temporary upload directory exists
        if not os.path.exists(settings.UPLOAD_DIR):
            os.makedirs(settings.UPLOAD_DIR)

    def tearDown(self):
        # Cleanup: remove all files in the directory
        for filename in os.listdir(settings.UPLOAD_DIR):
            file_path = os.path.join(settings.UPLOAD_DIR, filename)
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                os.rmdir(file_path)
        os.rmdir(settings.UPLOAD_DIR)  # Now remove directory

    def mock_ensure_with_dummy_pic(self, mock, code="M0CKHASH", fmt="jpg", size=0):
        dummy = MagicMock()
        dummy.item.code = code
        dummy.format = fmt
        dummy.size = size
        mock.return_value = dummy
        return mock

    @patch("core.pic.models.PicItem.ensure")
    def test_ensure_call_with_file_content(self, mock_ensure):
        """Ensure should PicItem.ensure called with contents of uploaded file."""
        # Arrange: Dummy PicItem instance & Image file
        kwargs = {"code": "DUMYHASH", "fmt": "png", "size": 0}
        mock_ensure = self.mock_ensure_with_dummy_pic(mock_ensure, **kwargs)
        args = ("dummy.png", b"\x89PNG\r\n\x1a\n")
        uploaded_file = SimpleUploadedFile(*args, content_type="image/png")
        # Act: POST the file for the upload view to handle
        self.client.post(self.upload_url, {"image": uploaded_file})
        # Assert: PicItem.ensure called with exact file contents
        mock_ensure.assert_called_once_with(b"\x89PNG\r\n\x1a\n")

    @patch("core.pic.models.PicItem.ensure")
    def test_file_saved_as_hash_filename_fmt_ext(self, mock_ensure):
        """Test uploaded pic file saved w/ Item.code & PicItem.format filename."""
        # Arrange: Dummy PicItem & Image file
        kwargs = {"code": "DUMYHASH", "fmt": "gif", "size": 0}
        mock_ensure = self.mock_ensure_with_dummy_pic(mock_ensure, **kwargs)
        image_content = b"GIF89a"
        args = ("dummy.gif", image_content)
        uploaded_file = SimpleUploadedFile(*args, content_type="image/gif")
        # Act: Post image
        self.client.post(self.upload_url, {"image": uploaded_file})
        # Assert: File should be saved to server FS correctly
        expect_filename = f"{mock_ensure().item.code}.{mock_ensure().format}"
        expect_filepath = settings.UPLOAD_DIR / expect_filename
        self.assertTrue(expect_filepath.exists())

    @patch("core.pic.models.PicItem.ensure")
    def test_response_contains_model_details(self, mock_ensure):
        """Response to upload needs to contain associated model details."""
        # Arrange: Prepare a dummy PicItem & Image file
        mock_ensure = self.mock_ensure_with_dummy_pic(mock_ensure)
        args = ("dummy.jpg", b"\xff\xd8\xff")
        uploaded_file = SimpleUploadedFile(*args, content_type="image/jpeg")
        # Act: POST image, capture response
        resp = self.client.post(self.upload_url, {"image": uploaded_file})
        resp_txt = resp.content.decode()
        # Assert: Response has file details
        self.assertIn(mock_ensure().item.code, resp_txt)
        self.assertIn(mock_ensure().format, resp_txt)

    @patch("core.pic.models.PicItem.ensure")
    def test_upload_accepts_allowed_file_types(self, mock_ensure):
        # Arrange: Prepare a dummy PicItem to simulate normal processing & dummy JPEG
        mock_ensure = self.mock_ensure_with_dummy_pic(mock_ensure)
        jpg = b"\xff\xd8\xff"
        file_jpg = SimpleUploadedFile("t.jpg", jpg, content_type="image/jpeg")
        png = b"\x89PNG\r\n\x1a\n"
        file_png = SimpleUploadedFile("t.png", png, content_type="image/png")
        file_gif = SimpleUploadedFile("t.gif", b"GIF89a", content_type="image/gif")
        # Act: POST the file.
        resp_jpg = self.client.post(self.upload_url, {"image": file_jpg})
        resp_png = self.client.post(self.upload_url, {"image": file_png})
        resp_gif = self.client.post(self.upload_url, {"image": file_gif})
        # Assert: Check for HTTP 200 and that processing occurred.
        self.assertEqual(resp_jpg.status_code, 200)
        self.assertEqual(resp_png.status_code, 200)
        self.assertEqual(resp_gif.status_code, 200)
        self.assertEqual(mock_ensure.call_count, 3)

    @patch("core.pic.models.PicItem.ensure")
    def test_upload_rejects_disallowed_file_types(self, mock_ensure):
        # Arrange: Create a dummy text file.
        x = b"Hello, world!"
        file_upl = SimpleUploadedFile("invalid.xyz", x, content_type="text/plain")
        # Act: POST the file.
        resp = self.client.post(self.upload_url, {"image": file_upl})
        # Assert: Expect HTTP 400 and that PicItem.ensure is never called.
        self.assertEqual(resp.status_code, 400)
        self.assertIn("File type not allowed", resp.content.decode())
        mock_ensure.assert_not_called()

    @patch("core.pic.models.PicItem.ensure")
    def test_empty_file_upload_returns_error(self, mock_ensure):
        """
        If the uploaded file is empty, the view should return HTTP 400 and
        not call PicItem.ensure.
        """
        # Arrange: Create an empty file upload.
        empty_file = SimpleUploadedFile("empty.png", b"", content_type="image/png")
        # Act: POST the empty file.
        resp = self.client.post(self.upload_url, {"image": empty_file})
        # Assert: Expect HTTP 400 and ensure PicItem.ensure is not called.
        self.assertEqual(resp.status_code, 400)
        self.assertIn("EMPTY", resp.content.decode().upper())
        mock_ensure.assert_not_called()

    @patch("core.pic.models.PicItem.ensure")
    def test_file_write_error_returns_server_error(self, mock_ensure):
        """If error occurs during file writing, view should return HTTP 500."""
        # Arrange: Set up a dummy PicItem so processing proceeds.
        dummy_pic = MagicMock()
        dummy_pic.item.code = "ERRHASH"
        dummy_pic.format = "jpg"
        mock_ensure.return_value = dummy_pic

        # Create a dummy image file (non-empty).
        image_content = b"\xff\xd8\xff"  # Minimal JPEG header.
        uploaded_file = SimpleUploadedFile(
            "dummy.jpg", image_content, content_type="image/jpeg"
        )

        # Patch 'open' in the module where it is used so that it raises an OSError.
        with patch("core.views.open", side_effect=OSError("Disk error")):
            # Act: POST the file.
            resp = self.client.post(self.upload_url, {"image": uploaded_file})

        # Assert: Expect HTTP 500 and an error message mentioning file saving.
        self.assertEqual(resp.status_code, 500)
        self.assertIn("ERROR", resp.content.decode().upper())
        self.assertIn("SAV", resp.content.decode().upper())
        self.assertIn("FILE", resp.content.decode().upper())


### Template Tests ###


# TODO: Test the redirection of the shortcode using URLs
class TemplateTagsTest(TestCase):
    def test_index_contains_form(self):
        resp = self.client.get(reverse("web_index"))
        self.assertContains(resp, "<form")
        self.assertContains(resp, 'name="content"')
        self.assertContains(resp, 'type="submit"')
        self.assertNotContains(resp, "/details")

    def test_index_contains_form_post(self):
        ctx = {"content": "https://www.google.com"}
        resp = self.client.post(reverse("web_index"), ctx)
        self.assertContains(resp, "<form")
        self.assertContains(resp, 'name="content"')
        self.assertContains(resp, 'type="submit"')
        # Check for the confirmation link unique to POST
        self.assertContains(resp, "/details")
