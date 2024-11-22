from datetime import datetime, timezone
from django.test import TestCase
from django.db import models
from unittest.mock import patch

from .models import Item
from .shortcode import SHORTCODE_MAX_LEN, SHORTCODE_MIN_LEN


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
            "url": models.URLField,
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

    def test_url_field_constraints(self):
        """Test that the url field has the expected constraints & atrributes"""
        url_field = Item._meta.get_field("url")
        self.assertEqual(getattr(url_field, "max_length", None), 192)
        self.assertTrue(getattr(url_field, "blank", False))
        self.assertTrue(getattr(url_field, "null", True))

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
        url1 = "https://example1.com"
        url2 = "https://example2.com"
        url3 = "https://example3.com"
        Item.objects.create(code="123456", hash="ABC", ctype="url", url=url1)
        Item.objects.create(code="123456Z", hash="ABC", ctype="url", url=url2)
        Item.objects.create(code="ZZZZZZ", hash="ABC", ctype="url", url=url3)

        # Search for the item
        found_item1 = Item.search_shortcode("123456")
        found_item2 = Item.search_shortcode("123456Z")
        found_item3 = Item.search_shortcode("ZZZZZZ")

        # Ensure the item was found
        if not found_item1:
            raise Exception("Item not found")
        if not found_item2:
            raise Exception("Item not found")
        if not found_item3:
            raise Exception("Item not found")

        # Assert that the item was found
        self.assertEqual(found_item1.code, "123456")
        self.assertEqual(found_item2.code, "123456Z")
        self.assertEqual(found_item3.code, "ZZZZZZ")
        self.assertEqual(found_item1.hash, found_item2.hash)
        self.assertEqual(found_item3.hash, found_item1.hash)
        self.assertEqual(found_item3.hash, "ABC")
        self.assertEqual(found_item1.url, url1)
        self.assertEqual(found_item2.url, url2)
        self.assertEqual(found_item3.url, url3)

    def test_failure(self):
        """Test search_shortcode returns None when item not found."""
        # Search for an item that doesn't exist
        found_item = Item.search_shortcode("D0ESN0T3X1ST")
        # Assert that the item was not found
        self.assertIsNone(found_item)


class ItemEnsureTest(TestCase):
    # Known hash_b32 values for different content
    GOOG_URL = "https://google.com"
    GOOG_H32 = "RGY6JE5M99DVYMWA5032GVYC"
    CONT_B32 = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"

    def test_fields_assigned(self):
        # """Test ensure assigns fields correctly."""
        # item = Item.ensure(self.GOOG_URL)
        ## Create timestamp to compare with Item's btime & mtime fields
        # now = datetime.now(timezone.utc)
        # self.assertEqual(item.id, self.GOOG_H32)
        # self.assertEqual(item.url, self.GOOG_URL)
        # self.assertEqual(item.ctype, "url")
        # self.assertLessEqual((now - item.btime).total_seconds(), 10)
        # self.assertLessEqual((now - item.mtime).total_seconds(), 10)
        pass

    def test_creates(self):
        # """Assert that ensure creates an item if none of that hash exists."""
        ## First assert no items exist
        # self.assertFalse(Item.objects.exists())
        ## Use ensure to create an item
        # Item.ensure(self.GOOG_URL)
        ## Assert that the item was created
        # self.assertEqual(Item.objects.count(), 1)
        pass

    def test_idempotency(self):
        # """Test ensure is idempotent, doesnt create duplicate items in backend.
        # This also tests that other fields are assigned correctly and the same."""
        # # Call ensure first time
        # item1 = Item.ensure(self.GOOG_URL)
        # self.assertEqual(item1.id, self.GOOG_H32)
        # self.assertEqual(item1.url, self.GOOG_URL)

        # # Call ensure second time
        # item2 = Item.ensure(self.GOOG_URL)
        # # Compare id url and shortcodes of both items
        # self.assertEqual(item2.id, item1.id)
        # self.assertEqual(item2.url, item1.url)
        # self.assertEqual(item2.shortcode, item1.shortcode)

        # # Ensure only one item was created in the backend
        # self.assertEqual(Item.objects.count(), 1)
        pass


class TestShortcodeProp(TestCase):
    COUNT_B32 = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
    PREFIX = COUNT_B32[:SHORTCODE_MIN_LEN]
    ID0 = f"{PREFIX}0000"
    ID1 = f"{PREFIX}0001"
    ID2 = f"{PREFIX}0002"
    ID3 = f"{PREFIX}0003"
    ID4 = f"{PREFIX}0004"
    IDS = [ID0, ID1, ID2, ID3, ID4]
    EX0 = PREFIX
    EX1 = f"{PREFIX}0"
    EX2 = f"{PREFIX}00"
    EX3 = f"{PREFIX}000"
    EX4 = f"{PREFIX}0004"
    EXS = [EX0, EX1, EX2, EX3, EX4]
    pass

    # def test_collision(self):
    #     """Test that min_shortcode_len returns the correct length."""
    #     # Loop through expected ids and shortcodes to test min_shortcode_len
    #     for i, id in enumerate(self.IDS):
    #         # Indicate to test runner which iteration failed
    #         with self.subTest(i=i, id=id, expect=self.EXS[i]):
    #             expect = self.EXS[i]
    #             url = f"https://example{i}.com"
    #             item = Item.objects.create(id=id, ctype="url", url=url)
    #             if i == 1:
    #                 breakpoint()
    #                 # pass
    #             self.assertEqual(item.shortcode, expect)

    # def test_ensure_creates
    # @patch("core.models.hash_b32")
    # def test_with_shortcode_collision(self, mock_h32):
    #     """Test ensure handles prefix collisions by increasing shortcode len."""
    #     # Make the mock return same value everytime for content hashes
    #     prefix = self.CONT_B32[:SHORTCODE_MIN_LEN]
    #     id1 = f"{prefix}0000"
    #     id2 = f"{prefix}0001"
    #     id3 = f"{prefix}0002"
    #     id4 = f"{prefix}0003"
    #     id5 = f"{prefix}0004"
    #     mock_h32.return_value = [id1, id2, id3, id4, id5]
    #     # Create expected shortcodes for ids based on order of creation
    #     exp1 = prefix
    #     exp2 = f"{prefix}0"
    #     exp3 = f"{prefix}00"
    #     exp4 = f"{prefix}000"
    #     exp5 = f"{prefix}0004"

    #     # Ensure all those items are created w/ that sequence of ids
    #     item1 = Item.ensure("Hello, World!")
    #     item2 = Item.ensure("FooBar")
    #     item3 = Item.ensure("FooBarBaz")
    #     item4 = Item.ensure("DEADBEEF")
    #     item5 = Item.ensure("C0FFEE")

    #     # Call ensure for first time with any content
    #     # and assert its id is the mocked return
    #     item1 = Item.ensure("Hello, World!")
    #     self.assertEqual(item1.id, self.CONT_B32)

    #     # Call ensure again on different content and same as mock return
    #     item2 = Item.ensure("FooBar")
    #     self.assertEqual(item2.id, self.CONT_B32)

    #     # Now check that the later shortcode property has one more digit
    #     self.assertEqual(item1.shortcode, item1.id[:SHORTCODE_MIN_LEN])
    #     self.assertEqual(item2.shortcode, item2.id[: SHORTCODE_MIN_LEN + 1])
