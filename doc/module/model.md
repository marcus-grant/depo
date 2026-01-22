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

**Item (base):** code, hash_rest, kind, size_b, upload_at, uid, perm, origin_at (optional)

**TextItem(Item):** format (ContentFormat)

**PicItem(Item):** format (ContentFormat), width, height

**LinkItem(Item):** url

Note: `mime` is not stored. MIME is derived from `format` at serve time via `util/formats.py`.

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
