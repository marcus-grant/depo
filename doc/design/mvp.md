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
Application orchestration (thin)
  ▼
IngestService (pure)
  ▼
WritePlan DTO
  ▼
Repository (SQLite)
  ▼
StorageBackend (filesystem)
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

- `code` = prefix of full hash
- `hash_remainder` = remaining suffix
- Full hash string = `code + hash_remainder`

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

- `code` (PK)
- `hash_rest`
  - Note: `code` + `hash_rest` = full hash, each code with its len is unique
- `kind` : `ItemKind(Enum)`
- `size_b`: int
- `uid` (int, FK -> `User`)
- `perm` (`private`, `unlisted`, `public`, refactoring with `gid`)
  - Very simple for now till `Group` model exists
- `upload_at` (int, Unix Epoch UTC)
- `origin_at` (int | None, original file creation time if known)

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
    def build_plan(
        self,
        *,
        payload_bytes: bytes | None = None,
        payload_path: Path | None = None,
        filename: str | None = None,
        declared_mime: str | None = None,      # hint only, not stored
        requested_format: str | None = None,
        min_code_length: int,
        max_size_bytes: int,
    ) -> WritePlan:
        '''
        Responsibilities:
        - enforce size limit
        - compute full hash (existing utility module)
        - infer kind and format (declared_mime is hint, not stored)
        - extract metadata (image dims)
        - return WritePlan
        Must not: touch DB, touch HTTP, write files.
        '''
        raise NotImplementedError
```

### 5.3 Repository (hard interface)

Repository resolves collisions and persists metadata.
Storage writes should be coordinated with
the repository so failures are handled safely.

```python
from typing import Protocol, Optional

class ItemMeta(Protocol):
    code: str
    full_hash: str
    kind: str
    mime_type: str
    size_bytes: int
    storage_key: str

class Repository(Protocol):
    def get_by_code(self, code: str) -> Optional[ItemMeta]:
        ...

    def persist(self, plan: WritePlan) -> ItemMeta:
        '''
        Responsibilities:
        - collision resolution by extending code prefix length
        - DB writes (Item + subtype tables)
        - transactional consistency
        - ensure dedupe: same full_hash returns existing item
        '''
        ...
```

### 5.4 Storage backend (MVP)

```python
from pathlib import Path
from typing import Protocol, BinaryIO, Optional

class StorageBackend(Protocol):
    def put(
        self,
        *,
        code: str,
        source_bytes: Optional[bytes] = None,
        source_path: Optional[Path] = None,
    ) -> str:
        '''Returns storage_key.'''
        ...

    def open(self, *, storage_key: str) -> BinaryIO:
        ...
```

#### Storage path derivation

Paths are derived, not stored.
Given an item's `code` and `format`, the storage backend computes:

```
{STORAGE_ROOT}/{code}.{ext}
```

Extension equals `format.value` (e.g., `ContentFormat.PNG` → `.png`).
MIME type for HTTP headers is derived via `mime_for_format()` at serve time.

Extension is derived from MIME type. This keeps Item lean and avoids redundancy
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
