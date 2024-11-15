import base64
import hashlib
from typing import Any, Union, Tuple

SHORTCODE_HASH_SIZE = 15  # 15 bytes = 120 bit or 24 base32 digits
if SHORTCODE_HASH_SIZE % 5 != 0:
    raise ValueError("Hash size must be a multiple of 5")
SHORTCODE_MAX_LEN = SHORTCODE_HASH_SIZE * 8 // 5
SHORTCODE_MIN_LEN = 8


# Library entrypoint, will probably become separate modules later import base64 import hashlib from typing import Any, Union, Tuple from web.models import Item SHORTCODE_HASH_SIZE = 15  # 15 bytes = 120 bit or 24 base32 digits SHORTCODE_MIN_LEN = 8 Crockford Base32 # U gets used for pads if needed
BASE32_CODE_HEX = "0123456789ABCDEFGHIJKLMNOPQRSTUV"
BASE32_CODE_HEX_SET = set(BASE32_CODE_HEX)
BASE32_PAD = "U"
BASE32_CODE_CROCK = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
BASE32_CODE_CROCK_SET = set(BASE32_CODE_CROCK + BASE32_PAD + "=")
TRANS_CROCK_TO_HEX = str.maketrans(BASE32_CODE_CROCK, BASE32_CODE_HEX)
TRANS_HEX_TO_CROCK = str.maketrans(BASE32_CODE_HEX, BASE32_CODE_CROCK)


# TODO: Rename function so it doesn't shadown built-ins
def hash_std(data: Union[str, bytes]) -> bytes:
    """Creates a hex digest of the passed data by hashing with blake2b"""
    # Ensure textual data is always UTF8 binary streams
    if isinstance(data, str):
        data = data.encode("utf-8")

    # Create hasher
    hasher = hashlib.blake2b(digest_size=SHORTCODE_HASH_SIZE)

    # Update hash object with data
    hasher.update(data)

    # Return hasher object so usesr can take either the hexdigest or bin
    return hasher.digest()


def validate_b32_encode(data: Any) -> bytes:
    if isinstance(data, str):
        data = data.encode("utf-8")
    elif not isinstance(data, bytes):
        raise TypeError(f"Expected str or bytes, got: {type(data)}")
    return data


def encode_b32_hex(data: Union[str, bytes]) -> str:
    data = validate_b32_encode(data)
    enc_hex_b = base64.b32hexencode(data)
    enc_hex = enc_hex_b.decode("utf-8")
    return enc_hex


def encode_b32(data: Union[str, bytes]) -> str:
    # Base32 encode with hex extension variant,
    # ...re-encoded to UTF and enforce upper case
    enc_hex = encode_b32_hex(data)

    # Translate to Crockford Base32
    enc_crock = enc_hex.translate(TRANS_HEX_TO_CROCK)
    # Use U for padding instead of =
    enc_crock = enc_crock.replace("=", BASE32_PAD)
    return enc_crock


def validate_b32_decode(data: str, strict: bool = False) -> str:
    if strict:
        for ch in data:
            if ch not in BASE32_CODE_CROCK_SET:
                raise ValueError(f"Invalid character in base32 data: {ch}")
    # Normalize to uppercase
    data = data.upper()
    # Normalize mistaken chars into corresponding codes
    # This includes O->0, I->1, L->1
    data = data.replace("I", "1").replace("L", "1")
    data = data.replace("O", "0")
    # # Normalize padding to set pad character
    data = data.replace("=", BASE32_PAD)
    # Final check for invalid characters after normalization
    for ch in data:
        if ch not in BASE32_CODE_CROCK_SET:
            raise ValueError(f"Invalid character in base32 data: {ch}")
    return data


def decode_b32_hex(data: str) -> bytes:
    data_enc = base64.b32hexdecode(data)
    return data_enc


def decode_b32(encoded: str, strict: bool = False) -> bytes:
    valid_encoded = validate_b32_decode(encoded, strict)
    valid_encoded = valid_encoded.replace(BASE32_PAD, "=")
    hex_enc = valid_encoded.translate(TRANS_CROCK_TO_HEX)
    dec_data = decode_b32_hex(hex_enc)
    return dec_data


def hash_b32(data: Union[str, bytes]) -> str:
    """Hashes data and encodes it with Base32"""
    hashed = hash_std(data)
    encoded = encode_b32(hashed)
    return encoded
