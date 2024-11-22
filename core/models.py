from django.db import models
from typing import Optional, Union

from .shortcode import hash_b32, SHORTCODE_MAX_LEN, SHORTCODE_MIN_LEN


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
    url = models.URLField(max_length=192, blank=True, null=True)
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
    def ensure(cls, content: Union[str, bytes]) -> "Item":
        """Ensure that a shortcode item hashed to the given content exists.
        If it exists, just use the lookup to retrieve its model instance.
        If not, then create a new Item instance and return."""
        hash = hash_b32(content)
        item = cls.search_shortcode(hash)
        if item:
            return item
        item = cls(id=id, ctype="url", url=content)
        item.save()
        return item

    # def min_shortcode_len(self, min_len: int = SHORTCODE_MIN_LEN) -> int:
    #     for length in range(min_len, SHORTCODE_MAX_LEN):
    #         candidate_code = self.id[:length]
    #         # Does this candidate code uniquely identify the item?
    #         matches = Item.objects.filter(id__startswith=candidate_code)
    #         if matches.count() == 1:
    #             return length
    #         # If no matches, something is wrong
    #         elif matches.count() == 0:
    #             raise ValueError(f"No shortcode item of id: {id} found")
    #     return SHORTCODE_MAX_LEN
