from django.db import models
from typing import Optional, TypedDict

from core.models.item import Item, Content, ItemContext


class LinkItemContext(TypedDict):
    item: ItemContext
    url: str


class LinkItem(models.Model):
    item = models.OneToOneField(Item, primary_key=True, on_delete=models.CASCADE)
    url = models.URLField(max_length=255)

    @classmethod
    def ensure(cls, content: Content, ctype: Optional[str] = "url") -> "LinkItem":
        if isinstance(content, bytes):
            raise TypeError("Content must be a string to create a LinkItem.")
        if ctype != "url":
            msg = "Warning: LinkItem.ensure called with"
            print(f"{msg} ctype={ctype}. Defaulting to 'url'.")

        # Ensure the parent Item exists
        item = Item.ensure(content, ctype="url")

        # Get or create the LinkItem instance
        args = {"item": item, "url": content}
        link_item, created = cls.objects.get_or_create(**args)
        if created:
            link_item.save()
        return link_item

    def context(self) -> LinkItemContext:
        item = self.item.context()
        return {"item": item, "url": self.url}
