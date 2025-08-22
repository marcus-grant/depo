# core/views/shortcode.py
from django.shortcuts import render

from core.models.item import Item


def shortcode_details(request, shortcode: str):
    item = Item.search_shortcode(shortcode)
    if not item:
        raise ValueError(f"Item with shortcode '{shortcode}' not found.")
    # TODO: Change to handle new context methods
    # TODO: Fix get_child and maybe consider having subitems handle search themselves
    link = item.get_child()
    ctx = link.context()
    
    # For PicItem, the template expects the pic data under 'pic' key
    if item.ctype == 'pic':
        # Move the PicItem-specific data under 'pic' key
        ctx = {
            'item': ctx['item'],
            'pic': {
                'url': ctx['url'],
                'format': ctx['format'],
                'size': ctx['size']
            }
        }
    
    return render(request, "shortcode-details.html", ctx)
