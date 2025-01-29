# core/pic/model.py

from django.db import models
from django.core.exceptions import ValidationError

from core.models import Item


class PicItem(models.Model):
    FORMAT_CHOICES = [
        ("jpg", "JPEG"),
        ("gif", "GIF"),
        ("png", "PNG"),
    ]

    item = models.OneToOneField(Item, primary_key=True, on_delete=models.CASCADE)
    format = models.CharField(max_length=4, choices=FORMAT_CHOICES)
    size = models.IntegerField()

    @classmethod
    def ensure(cls, content):
        """
        Ensure that a PicItem exists for the given image content.
        Validates the image format based on magic bytes.

        Args:
            content (bytes): The image content to hash and store.
            ctype (str): Content type, default is 'pic'.

        Returns:
            PicItem: The existing or newly created PicItem.
        """
        if not isinstance(content, bytes):
            raise TypeError("Content must be bytes for PicItem.")

        # Determine image format based on magic bytes
        # TODO: Move binary format detection via magic bytes to own module
        # NOTE: New module should include enums/classes to label format type
        if content.startswith(b"\xff\xd8\xff"):
            img_format = "jpg"
        elif content.startswith(b"\x89PNG\r\n\x1a\n"):
            img_format = "png"
        elif content.startswith(b"GIF89a") or content.startswith(b"GIF87a"):
            img_format = "gif"
        else:
            msg = "Unsupported image format. Only jpg, png, and gif are supported."
            raise ValueError(msg)

        # Use Item.ensure to get or create the parent Item
        item = Item.ensure(content=content, ctype="pic")

        # Check if PicItem already exists
        pic_item, created = cls.objects.get_or_create(
            item=item,
            defaults={
                "size": len(content),
                "format": img_format,
            },
        )

        # TODO: Do we really want to save every time?
        if not created:
            # Update size and format if not created and there are any differences
            pic_item.size = len(content)
            pic_item.format = img_format
            pic_item.save()

        return pic_item

    # def __str__(self): -> str:
    #     return f"PicItem(code={self.item.code},format={self.format},size={self.size})"
