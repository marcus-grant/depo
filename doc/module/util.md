# util/ module

Shared utilities with no domain dependencies.
Pure Python, no I/O.

## shortcode.py

Content hashing and code canonicalization.

- `hash_full_b32(data: bytes) -> str`:
  - BLAKE2b-120, Crockford base32, 24 chars
- `canonicalize_code(code: str) -> str`
  - normalize user input for DB lookup

## validate.py

Input validation for ingest pipeline.
Raises on failure, returns None on success.

```python
validate_payload(payload_bytes: bytes | None, payload_path: Path | None) -> None
validate_size(size: int, max_size: int) -> None
```

Raises `ValueError` with descriptive message.

