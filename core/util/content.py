from core.util.validator import looks_like_url


def classify_type(request) -> str:
    """
    Classify content type based on request data.
    Returns 'image', 'url', or 'text'.
    """
    # Check if it's a base-64 image or has uploaded files
    if getattr(request, "is_base64_image", False) or request.FILES:
        return "image"

    # Check raw input for URL vs text
    raw_input = request.POST.get("content", "").strip()
    if looks_like_url(raw_input):
        return "url"

    return "text"