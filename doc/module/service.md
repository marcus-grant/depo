# service/ module

Application services and orchestration. May depend on model/ and util/.

## classify.py

Content classification from bytes and hints.

### Function

```python
classify(
    data: bytes,
    *,
    filename: str | None = None,
    declared_mime: str | None = None,
    requested_format: ContentFormat | None = None,
) -> ContentClassification
```

**Priority:** requested_format > declared_mime > magic bytes > filename extension

Uses strategy chain pattern with isolated helpers:

- `_from_requested_format()` — wraps validated ContentFormat
- `_from_declared_mime()` — calls format_for_mime
- `_from_magic_bytes()` — detects PNG, JPEG, WEBP signatures
- `_from_filename()` — calls format_for_extension

Raises `ValueError` if content cannot be classified.

### ContentClassification DTO

```python
@dataclass(frozen=True)
class ContentClassification:
    kind: ItemKind
    format: ContentFormat
```

## media.py

Image metadata extraction. Soft dependency on Pillow.

### Function

```python
get_image_info(data: bytes) -> ImageInfo
```

**Raises:**

- `ImportError` if Pillow unavailable
- `ValueError` if data is invalid or format unsupported

### ImageInfo DTO

```python
@dataclass(frozen=True)
class ImageInfo:
    format: ContentFormat | None = None
    width: int | None = None
    height: int | None = None
```

## ingest.py

Thin orchestrator for the ingest pipeline.

### IngestService

```python
class IngestService:
    def __init__(
        self,
        *,
        min_code_length: int = 8,
        max_size_bytes: int = 2**20,
    ) -> None: ...

    def build_plan(
        self,
        *,
        payload_bytes: bytes | None = None,
        payload_path: Path | None = None,
        filename: str | None = None,
        declared_mime: str | None = None,
        requested_format: ContentFormat | None = None,
    ) -> WritePlan: ...
```

**Pipeline:**

1. Validate payload (exactly one of bytes/path)
2. Validate size (non-empty, within limit)
3. Hash content via `hash_full_b32`
4. Classify via `classify()`
5. Extract image metadata if `PICTURE` kind
6. Assemble and return `WritePlan`

**Raises:** `ValueError` for validation or classification failures.

See doc/design/mvp.md §5.2 for design rationale.
