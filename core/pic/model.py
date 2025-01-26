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

    # def __str__(self): -> str:
    #     return f"PicItem(code={self.item.code},format={self.format},size={self.size})"
