# core/tests/models/test_pic.py

from datetime import datetime
from django.test import TestCase
from django.db import models
from django.utils import timezone
from unittest.mock import patch

from core.models.pic import PicItem
from core.models import Item
from core.util.shortcode import hash_b32, SHORTCODE_MAX_LEN, SHORTCODE_MIN_LEN


class PicItemSchemaTest(TestCase):
    def test_picitem_fields(self):
        """Test that PicItem has correct fields."""
        pic_item = PicItem()
        fnames = [field.name for field in pic_item._meta.get_fields()]
        expected_fields = {
            "item": models.OneToOneField,
            "format": models.CharField,
            "size": models.IntegerField,
        }

        for field_name, field_type in expected_fields.items():
            self.assertIn(field_name, fnames)
            self.assertIsInstance(PicItem._meta.get_field(field_name), field_type)


class PicItemEnsureTest(TestCase):
    VALID_JPG_CONTENT = b"\xff\xd8\xff\xe0" + b"\x00" * 100  # JPEG magic bytes
    VALID_PNG_CONTENT = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100  # PNG magic bytes
    VALID_GIF_CONTENT = b"GIF89a" + b"\x00" * 100  # GIF magic bytes
    INVALID_CONTENT = b"\x00\x01\x02\x03"  # Unsupported format

    @patch("core.models.item.hash_b32")
    def test_create_picitem_with_jpg(self, mock_hash_b32):
        """Test that ensure creates a PicItem for valid JPEG content."""
        mock_hash_b32.return_value = "PIC12345HASH1"

        pic_item = PicItem.ensure(content=self.VALID_JPG_CONTENT)

        # Assertions
        self.assertEqual(PicItem.objects.count(), 1)
        self.assertEqual(Item.objects.count(), 1)

        self.assertEqual(pic_item.item.code, "PIC12345")
        self.assertEqual(pic_item.item.hash, "HASH1")
        self.assertEqual(pic_item.item.ctype, "pic")
        self.assertEqual(pic_item.size, len(self.VALID_JPG_CONTENT))
        self.assertEqual(pic_item.format, "jpg")

    @patch("core.models.item.hash_b32")
    def test_create_picitem_with_png(self, mock_hash_b32):
        """Test that ensure creates a PicItem for valid PNG content."""
        mock_hash_b32.return_value = "PIC22345HASH2"

        pic_item = PicItem.ensure(content=self.VALID_PNG_CONTENT)

        # Assertions
        self.assertEqual(PicItem.objects.count(), 1)
        self.assertEqual(Item.objects.count(), 1)

        self.assertEqual(pic_item.item.code, "PIC22345")
        self.assertEqual(pic_item.item.hash, "HASH2")
        self.assertEqual(pic_item.item.ctype, "pic")
        self.assertEqual(pic_item.size, len(self.VALID_PNG_CONTENT))
        self.assertEqual(pic_item.format, "png")

    @patch("core.models.item.hash_b32")
    def test_create_picitem_with_gif(self, mock_hash_b32):
        """Test that ensure creates a PicItem for valid GIF content."""
        mock_hash_b32.return_value = "PIC32345HASH3"

        pic_item = PicItem.ensure(content=self.VALID_GIF_CONTENT)

        # Assertions
        self.assertEqual(PicItem.objects.count(), 1)
        self.assertEqual(Item.objects.count(), 1)

        self.assertEqual(pic_item.item.code, "PIC32345")
        self.assertEqual(pic_item.item.hash, "HASH3")
        self.assertEqual(pic_item.item.ctype, "pic")
        self.assertEqual(pic_item.size, len(self.VALID_GIF_CONTENT))
        self.assertEqual(pic_item.format, "gif")

    def test_ensure_with_invalid_content_raises(self):
        """Test ensure raises an exception for unsupported content format"""
        with self.assertRaises(ValueError) as context:
            PicItem.ensure(content=self.INVALID_CONTENT)
        self.assertIn("Unsupported image format.", str(context.exception))

    @patch("core.models.item.hash_b32")
    def test_idempotency_of_ensure(self, mock_hash_b32):
        """Test that multiple calls to ensure with the same content do not create duplicates."""
        mock_hash_b32.return_value = "PIC42345HASH4"

        pic_item1 = PicItem.ensure(content=self.VALID_JPG_CONTENT)
        pic_item2 = PicItem.ensure(content=self.VALID_JPG_CONTENT)

        self.assertEqual(PicItem.objects.count(), 1)
        self.assertEqual(Item.objects.count(), 1)
        self.assertEqual(pic_item1, pic_item2)

    @patch("core.models.item.hash_b32")
    def test_existing_item_usage(self, mock_hash_b32):
        """Ensures it uses an existing Item if one with the same code and hash exists."""
        mock_hash_b32.return_value = "1234567890"

        # Create an existing Item
        existing_item = Item.objects.create(code="12345678", hash="90", ctype="pic")
        kwargs = {"item": existing_item, "size": 2048, "format": "jpg"}
        pic_item_existing = PicItem.objects.create(**kwargs)

        # Call ensure with content that hashes to the same code and hash
        pic_item_new = PicItem.ensure(content=self.VALID_JPG_CONTENT)

        self.assertEqual(PicItem.objects.count(), 1)  # No new PicItem created
        self.assertEqual(pic_item_new, pic_item_existing)


class PicItemContextTest(TestCase):
    def test_correct_return_schema(self):
        """Returns expected dictionary structure"""
        # Arrange: Item instance
        item = Item.objects.create(code="P1C1", hash="HASH1", ctype="pic")

        # Act: Create pic then get context from it
        pic = PicItem.objects.create(item=item, format="jpg", size=1024)
        ctx = pic.context()

        # Assert: Check the structure and contents of the context
        expected_context = {
            "item": {
                "code": "P1C1",
                "hash": "P1C1HASH1",
                "ctype": "pic",
                "btime": item.btime.isoformat(),
                "mtime": item.mtime.isoformat(),
            },
            "size": 1024,
            "format": "jpg",
        }

        self.assertEqual(ctx, expected_context)
