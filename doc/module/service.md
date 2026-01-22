# service/ module

Application services and orchestration. May depend on model/ and util/.

## classify.py

Content classification from bytes and hints.

### classify.py Function:**

```python
classify(
    data: bytes,
    *,
    filename: str | None,
    declared_mime: str | None,
    requested_format: str | None
) -> ContentClassification
```

### classify.py Function
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
```

---

**Commit:**
```
Doc: Update model and service module specs

- model/formats.py: Add inbound lookup functions, fix path reference
- service/classify.py: Fix requested_format type (ContentFormat, not str),
  document strategy chain pattern and helpers

## media.py

Image metadata extraction. Soft dependency on Pillow.

### media.py Function

- `get_image_info(data: bytes) -> ImageInfo`

### media.py ImageInfo DTO

```python
@dataclass(frozen=True)
class ImageInfo:
    format: ContentFormat | None = None
    width: int | None = None
    height: int | None = None
```

Returns empty ImageInfo if Pillow unavailable or data is not a valid image.

## ingest.py

Thin orchestrator for the ingest pipeline.

**Class:** `IngestService`

### Ingest Method

```python
build_plan(
    *,
    payload_bytes,
    payload_path,
    filename,
    declared_mime,
    requested_format,
    min_code_length,
    max_size_bytes
) -> WritePlan`
```

See doc/design/mvp.md `IngestService` section for full interface specification.
