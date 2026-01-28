# Design Requirements — MVP (v0.0.1)

These are the requirements for this *content-addressed paste / image service*.

## Purpose

Establish a
correct, stable foundation that is minimally usable for friends/family,
supports both API and browser usage, and optimizes for iteration toward v1.0.

This version prioritizes correctness, clear invariants,
and clean architecture over features.

---

## 1. Core Invariants (Non-Negotiable)

1. **Content-addressed storage**
   - Item identity is derived solely from content bytes.
   - Hashing + short code behavior is deterministic and stable.
   - Items are immutable once created.

2. **Two canonical access paths**
   - `/{code}/raw` returns the exact bytes, always.
   - `/{code}/info` is a human-facing representation based on item format.

3. **No anonymous uploads**
   - Uploads require authentication.
   - Reads may be public or unlisted.

4. **Filesystem-backed payloads**
   - Payloads (including text) are stored outside the DB.
   - DB stores metadata only.

5. **Single-instance, SQLite-first**
   - SQLite is a first-class backend.
   - No distributed assumptions.

---

## 2. Architecture (MVP)

### 2.1 Layering

```txt
HTTP Layer (FastAPI)
  ├── Auth / guards
  ├── Routing (/{code}, /raw, /info, /upload)
  ▼
IngestOrchestrator
  ├── IngestService.build_plan() → WritePlan
  ├── Repository (dedupe, resolve code, insert)
  └── StorageBackend (write bytes)
  ▼
PersistResult (item, created)
```

### Rules

- No business logic in routes.
- No framework objects below orchestration.
- Core decisions are testable without HTTP.

### 2.2 Module boundaries (recommended)

- `domain/` – DTOs, enums, policies, contracts
- `services/` – ingest/classification logic
- `repos/` – persistence logic (SQLite)
- `storage/` – filesystem storage
- `web/` – FastAPI routes, templates, HTMX handlers
- `tests/` – contract tests and integration tests

---

## 3. External Contract (Must Not Change)

### 3.1 URL surface

- `GET /{code}`
  - Browser-like clients → redirect to `/{code}/info`
  - API / non-browser clients → redirect to `/{code}/raw`
- `GET /{code}/raw` → raw bytes
- `GET /{code}/info` → viewer / metadata
- `POST /upload` → multipart/form-data (browser)
- Optional: `POST /upload/raw` → raw body (curl / API)

### 3.2 Hashing & short code rules

- Hash algorithm: **BLAKE2b**
- Digest size: **120 bits** (15 bytes)
- Encoding: **Crockford base32**
- Canonical output: uppercase
- Full encoded hash length: **24 characters**

Storage model:

- `hash_full` = complete 24-char hash (primary identity)
- `code` = unique prefix (8-24 chars, assigned at creation)
- Domain models store `hash_full` directly (matches DB schema)

### 3.3 Collision handling (prefix extension)

- Configurable minimum code length (e.g. 8)
- If collision with different content:
  - extend prefix length (9, 10, … up to 24)
- DB stores canonical `code`; `hash_remainder` updates accordingly.

### 3.4 Canonicalization on input

- Accept ambiguous characters and normalize:
  - `o` / `O` → `0`
  - `i` / `I` / `l` / `L` → `1`
- Uppercase before DB lookup.
- DB stores canonical uppercase only.

---

## 4. Domain Model (MVP)

### 4.1 Item (base, immutable)

#### Item Responsibilities

- Identity
- Storage location
- Core metadata

#### Item Fields (conceptual)

#### Item Fields (DB schema)

- `hash_full` (PK, 24-char content hash)
- `code` (UNIQUE, 8-24 char URL identifier)
- `kind` : `ItemKind(Enum)`
- `size_b`: int
- `uid` (int, default 0; no FK until User table exists)
- `perm` (Visibility enum, default PUBLIC)
- `upload_at` (int, Unix Epoch UTC)
- `origin_at` (int | None, original file creation time if known)

#### Item Fields (domain model)

- `code` (from DB)
- `hash_full` (content-addressed identity)
- All other fields map directly

### 4.2 TextItem (heavy-load-bearing)

### 4.2 TextItem

#### TextItem Philosophy

- Notes, scripts, lists, markdown, and data formats are all TextItem.
- Format determines `/info` default behavior.

#### TextItem Fields

- `code` (PK, FK → Item)
- `format`
  - str
  - *(`plain`, `markdown`, `python`, `bash`, `json`, `yaml`, `csv`, `html`)*

#### TextItem Rules

- `/info` behavior is determined by `format`.
- `/raw` always returns bytes.
- Dangerous formats (`html`, `svg`) are **never rendered**, only highlighted.

### 4.3 PicItem

#### PicItem Fields

- `code` (PK, FK → Item)
- `format` (str, e.g. `png`, `jpeg`, `gif`, `webp`)
- `width` (int)
- `height` (int)

SVG and EXIF support deferred to post-MVP.

### 4.4 LinkItem (explicit in MVP)

### 4.4 LinkItem

#### LinkItem Rules

- Created explicitly (no implicit URL auto-detection in MVP).
- `/{code}` redirects to target (via `/info` in browser).

#### LinkItem Fields

- `code` (PK, FK → Item)
- `url` (str, validated; schemes default to http/https)

---

## 5. Ingest Pipeline (MVP)

### 5.1 WritePlan DTO (hard interface)

#### WritePlan Purpose

Framework-agnostic handoff between inference and persistence.

#### WritePlan Hard rules

- Hashing happens before persistence.
- Bytes are never modified (no normalization).
- Exactly one payload reference (bytes OR temp file path).
- DTO must be serializable (no ORM objects, no request objects).

#### WritePlan Interface

```python
@dataclass(frozen=True)
class WritePlan:
    # Identity
    hash_full: str                 # 24-char base32 string
    code_min_len: int

    # Payload reference (exactly one)
    payload_kind: PayloadKind
    payload_bytes: bytes | None = None
    payload_path: Path | None = None

    # Classification & metadata
    kind: ItemKind
    format: ContentFormat | None   # None only for LinkItem
    size_b: int
    upload_at: int
    origin_at: int | None = None

    # Image-specific
    width: int | None = None
    height: int | None = None

    # Link-specific
    link_url: str | None = None
```

### 5.2 IngestService (hard interface)

```python
class IngestService:
    def __init__(
        self,
        *,
        min_code_length: int = 8,
        max_size_bytes: int = 2**20,
    ) -> None:
        '''Configuration set at construction time.'''
        ...

    def build_plan(
        self,
        *,
        payload_bytes: bytes | None = None,
        payload_path: Path | None = None,
        filename: str | None = None,
        declared_mime: str | None = None,
        requested_format: ContentFormat | None = None,
    ) -> WritePlan:
        '''
        Responsibilities:
        - validate payload (exactly one of bytes/path)
        - enforce size limit (non-empty, within max)
        - compute full hash via hash_full_b32
        - classify via classify()
        - extract image metadata for PICTURE kind
        - assemble and return WritePlan

        Must not: touch DB, touch HTTP, write files.

        Raises:
            ValueError: If validation or classification fails.
        '''
        ...
```

>**Note**: `declared_mime` is a hint for classification, not stored.
>`requested_format` is a validated `ContentFormat` from the web layer.

### 5.3 Repository (hard interface)

Repository handles DB persistence. Orchestrator coordinates with storage.

```python
from typing import Protocol

class Repository(Protocol):
    def get_by_code(self, code: str) -> TextItem | PicItem | LinkItem | None:
        """Lookup by exact code. Assumes input is canonicalized."""
        ...

    def get_by_full_hash(
      self, hash_full: str) -> TextItem | PicItem | LinkItem | None:
        """Dedupe lookup by content hash."""
        ...

    def resolve_code(self, hash_full: str, min_len: int) -> str:
        """Find shortest unique code prefix (min_len to 24)."""
        ...

    def insert(
        self,
        plan: WritePlan,
        code: str,
        *,
        uid: int = 0,
        perm: Visibility = Visibility.PUBLIC,
    ) -> TextItem | PicItem | LinkItem:
        """
        Insert new item. Code must be pre-resolved.
        Raises CodeCollisionError if code already exists (application bug).
        """
        ...
```

#### Design decisions

- **Raw SQL** with manual mapping (no ORM)
- **Return concrete types** (`TextItem | PicItem | LinkItem`), not Protocol
- **Validation at boundary** — repo trusts inputs are canonical
- **uid/perm defaults** — superuser (0) and PUBLIC until auth layer exists

### 5.4 Storage backend (MVP)

```python
from pathlib import Path
from typing import Protocol, BinaryIO

class StorageBackend(Protocol):
    def put(
        self,
        *,
        code: str,
        format: ContentFormat,
        source_bytes: bytes | None = None,
        source_path: Path | None = None,
    ) -> None:
        """Write payload to storage. Exactly one of source_bytes/source_path."""
        ...

    def open(self, *, code: str, format: ContentFormat) -> BinaryIO:
        """Open payload for reading."""
        ...

    def delete(self, *, code: str, format: ContentFormat) -> None:
        """Remove payload. Used for rollback on failed DB insert."""
        ...
```

#### Storage path derivation

Paths are derived, not stored. Flat structure:

```txt
{STORAGE_ROOT}/{code}.{ext}
```

Extension equals `format.value` (e.g., `ContentFormat.PNG` → `.png`).
MIME type for HTTP headers is derived via `mime_for_format()` at serve time.

#### LinkItem exception

LinkItem has no payload bytes (URL is metadata only). Orchestrator skips
storage operations for `ItemKind.LINK`.

### 5.5 IngestOrchestrator

Single entry point for the web layer. Coordinates full ingest pipeline.

```python
@dataclass(frozen=True)
class PersistResult:
    item: TextItem | PicItem | LinkItem
    created: bool  # False = dedupe hit

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
        filename: str | None = None,
        declared_mime: str | None = None,
        requested_format: ContentFormat | None = None,
        uid: int = 0,
        perm: Visibility = Visibility.PUBLIC,
    ) -> PersistResult:
        """
        Full pipeline:
        1. IngestService.build_plan() → WritePlan
        2. Repo.get_by_full_hash() → dedupe check
        3. Repo.resolve_code() → collision handling
        4. Storage.put() → write bytes (skip for LinkItem)
        5. Repo.insert() → write metadata
        6. Return PersistResult

        On DB failure after storage write, calls Storage.delete() for rollback.
        """
        ...
```

#### IngestOrchestrator - Design decisions

- **Orchestrator owns coordination** — repo and storage are siblings
- **Dedupe at orchestrator level** — returns existing item without re-writing
- **Storage before DB** — orphan files easier to cleanup than orphan rows
- **PersistResult DTO** — web layer can decide whether to show "exists" vs "created"
- **Future-ready**:
  - WAL table (`pending_writes`) can be added for atomic writes
  - Metadata cache layer can skip DB reads for hot items
  - Write coalescing can batch repo inserts during high ingest
  - Local content cache can serve as LRU layer fronting remote storage
    - Think of a cache on local FS for remote S3, SFTP, WebDAV, etc.
  - All without changing the orchestrator's public interface

---

## 6. HTTP & UI (MVP)

### 6.1 API

- `POST /upload` (multipart)
- Optional: `POST /upload/raw`
- `GET /{code}` (redirect)
- `GET /{code}/raw`
- `GET /{code}/info`

### 6.2 Browser UI

- Server-rendered HTML
- HTMX from day one for interactivity on `/info` pages:
  - toggle raw/rendered views (especially markdown/data)
  - inline metadata panes
  - progressive enhancement

---

## 7. Auth (MVP)

- No anonymous uploads.
- Manual user provisioning (admin edits DB).
- Username + password.
- Authorization is minimal:
  - item has owner + visibility
  - `/upload` requires auth

---

## 8. Explicit MVP Exclusions

- Aliases
- Editing UI
- Version history
- Groups / moderation
- Object storage origin
- Redis / metadata caching
- Public registration / password recovery
