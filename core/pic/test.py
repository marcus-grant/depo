# core/pic/test.py

from django.test import TestCase
from django.db import models

from core.pic.model import PicItem
from core.models import Item


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
