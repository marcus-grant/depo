# model/ module

Domain models, DTOs, and enums. Pure Python with no I/O dependencies.

## enums.py

| Enum | Members | Stored in DB |
|------|---------|--------------|
| ItemKind | TEXT, IMAGE, LINK | Yes |
| Visibility | PRIVATE, UNLISTED, PUBLIC | Yes |
| PayloadKind | BYTES, FILE | No |

All use StrEnum with \u22645 char values.

## item.py

Frozen dataclasses with `kw_only=True`.

**Item (base):** code, hash_rest, kind, mime, size_b, upload_at, uid, perm, origin_at (optional)

**TextItem(Item):** format

**PicItem(Item):** format, width, height

**LinkItem(Item):** url

## write_plan.py

Frozen DTO for ingest-to-repository handoff.

**Required:** hash_full, code_min_len, payload_kind, kind, mime, size_b, upload_at

**Optional:** origin_at, payload_bytes, payload_path, text_format, pic_format, pic_width, pic_height, link_url