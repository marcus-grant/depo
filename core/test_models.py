from datetime import datetime, timezone
from django.test import TestCase
from django.db import models
from unittest.mock import patch

from .models import Item, LinkItem
from .shortcode import SHORTCODE_MAX_LEN, SHORTCODE_MIN_LEN

# TODO: Create Separate Item & LinkItem SchemaTest classes

###
# # Item (Parent class) Tests
###


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


class LinkItemSchemaTest(TestCase):
    def test_url_field_constraints(self):
        """Test that the url field has the expected constraints & atrributes"""
        url_field = LinkItem._meta.get_field("url")
        self.assertEqual(getattr(url_field, "max_length", None), 255)
        self.assertFalse(getattr(url_field, "blank", True))
        self.assertFalse(getattr(url_field, "null", True))

    def test_fieldname_types(self):
        """Test that the LinkItem entity has the expected fields"""
        fields = LinkItem._meta.get_fields()
        field_names = [field.name for field in fields]
        expect = {
            "item_ptr": models.OneToOneField,
            "url": models.URLField,
        }

        for expect_name, expect_type in expect.items():
            with self.subTest(field_name=expect_name):
                self.assertIn(expect_name, field_names)
                field = LinkItem._meta.get_field(expect_name)
                self.assertIsInstance(field, expect_type)

    def test_access_parent_fields(self):
        """Test that LinkItem can access parent fields"""
        # Create a LinkItem
        f = {"code": "G00G", "hash": "L3", "ctype": "url", "url": "https://google.com"}
        LinkItem.objects.create(**f)
        # Retrieve all fields from both parent and child of model instance
        item = LinkItem.objects.first()
        item_fields = item.__dict__.keys()
        expect = {"code", "hash", "ctype", "btime", "mtime", "url"}
        for field in expect:
            with self.subTest(field_name=field):
                self.assertIn(field, item_fields)


# TODO: Create similar class for Item.ensure
class LinkItemEnsureTest(TestCase):
    # Known hash_b32 values for different content
    GOOG_URL = "https://google.com"
    GOOG_H32 = "RGY6JE5M99DVYMWA5032GVYC"
    CONT_B32 = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"

    def test_creates(self):
        """Assert that ensure creates a LinkItem if none of that hash exists."""
        # First assert no items exist
        self.assertFalse(LinkItem.objects.exists())
        # Use ensure to create a LinkItem
        LinkItem.ensure(self.GOOG_URL)
        self.assertEqual(LinkItem.objects.count(), 1)
        self.assertEqual(Item.objects.count(), 1)

    def test_fields_assigned(self):
        """Test ensure assigns fields correctly."""
        item = LinkItem.ensure(self.GOOG_URL)
        # Create timestamp to compare with Item's btime & mtime fields
        now = datetime.now(timezone.utc)
        self.assertEqual(item.item.code + item.item.hash, self.GOOG_H32)
        self.assertEqual(item.url, self.GOOG_URL)
        self.assertEqual(item.item.ctype, "url")
        self.assertLessEqual((now - item.item.btime).total_seconds(), 1)
        self.assertLessEqual((now - item.item.mtime).total_seconds(), 1)

    def test_idempotency(self):
        """Test ensure is idempotent, doesnt create duplicate items in backend.
        This also tests that other fields are assigned correctly and the same."""
        # Call ensure first time
        code1 = self.GOOG_H32[:SHORTCODE_MIN_LEN]
        hash1 = self.GOOG_H32[SHORTCODE_MIN_LEN:]
        item1 = Item.objects.create(code=code1, hash=hash1, ctype="url")
        link1 = LinkItem.objects.create(item=item1, url=self.GOOG_URL)
        self.assertEqual(link1.item.code + link1.item.hash, self.GOOG_H32)
        self.assertEqual(link1.url, self.GOOG_URL)

        # Call ensure second time
        link2 = LinkItem.ensure(content=self.GOOG_URL)
        # Compare id, url, and shortcodes of both items
        self.assertEqual(link2.item.code, link1.item.code)
        self.assertEqual(link2.item.hash, link1.item.hash)
        self.assertEqual(link2.pk, link1.pk)
        self.assertEqual(link2.url, link1.url)

        # Ensure only one item was created in the backend
        self.assertEqual(Item.objects.count(), 1)
        self.assertEqual(LinkItem.objects.count(), 1)

    # NOTE: This test should only be run in Item,
    # this & other subtypes should just assert ensure is called correctly
    def test_shortcode_collision(self):
        COUNT_B32 = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
        PREFIX = COUNT_B32[:SHORTCODE_MIN_LEN]
        HASH1, EX1 = f"{PREFIX}000", f"{PREFIX}"
        HASH2, EX2 = f"{PREFIX}001", f"{PREFIX}0"
        HASH3, EX3 = f"{PREFIX}002", f"{PREFIX}00"
        HASH4, EX4 = f"{PREFIX}003", f"{PREFIX}003"
        HASH5, EX5 = f"{PREFIX}004", f"{PREFIX}004"
        HASHES = [HASH1, HASH2, HASH3, HASH4, HASH5]
        EXS = [EX1, EX2, EX3, EX4, EX5]
        with patch("core.models.hash_b32") as mock_h32:
            for i, hash in enumerate(HASHES):
                mock_h32.return_value = hash
                with self.subTest(i=i, hash=hash, expect=EXS[i]):
                    content = f"https://example{i}.com"
                    item = LinkItem.ensure(content)
                    self.assertEqual(item.item.code, EXS[i])
                    hash_rem = hash[len(EXS[i]) :]
                    self.assertEqual(item.item.hash, hash_rem)
                    # TODO: Again, why are urls empty?
                    self.assertEqual(item.url, content)
        # Finally assert that non collision works normally
        content = "https://google.com"
        full_hash = "RGY6JE5M99DVYMWA5032GVYC"
        exp_code = full_hash[:SHORTCODE_MIN_LEN]
        exp_hash = full_hash[SHORTCODE_MIN_LEN:]
        item = Item.ensure(content)
        self.assertEqual(item.code, exp_code)
        self.assertEqual(item.hash, exp_hash)

    def test_raises_on_bad_content(self):
        """Test ensure raises an exception when given bad content."""
        with self.assertRaises(TypeError):
            LinkItem.ensure(b"foobar")


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
