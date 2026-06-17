# src/depo/util/password.py
"""
Password hashing and verification using stdlib scrypt.
Author: Marcus Grant
Created: 2026-06-17
License: Apache-2.0
"""

import hashlib
import hmac
import os


def hash_password(pw: str, *, n: int, r: int, p: int) -> str:
    """Hash a password using scrypt, returning a PHC-style string."""
    salt = os.urandom(16)
    dk = hashlib.scrypt(pw.encode(), salt=salt, n=n, r=r, p=p)
    return f"scrypt$n={n},r={r},p={p}${salt.hex()}${dk.hex()}"


def verify_password(pw: str, stored: str) -> bool:
    """Verify a password against a stored PHC-style scrypt hash."""
    try:
        algo, params, salt_hex, digest_hex = stored.split("$")
    except ValueError:
        return False
    if algo != "scrypt":
        return False
    try:
        param_dict = dict(kv.split("=") for kv in params.split(","))
        n = int(param_dict["n"])
        r = int(param_dict["r"])
        p = int(param_dict["p"])
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
    except (KeyError, ValueError):
        return False
    dk = hashlib.scrypt(pw.encode(), salt=salt, n=n, r=r, p=p)
    return hmac.compare_digest(dk, expected)
