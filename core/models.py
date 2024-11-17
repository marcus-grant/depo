from functools import partial
from django.db import models
from typing import Optional, Tuple

from .shortcode import hash_b32, SHORTCODE_MAX_LEN, SHORTCODE_MIN_LEN


# TODO: Shortcode isn't the right noun here, the property short_id is the real shortcode
# Create your models here.
class Shortcode(models.Model):
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

    @property
    def short_id(self) -> str:
        return self.id[: self.min_shortcode_len()]

    def min_shortcode_len(self, min_len: int = SHORTCODE_MIN_LEN) -> int:
        for length in range(min_len, SHORTCODE_MAX_LEN):
            candidate_code = self.id[:length]
            # Does this candidate code uniquely identify the item?
            matches = Shortcode.objects.filter(id__startswith=candidate_code)
            if matches.count() == 1:
                return length
            # If no matches, something is wrong
            elif matches.count() == 0:
                raise ValueError(f"No shortcode item of id: {id} found")
        return SHORTCODE_MAX_LEN

    # TODO: Good memoization candidate
    @classmethod
    def lookup_shortcode(cls, id_part: str) -> Optional["Shortcode"]:
        filter = cls.objects.filter
        fargs = {"id__startswith": id_part}
        return filter(**fargs).order_by("btime").first()

    @classmethod
    def generate(cls, content: str) -> "Shortcode":
        id = hash_b32(content)
        shortcode = cls.lookup_shortcode(id)
        if shortcode:
            return shortcode
        shortcode = cls(id=id, ctype="url", url=content)
        shortcode.save()
        return shortcode


# class ShortcodeManager(models.Manager):
#     @staticmethod
#     def lookup_shortcode(id_part: str) -> Optional[Shortcode]:
#         return (
#             Shortcode.objects.filter(id__startswith=id_part).order_by("btime").first()
#         )
#
#     @staticmethod
#     def gen_shortcode(content: str) -> Shortcode:
#         """Generator for a shortcode entity.
#         Primarily exists to standardize the hashing and encoding of content while
#         ensuring idempotency of the shortcode.
#         """
#         id = hash_b32(content)
#         shortcode = ShortcodeManager.lookup_shortcode(id)
#         if shortcode:
#             return shortcode
#         shortcode = Shortcode(id=id, ctype="url", url=content)
#         shortcode.save()
#         return shortcode
