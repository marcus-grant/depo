# core/tests
from datetime import datetime, timezone
from unittest.mock import patch
from django.db import models
from django.test import TestCase
from django.urls import reverse

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


# TODO: Implement these suggestions:
# 9. Improve Test Readability and Maintainability
# Suggestion:
# Use Test Data Factories:
# Consider using a library like factory_boy to create test data.
# This can make your tests cleaner and more maintainable.
# Example with factory_boy:
# import factory
# from .models import Item, LinkItem
#
# class ItemFactory(factory.django.DjangoModelFactory):
#     class Meta:
#         model = Item
#
#     code = factory.Faker('bothify', text='??????')
#     hash = factory.Faker('bothify', text='######')
#     ctype = 'url'
#
# class LinkItemFactory(ItemFactory):
#     class Meta:
#         model = LinkItem
#
#     url = factory.Faker('url')
# Use Factories in Tests:
# class LinkItemEnsureTest(TestCase):
#     def test_linkitem_ensure_creates(self):
#         """Test that LinkItem.ensure creates a LinkItem correctly."""
#         url = "https://example.com"
#         link_item = LinkItem.ensure(url)
#         self.assertEqual(link_item.url, url)
#         # Use factories to create additional instances if needed
# 10. Follow Best Practices in Django Testing
# Suggestion:
# Use setUpTestData for Class-Level Data:
# If you have data that doesn't change between tests, use @classmethod and setUpTestData to create it once per test class.
# Example:
# class ItemEnsureTest(TestCase):
#     @classmethod
#     def setUpTestData(cls):
#         cls.GOOG_URL = "https://google.com"
#         cls.link_item = LinkItem.ensure(cls.GOOG_URL)
#
#     def test_idempotency(self):
#         """Test ensure is idempotent."""
#         link_item2 = LinkItem.ensure(self.GOOG_URL)
#         self.assertEqual(self.link_item.pk, link_item2.pk)
# Avoid Hardcoding Timestamps:
# Instead of comparing timestamps to datetime.now(), use assertIsNotNone or check relative differences.
