# tests/factories/payloads.py
"""
Factory functions for test payloads.
Author: Marcus Grant
Date: 2026-01-26
License: Apache-2.0
"""

from io import BytesIO

from PIL import Image


def gen_image(fmt: str, width: int, height: int) -> bytes:
    """Generate minimal valid image bytes."""
    buf = BytesIO()
    img = Image.new("RGB", (width, height), color=(255, 0, 0))
    img.save(buf, format=fmt)
    return buf.getvalue()
