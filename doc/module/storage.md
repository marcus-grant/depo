# storage/ module

Payload storage for item content.
Depends on model/ for ContentFormat.
No framework dependencies.

## protocol.py

Storage backend protocol definition.

```python
from pathlib import Path
from typing import Protocol, BinaryIO
from depo.model.enums import ContentFormat

class StorageBackend(Protocol):
    def put(
        self,
        *,
        code: str,
        format: ContentFormat,
        source_bytes: bytes | None = None,
        source_path: Path | None = None,
    ) -> None:
        """
        Write payload to storage.
        Exactly one of source_bytes or source_path must be provided.
        """
        ...

    def open(self, *, code: str, format: ContentFormat) -> BinaryIO:
        """
        Open payload for reading.
        Caller responsible for closing the handle.
        """
        ...

    def delete(self, *, code: str, format: ContentFormat) -> None:
        """
        Remove payload from storage.
        Used for rollback on failed DB insert.
        No error if file doesn't exist (idempotent).
        """
        ...
```

## filesystem.py

Local filesystem implementation of StorageBackend.

### FilesystemStorage

```python
class FilesystemStorage:
    def __init__(self, root: Path) -> None:
        """
        Args:
            root: Base directory for all stored files.
                  Created if it doesn't exist.
        """
        ...

    def put(
        self,
        *,
        code: str,
        format: ContentFormat,
        source_bytes: bytes | None = None,
        source_path: Path | None = None,
    ) -> None: ...

    def open(self, *, code: str, format: ContentFormat) -> BinaryIO: ...

    def delete(self, *, code: str, format: ContentFormat) -> None: ...
```

### Path derivation

```python
def _path_for(self, code: str, format: ContentFormat) -> Path:
    return self._root / f"{code}.{format.value}"
```

Flat structure: `{root}/{code}.{ext}`

Examples:

- `ABCD1234` + `ContentFormat.PNG` → `storage/ABCD1234.png`
- `XYZW9999` + `ContentFormat.MARKDOWN` → `storage/XYZW9999.md`

### Design decisions

- **Flat storage** — no sharding, simple path derivation
- **Injected root** — testable with `tmp_path` fixture
- **Atomic writes** — write to temp file, rename (future consideration)
- **Idempotent delete** — no error if missing, safe for rollback
- **Format required** — extension derived from ContentFormat, not stored separately

### LinkItem note

LinkItem has no payload (URL is metadata only).
Orchestrator skips storage operations for `ItemKind.LINK`.
Storage layer is unaware of this—it simply never receives LinkItem calls.

### Future backends

Same protocol supports:

- S3 / object storage
- Remote filesystem (SFTP, WebDAV)
- Local cache in front of remote (LRU eviction)

Orchestrator and web layer unchanged—only storage implementation swaps.
