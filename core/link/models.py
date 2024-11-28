from django.db import models
from typing import Optional

from core.models import Item, Content


class LinkItem(models.Model):
    item = models.OneToOneField(Item, primary_key=True, on_delete=models.CASCADE)
    url = models.URLField(max_length=255)

    @classmethod
    def ensure(cls, content: Content, ctype: Optional[str] = "url") -> "LinkItem":
        if isinstance(content, bytes):
            raise TypeError("Content must be a string to create a LinkItem.")
        if ctype != "url":
            print(
                f"Warning: LinkItem.ensure called with ctype={ctype}. Defaulting to 'url'."
            )

        # Ensure the parent Item exists
        item = Item.ensure(content, ctype="url")

        # Get or create the LinkItem instance
        link_item, _ = cls.objects.get_or_create(item=item, defaults={"url": content})
        return link_item
