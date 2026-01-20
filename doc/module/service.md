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

### classify.py ContentClassification DTO

```python
@dataclass(frozen=True)
class ContentClassification:
    kind: ItemKind
    format: ContentFormat
```

**Priority:** requested_format > declared_mime > magic bytes > filename extension

Raises `ValueError` if content cannot be classified.

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
