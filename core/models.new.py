from django.db import models
from django.utils import timezone
from typing import Optional, Union, Tuple

from .shortcode import SHORTCODE_MAX_LEN, SHORTCODE_MIN_LEN


# Create your models here.
class Item(models.Model):
    CONTENT_TYPES = [
        ("url", "URL"),
        ("txt", "Text"),
        ("pic", "Picture"),
        # Add more types as needed
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
            matches = Item.objects.filter(id__startswith=candidate_code)
            if matches.count() == 1:
                return length
            elif matches.count() == 0:
                raise ValueError(f"No shortcode item of id: {id} found")
        return SHORTCODE_MAX_LEN
