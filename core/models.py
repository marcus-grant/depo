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

    id = models.CharField(primary_key=True, max_length=SHORTCODE_MAX_LEN)
    ctype = models.CharField(max_length=3, choices=CONTENT_TYPES)
    url = models.URLField(max_length=192, blank=True, null=True)
    btime = models.DateTimeField(auto_now_add=True)
    mtime = models.DateTimeField(auto_now=True)

    # NOTE: Good memoization candidate
    # Consider using the @cached_property decorator
    # Also consider adding shortcode field, to guard against race condition and speed this up
    @property
    def shortcode(self, min_len: int = SHORTCODE_MIN_LEN) -> str:
        for length in range(min_len, SHORTCODE_MAX_LEN + 1):
            # Get candidate as prefix of id in growing lens & count matches
            candidate = self.id[:length]
            params = {"id__startswith": candidate, "btime__lte": self.btime}
            count = Item.objects.filter(**params).count()
            if count == 1:  # We found a unique shortcode at this len
                return candidate
        # If here, either hihgly unlikely hash collision or something is wrong
        return self.id[:SHORTCODE_MAX_LEN]

    # def shortcode(self, min_len: int = SHORTCODE_MIN_LEN) -> str:
    #     return self.id[: self.min_shortcode_len()]

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

    # NOTE: Good memoization candidate
    @classmethod
    def lookup_shortcode_item(cls, id_part: str) -> Optional["Item"]:
        filter = cls.objects.filter
        fargs = {"id__startswith": id_part}
        return filter(**fargs).order_by("btime").first()

    # NOTE: Add explicit and implicit ctype detection later
    # Implicit will use magic bytes encoded to b32 to determine content type if bytes
    # Will also analyze strs to determine if urls or text
    @classmethod
    def ensure(cls, content: Union[str, bytes]) -> "Item":
        """Ensure that a shortcode item hashed to the given content exists.
        If it exists, just use the lookup to retrieve its model instance.
        If not, then create a new Item instance and return."""
        id = hash_b32(content)
        item = cls.lookup_shortcode_item(id)
        if item:
            return item
        item = cls(id=id, ctype="url", url=content)
        item.save()
        return item
