from b3c32 import coerce_crockford_b32, hash_b32

_SHORTCODE_BITS = 120


def hash_full_b32(data: bytes) -> str:
    """Compute the canonical shortcode for content.

    Depo's width choice, 120 bits, applied to the b3c32 contract
    pipeline. Thin by design: the contract layer owns hashing and
    encoding; depo owns only the width.

    Args:
        data: The bytes to hash.

    Returns:
        A 24-character canonical Crockford Base32 shortcode.
    """
    return hash_b32(data, _SHORTCODE_BITS)


def canonicalize_code(code: str) -> str:
    """Depo's coercion boundary for user-supplied codes.

    Delegates to b3c32's coerce; depo-specific search arguments
    accrete here later without touching the contract layer.

    Args:
        code: User-supplied code string.

    Returns:
        Canonical uppercase string with ambiguous chars normalized.

    Raises:
        CoercionError: If code is empty or contains invalid characters.
    """
    return coerce_crockford_b32(code)
