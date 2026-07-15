# util/ module

Shared utilities with no domain dependencies.
Pure Python, no I/O.

## shortcode.py

Content hashing and code canonicalization.

- `hash_full_b32(data: bytes) -> str`:
  - BLAKE2b-120, Crockford base32, 24 chars
- `canonicalize_code(code: str) -> str`
  - normalize user input for DB lookup

## errors.py

Centralized exception hierarchy rooted at `DepoError`.
All exceptions carry `status` (HTTP code), `message`, `ctx` (dict),
`severity` (a `Severity` level), and `exception` (optional wrapped exception).

Domain bases:
`ConfigError`, `RepoError`, `ValidationError`, `ClassificationError`,
`ServerError`.

The auth errors sit directly under `DepoError` rather than sharing an auth
base. `AuthenticationError` is a failed credential check; `AuthRequiredError`
is a request reaching a gated route with no session. They are distinct
surfaces, not a hierarchy.

`Severity` is an `IntEnum` mirroring stdlib logging levels
(DEBUG 10 through CRITICAL 50);
each error's `severity` is a class attribute resolved by inheritance,
overridable per instance.

See [errors.md](../design/errors.md)
for the full hierarchy, severity decisions, and the logging seam.

## validate.py

Input validation for ingest pipeline.
Raises `PayloadSourceError` or `PayloadEmptyError` on invalid payload source.
Raises `PayloadTooLargeError` if size exceeds maximum.

```python
validate_payload(payload_bytes: bytes | None, payload_path: Path | None) -> None
validate_size(size: int, max_size: int) -> None
```

## password.py

Password hashing and verification using stdlib scrypt.
No external dependencies.

```python
hash_password(pw: str, *, n: int, r: int, p: int) -> str
verify_password(pw: str, stored: str) -> bool
```

`hash_password` salts with `os.urandom`, derives via `hashlib.scrypt`,
and returns a PHC-style string: `scrypt$n=...,r=...,p=...$salt_hex$digest_hex`.
`verify_password` parses the stored string, recomputes the digest, and
compares with `hmac.compare_digest`. Returns `False` on malformed input.
Cost parameters come from config (`scrypt_n`, `scrypt_r`, `scrypt_p`).
