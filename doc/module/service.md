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
        max_url_len: int = 2048,
    ) -> None: ...

    def build_plan(
        self,
        *,
        payload_bytes: bytes | None = None,
        payload_path: Path | None = None,
        filename: str | None = None,
        declared_mime: str | None = None,
        requested_format: ContentFormat | None = None,
        link_url: str | None = None,
    ) -> WritePlan: ...
```

**Pipeline:**

1. Validate payload (exactly one of bytes/path)
2. Validate size (non-empty, within limit)
3. Hash content via `hash_full_b32`
4. Classify via `classify()` or Assemble early exit `WritePlan` if `LinkItem`
5. Extract image metadata if `PICTURE` kind
6. Assemble and return `WritePlan`

>**NOTE:** The `payload_path` just gets re-routed to `payload_bytes`.
>Deferring `payload_path` handling till streaming content to temp files implemented.
>
>**NOTE:** `link_url` is an explicit branch,
>future inference from text payload as fallback.

**Raises:** `ValueError` for validation or classification failures.

See doc/design/mvp.md §5.2 for design rationale.

## orchestrator.py

Coordinates full ingest pipeline. Single entry point for web layer writes.

### PersistResult DTO

```python
@dataclass(frozen=True)
class PersistResult:
    item: TextItem | PicItem | LinkItem
    created: bool  # False = dedupe, True = new item
```

### IngestOrchestrator

```python
class IngestOrchestrator:
    def __init__(
        self,
        ingest_service: IngestService,
        repo: Repository,
        storage: StorageBackend,
    ) -> None: ...

    def ingest(
        self,
        *,
        payload_bytes: bytes | None = None,
        payload_path: Path | None = None,
        link_url: str | None = None,
        filename: str | None = None,
        declared_mime: str | None = None,
        requested_format: ContentFormat | None = None,
        uid: int = 0,
        perm: Visibility = Visibility.PUBLIC,
    ) -> PersistResult: ...
```

#### IngestOrchestrator - Pipeline

1. `IngestService.build_plan()` → WritePlan
2. `Repo.get_by_full_hash()` → dedupe check, return early if exists
3. `Repo.insert()` → resolve code internally, write metadata
4. `Storage.put()` → write bytes (skip for LinkItem)
5. On storage failure → `Repo.delete()` for rollback
6. Return `PersistResult(item, created)`

#### IngestOrchestrator - Raises

Re-raises exceptions from components.
`CodeCollisionError` on insert constraint violation (application bug).

## selector.py

Read-side counterpart to the ingest pipeline. Module-level functions
for fetching items and opening stored content.

Follows the services-write/selectors-read pattern.
See doc/design/patterns.md for rationale.

### Functions

```python
def get_item(
    repo: Repository,
    code: str,
) -> TextItem | PicItem | LinkItem:
    """
    Fetch item by shortcode.

    Raises:
        NotFoundError: If code does not exist.
    """
    ...

def get_raw(
    repo: Repository,
    storage: StorageBackend,
    code: str,
) -> tuple[BinaryIO | None, TextItem | PicItem | LinkItem]:
    """
    Open stored content for streaming + return item for response headers.

    Returns (file_handle, item) for Text/PicItems.
    Returns (None, item) for LinkItems (caller issues redirect).
    File handle is caller's responsibility to close.

    Raises:
        NotFoundError: If code does not exist.
    """
    ...

def get_info(
    repo: Repository,
    code: str,
) -> TextItem | PicItem | LinkItem:
    """
    Fetch item metadata.
    Currently equivalent to get_item().
    Separate function as seam for future expansion
    (view counts, access logs, cache headers).

    Raises:
        NotFoundError: If code does not exist.
    """
    ...
```

### Design decisions

- **Module-level functions, not a class** — read path has no shared state
- **Repo and storage as explicit parameters** — no hidden dependencies,
  trivially testable
- **get_raw returns (BinaryIO | None, Item)** — None handle signals LinkItem,
  web layer issues 302 redirect; file handle for Text/PicItem, caller closes
- **get_info as separate function** — thin wrapper today, seam for future
  concerns (view counting, access control)
- **Raises NotFoundError** — consistent with repo layer errors,
  web layer translates to 404
