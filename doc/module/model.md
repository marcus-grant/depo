# model/ module

Domain models, DTOs, and enums. Pure Python with no I/O dependencies.

## enums.py

| Enum | Members | Stored in DB |
|------|---------|--------------|
| ItemKind | TEXT, PICTURE, LINK | Yes |
| Visibility | PRIVATE, UNLISTED, PUBLIC | Yes |
| PayloadKind | BYTES, FILE | No |
| ContentFormat | TXT, MD, JSON, YAML, PNG, JPG, WEBP, ... | Yes |

All use StrEnum. ItemKind/Visibility/PayloadKind values ≤5 chars.
ContentFormat values are canonical short extensions (e.g., `jpg` not `jpeg`).

## item.py

Frozen dataclasses with `kw_only=True`.

**Item (base):** code, hash_full, kind, size_b, upload_at, uid, perm, origin_at (optional)

**TextItem(Item):** format (ContentFormat)

**PicItem(Item):** format (ContentFormat), width, height

**LinkItem(Item):** url

>**NOTE**: `mime` is not stored.
>MIME is derived from `format` at serve time via `model/formats.py`.

## user.py

Frozen dataclass with `kw_only=True`. Represents an authenticated system user.

**User:** id, email, name, pw_hash, created_at

- `id`: surrogate integer primary key, assigned by the database
- `email`: unique, used as login identifier
- `name`: unique display name
- `pw_hash`: `PHC`-style `scrypt`` hash string
  - sentinel value `UNSET` until `ft/credentials`
    - sets a real hash via the `set-password` command
- `created_at`: Unix epoch integer, consistent with Item timestamp fields

> **NOTE:** `pw_hash` is stored directly on `User` for MVP. A post-MVP item
> tracks moving it to a dedicated `credentials` table to keep the user model
> hash-free and support multiple auth methods per user.

## write_plan.py

Frozen DTO for ingest-to-repository handoff.

**Required:** hash_full, code_min_len, payload_kind, kind, size_b, upload_at

**Optional:** format, origin_at, payload_bytes, payload_path, width, height, link_url

>Note: `format` is None only for LinkItem.
>Image dimensions (width, height) are top-level, not prefixed.

## formats.py

Bidirectional mapping between ContentFormat and MIME/extension/kind.

**Outbound (format → external):**

- `mime_for_format(fmt: ContentFormat) -> str`
- `extension_for_format(fmt: ContentFormat) -> str`
- `kind_for_format(fmt: ContentFormat) -> ItemKind`

**Inbound (external → format):**

- `format_for_mime(mime: str) -> ContentFormat | None`
- `format_for_extension(ext: str) -> ContentFormat | None`

Accepts variants per Postel's Law (e.g., `application/x-yaml`, `jpeg`, `yml`).
Returns None for unsupported input on inbound functions.
