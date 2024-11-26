from django.db import models
from typing import Optional, Union, Literal, TYPE_CHECKING

from .shortcode import hash_b32, SHORTCODE_MAX_LEN, SHORTCODE_MIN_LEN

if TYPE_CHECKING:
    from .models import LinkItem

CTYPE = Literal["url", "txt", "pic"]


# Create your models here.
class Item(models.Model):
    CONTENT_TYPES = [
        ("url", "URL"),
        ("txt", "Text"),
        ("pic", "Picture"),
    ]

    code = models.CharField(primary_key=True, max_length=SHORTCODE_MAX_LEN)
    hash = models.CharField(max_length=SHORTCODE_MAX_LEN)  # Remaining hash minus code
    ctype = models.CharField(max_length=3, choices=CONTENT_TYPES)
    btime = models.DateTimeField(auto_now_add=True)
    mtime = models.DateTimeField(auto_now=True)
    # TODO: Refactor mtime to ctime because like POSIX, ctime is metadata change
    # mtime in POSIX implies content change, which never happens here.

    # NOTE: Good memoization candidate
    @classmethod
    def search_shortcode(cls, shortcode: str) -> Optional["Item"]:
        """
        Lookup an Item by its shortcode.

        Args:
            shortcode (str): The shortcode to lookup.

        Returns:
            Optional[Item]: The Item if found, else None.
        """
        try:
            return cls.objects.get(code=shortcode)
        except cls.DoesNotExist:
            return None

    # NOTE: Add explicit and implicit ctype detection later
    # Implicit will use magic bytes encoded to b32 to determine content type if bytes
    # Will also analyze strs to determine if urls or text
    @classmethod
    def ensure(cls, content: Union[str, bytes], ctype: CTYPE = "url") -> "Item":
        """
        Ensure that a shortcode item hashed to the given content exists.
        If it exists, retrieve its model instance.
        If not, create a new Item instance and return it.

        Args:
            content (Union[str, bytes]): The content to hash and ensure existence.

        Returns:
            Item: The existing or newly created Item.
        """
        # First validate the ctype
        if ctype not in dict(cls.CONTENT_TYPES):
            raise TypeError(f"Invalid ctype in Item.ensure: {ctype}.")

        # Generate all possible code prefixes from SHORTCODE_MIN_LEN to the length of full_hash
        full_hash = hash_b32(content)
        likely_lens = range(SHORTCODE_MIN_LEN, len(full_hash) + 1)
        likely_codes = [full_hash[:length] for length in likely_lens]

        # Fetch all existing items with codes that are prefixes of full_hash
        select = cls.objects.filter
        current_items = select(code__in=likely_codes).only("code", "hash")

        # Create a set for faster lookup
        current_codes = {item.code: item.hash for item in current_items}

        # TODO: Pull functionality into own function/method
        # Iterate through possible codes to find the shortest unique one
        for code in likely_codes:
            hash_rem = full_hash[len(code) :]  # Remaining hash after code
            existing_hash = current_codes.get(code)

            if existing_hash is None:
                # Code is unique; create and return the new item
                fields = {
                    "code": code,
                    "hash": hash_rem,
                    "ctype": ctype,
                }
                new_item = cls(**fields)
                new_item.save()
                return new_item
            elif existing_hash == hash_rem:
                # Exact match found; return the existing item
                return cls.objects.get(code=code)

        # If all possible prefixes are taken, raise an exception
        raise ValueError("Unable to generate a unique shortcode with the given hash.")

    # TODO: Add other content types in Union
    def get_child(self) -> Union["Item", "LinkItem"]:
        child = None
        for field in self._meta.fields:
            if field.name == "url":
                child = getattr(self, field.name)
                break
        return child or self


class LinkItem(Item):
    url = models.URLField(max_length=255)

    @classmethod
    def ensure(
        cls, content: Union[str, bytes], ctype: Optional[str] = None
    ) -> "LinkItem":
        if isinstance(content, bytes):
            raise TypeError("Content must be a string to create a LinkItem.")
        if ctype != "url":
            msg = "Warning: LinkItem.ensure called with "
            print(f"{msg}ctype={ctype}. Defaulting to 'url'.")
        item = super().ensure(content, "url")
        # Get or create LinkItem associated with this Item
        link_item, _ = cls.objects.get_or_create(pk=item.pk, defaults={"url": content})
        return link_item


# NOTE: Unique item creation
# # Existing hashing and code generation logic...
#        # After determining that the code is unique:
#        if ctype == 'url':
#            new_item = URLItem(
#                code=code,
#                hash=hash_rem,
#                ctype=ctype,
#                url=content if isinstance(content, str) else None,
#            )
#        elif ctype == 'txt':
#            new_item = TextItem(
#                code=code,
#                hash=hash_rem,
#                ctype=ctype,
#                text=content.decode('utf-8') if isinstance(content, bytes) else content,
#            )
#        elif ctype == 'pic':
#            new_item = PictureItem(
#                code=code,
#                hash=hash_rem,
#                ctype=ctype,
#                image=content,  # Assuming content is an uploaded file
#            )
#        else:
#            raise ValueError("Invalid content type.")
#        new_item.save()
#        return new_item
#
