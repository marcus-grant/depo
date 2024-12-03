from datetime import datetime, timezone
from django.test import TestCase
from django.db import models
from unittest.mock import patch

from core.models import Item
from core.link.models import LinkItem
from core.util.shortcode import SHORTCODE_MAX_LEN, SHORTCODE_MIN_LEN


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
            "item": models.OneToOneField,
            "url": models.URLField,
        }

        for expect_name, expect_type in expect.items():
            with self.subTest(field_name=expect_name):
                self.assertIn(expect_name, field_names)
                field = LinkItem._meta.get_field(expect_name)
                self.assertIsInstance(field, expect_type)

    def test_access_item_fields(self):
        """Test that LinkItem can access "parent" "item" fields"""
        # Create a LinkItem and its parent Item
        item_args = {"code": "G00G", "hash": "L3", "ctype": "url"}
        item = Item.objects.create(**item_args)
        link_args = {"item": item, "url": "https://google.com"}
        link = LinkItem.objects.create(**link_args)

        # Retrieve all fields from both parent and child of model instance
        retrieved_link = LinkItem.objects.get(pk=link.pk)

        # Define expected fields and their values
        expect_item = {
            "code": item_args["code"],
            "hash": item_args["hash"],
            "ctype": item_args["ctype"],
        }
        expect_link = {"item": item, "url": link_args["url"]}

        # Verify LinkItem fields
        for field, expect in expect_link.items():
            with self.subTest(field_name=field):
                self.assertEqual(getattr(retrieved_link, field), expect)

        # Access related Item instance
        for field, expect in expect_item.items():
            with self.subTest(field_name=field):
                self.assertEqual(getattr(retrieved_link.item, field), expect)

        # Verify 'btime' and 'mtime' fields are accessible
        self.assertIsNotNone(getattr(retrieved_link.item, "btime", None))
        self.assertIsNotNone(getattr(retrieved_link.item, "mtime", None))

        # Verify hash combines correctly
        full_hash = retrieved_link.item.code + retrieved_link.item.hash
        self.assertEqual(full_hash, "G00GL3")


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

    @patch("core.models.Item.ensure")
    def test_existing_item(self, mock_item_ensure):
        """Test that LinkItem.ensure uses existing Item when code collision occurs"""
        # Setup mock to return an existing Item
        existing_item = Item(code="G00G", hash="L3", ctype="url")
        existing_item.save()  # Ensure the Item is saved to the database
        mock_item_ensure.return_value = existing_item

        # Define content that would result in a hash collision
        content = "https://example.com"

        # Call LinkItem.ensure
        link_item = LinkItem.ensure(content)

        # Assert Item.ensure was called once with correct arguments
        mock_item_ensure.assert_called_once_with(content, ctype="url")

        # Verify that LinkItem is linked to the existing Item
        self.assertEqual(link_item.item, existing_item)
        self.assertEqual(link_item.url, content)

    @patch("core.models.Item.ensure")
    def test_new_item_creation(self, mock_item_ensure):
        """Test that LinkItem.ensure creates a new Item when no collision occurs"""
        # Setup mock to create and return a new Item
        new_item = Item(code="G00G", hash="L3", ctype="url")
        new_item.save()  # Save the Item to the database to satisfy foreign key constraints
        mock_item_ensure.return_value = new_item

        # Define content that would result in no hash collision
        content = "https://newexample.com"

        # Call LinkItem.ensure
        link_item = LinkItem.ensure(content)

        # Assert Item.ensure was called once with correct arguments
        mock_item_ensure.assert_called_once_with(content, ctype="url")

        # Verify that LinkItem is linked to the new Item
        self.assertEqual(link_item.item, new_item)
        self.assertEqual(link_item.url, content)

    @patch("core.models.hash_b32")
    def test_shortcode_collision(self, mock_h32):
        """Test shortcode collision handling in Item.ensure via LinkItem.ensure"""
        COUNT_B32 = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
        PREFIX = COUNT_B32[:SHORTCODE_MIN_LEN]
        HASH1, EX1 = f"{PREFIX}000", f"{PREFIX}"
        HASH2, EX2 = f"{PREFIX}001", f"{PREFIX}0"
        HASH3, EX3 = f"{PREFIX}002", f"{PREFIX}00"
        HASH4, EX4 = f"{PREFIX}003", f"{PREFIX}003"
        HASH5, EX5 = f"{PREFIX}004", f"{PREFIX}004"
        HASHES = [HASH1, HASH2, HASH3, HASH4, HASH5]
        EXS = [EX1, EX2, EX3, EX4, EX5]

        with patch("core.models.Item.ensure") as mock_item_ensure:
            for i, hash_val in enumerate(HASHES):
                mock_h32.return_value = hash_val

                # Setup Item.ensure to return a new Item with the expected code and hash
                expected_code = EXS[i]
                expected_hash = hash_val[len(expected_code) :]
                new_item = Item(code=expected_code, hash=expected_hash, ctype="url")
                new_item.save()  # Save the Item to the database
                mock_item_ensure.return_value = new_item

                with self.subTest(i=i, hash=hash_val, expect=EXS[i]):
                    content = f"https://example{i}.com"
                    link_item = LinkItem.ensure(content)

                    # Assert that Item.ensure was called correctly
                    mock_item_ensure.assert_called_with(content, ctype="url")

                    # Verify that the LinkItem's item fields are correctly assigned
                    self.assertEqual(link_item.item.code, EXS[i])
                    hash_rem = hash_val[len(EXS[i]) :]
                    self.assertEqual(link_item.item.hash, hash_rem)

                    # Verify that the LinkItem's url field is correctly assigned
                    self.assertEqual(link_item.url, content)

    def test_raises_on_bad_content(self):
        """Test ensure raises an exception when given bad content."""
        with self.assertRaises(TypeError):
            LinkItem.ensure(b"foobar")


class LinkItemContextTest(TestCase):
    def test_context(self):
        """Test that LinkItem.context returns the expected dictionary."""
        # Create a LinkItem instance
        item = Item(code="G00G", hash="L3", ctype="url")
        item.save()
        link_item = LinkItem(item=item, url="https://google.com")
        link_item.save()
        now = f"{datetime.now(timezone.utc):%Y-%m-%dT%H:%M}"
        link_ctx = link_item.context()
        # Define the expected context dictionary
        expect = {
            "item": {
                "code": "G00G",
                "hash": "G00GL3",
                "ctype": "url",
                "btime": item.btime.isoformat(),
                "mtime": item.mtime.isoformat(),
            },
            "url": "https://google.com",
        }
        # Verify keys
        self.assertIn("url", link_ctx)
        self.assertIn("item", link_ctx)
        self.assertIn("code", link_ctx["item"])
        self.assertIn("hash", link_ctx["item"])
        self.assertIn("ctype", link_ctx["item"])
        self.assertIn("btime", link_ctx["item"])
        self.assertIn("mtime", link_ctx["item"])

        # Verify values
        self.assertEqual(link_ctx["url"], expect["url"])
        self.assertEqual(link_ctx["item"]["code"], expect["item"]["code"])
        self.assertEqual(link_ctx["item"]["hash"], expect["item"]["hash"])
        self.assertEqual(link_ctx["item"]["ctype"], expect["item"]["ctype"])
        self.assertEqual(link_ctx["item"]["btime"], expect["item"]["btime"])
        self.assertEqual(link_ctx["item"]["btime"], expect["item"]["btime"])


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
