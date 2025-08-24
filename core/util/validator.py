from urllib.parse import urlparse


def looks_like_url(text: str) -> bool:
    """Check if text looks like a URL"""
    if not text or not isinstance(text, str):
        return False

    text = text.strip()

    try:
        parsed = urlparse(text)
        if parsed.scheme:
            return True
        parsed_with_https = urlparse(f"https://{text}")
        if (
            parsed_with_https.netloc
            and "." in parsed_with_https.netloc
            and " " not in text
        ):
            netloc = parsed_with_https.netloc
            if len(netloc) < 100 and not any(
                char in netloc for char in [" ", "\t", "\n"]
            ):
                return True
        return False
    except Exception:
        return False