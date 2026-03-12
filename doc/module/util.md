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
All exceptions carry `status` (HTTP code), `message`, and `ctx` (dict).
Domain bases: `RepoError`, `ValidationError`, `ClassificationError`, `ServerError`.
See [errors.md](../design/errors.md) for the full hierarchy and patterns.

## validate.py

Input validation for ingest pipeline.
Raises `PayloadSourceError` or `PayloadEmptyError` on invalid payload source.
Raises `PayloadTooLargeError` if size exceeds maximum.

```python
validate_payload(payload_bytes: bytes | None, payload_path: Path | None) -> None
validate_size(size: int, max_size: int) -> None
```
