# MVP Plan

Tracks remaining work to reach a shippable MVP. Completed work lives in
reference docs under `doc/design/` and `doc/module/`.

## Quick reminders

These are settled. Full detail lives in the linked reference docs.

**Layering** ([architecture](../design/architecture.md)):
Dependencies flow inward: web -> service -> repo -> storage -> model -> util.
No business logic in routes. No framework objects below orchestration.
Services write, selectors read.

**Items** ([items](../design/items.md)):
Immutable, content-addressed. Primary key is `hash_full` (24-char BLAKE2b,
Crockford base32). `code` is a unique prefix (8-24 chars). `kind` discriminates
into TextItem, PicItem, LinkItem.

**Shortcodes** ([shortcodes](../design/shortcodes.md)):
The shortcode is the primary interface. `/{code}` is the canonical URL.
Smart defaults based on request context. `/raw` and `/info` sub-paths
are explicit overrides.

**Ingest pipeline** ([ingest](../design/ingest.md)):
Payload enters, gets hashed, classified, persisted. Orchestrator coordinates
service, repo, and storage. Dedupe by content hash.

## Pre-MVP work

Ordered by dependency. Each heading is roughly one PR.

### Route refactoring

New route surface based on item-first URL structure. `/{code}` is the primary
interface, sub-paths describe intent.

Routes:

- `GET /{code}` - dispatcher delegates to:
  - page/api handler based on request context.
  - LinkItem always redirects.
- `GET /{code}/info` - dispatcher, delegates to `page_info`, `hx_info`, or `api_info`
- `GET /{code}/raw` - no negotiation, always raw bytes + headers
- `POST /upload` - dispatcher, delegates to `hx_upload` or `api_upload`
- `GET /upload` - `page_upload`, full page render
- `GET /health` - liveness probe

Handler naming:

- No prefix - dispatchers that negotiate context (`upload`, `shortcut`, `info`)
- `page_` - full page renders (`page_upload`, `page_info`)
- `hx_` - HTMX partial responses (`hx_upload`, `hx_info`)
- `api_` - API/plain text responses (`api_upload`, `api_info`)

Test files with endpoints that will need updating:

- tests/web/test_routes.py:
  - TestGetInfo, TestGetRaw:
    - use /api/{code}/info and /api/{code}/raw paths
- tests/web/test_info_page.py: all classes use /{code}/info paths

Split `routes.py` into per-concern routers. Fixed-path routers register first,
wildcard router last.

Reserved for post-MVP: `/a/{alias}`, `/tag/{tag}`.

### Browser UI and styling

Targets the final route and handler structure.

- Styling primitives from the design language: dither patterns (1-bit bitmap
  fills), TUI borders (box-drawing characters), hard-edge dither shadows,
  typography hierarchy
- Toggle raw/rendered views (markdown, data formats)
- Inline metadata panes
- Apply visual system from [design language](../design/language.md)

### Error handling

Centralize error handling after routes and pipeline have stabilized.

- Expand `util/errors.py` with specific exception types for clear status code
  mapping (400 vs 413 vs 422). `PayloadTooLargeError` is the starting pattern.
- Refactor scattered `ValueError` raises with inline strings into typed exceptions
- Test `ImportError` path when Pillow is missing (currently uncaught 501)
- Improve the 500 fallback for unexpected item types in `info_page`
- Plan logging architecture: structured logging, request IDs, error tracking
- Extract validation logic from `build_plan` into a validation module.
  - Validators raise typed exceptions, `build_plan` lets them bubble up.
  - Pairs naturally with the typed exception refactor above.

### Config and limits

- Raise default upload limit to 64 MiB (guests disabled by default)
- Refactor size limits to use the config loading infrastructure
- Set up local dev/manual testing config in XDG paths
- Access tracking per item (UPDATE on access for recent/popular surfacing,
  naive first, optimize later)
- Unify `payload_bytes`/`payload_path` into `payload: bytes | Path`:
  - Use `isinstance` dispatch.
  - Reduces null coalescing throughout ingest pipeline.
  - Related to temp file streaming and async pipeline work.

### Auth

Minimal auth to prevent open uploads on the public internet.

- No anonymous uploads
- Manual user provisioning (admin edits DB)
- Username + password
- Item has owner (`uid`) + visibility (`perm`)
- `/upload` requires auth
- `uid=0` superuser convention continues until user table exists

### Manual Testing

- Manual route testing with posting collections saved to repo
- Manual testing of browser UI and styling across browsers and devices and pages.

## Explicit exclusions

These are not MVP:

- Aliases
- Editing UI
- Version history
- Groups and moderation
- Object storage origin
- Redis and metadata caching
- Public registration and password recovery
- JSON API responses (plain text + headers for MVP)
