from functools import partial
from django.db import models
from typing import Optional, Tuple

from .shortcode import hash_b32, SHORTCODE_MAX_LEN, SHORTCODE_MIN_LEN


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


class ShortcodeManager(models.Manager):
    def lookup_shortcode(self, id_part: str) -> Optional[Shortcode]:
        shortcode = self.filter(id__startswith=id_part).order_by("btime").first()
        if shortcode:
            return shortcode
        return None

    def gen_shortcode(self, content: str) -> Tuple[Shortcode, str]:
        id = hash_b32(content)
        shortcode = self.lookup_shortcode(id)
        if shortcode:
            return shortcode, id[: shortcode.min_shortcode_len()]
        shortcode = Shortcode(id=id, ctype="url", url=content)
        shortcode.save()
        return shortcode, id[: shortcode.min_shortcode_len()]
