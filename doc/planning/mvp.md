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

### Error surfaces (ref/error-surfaces)

- Add `ExtensionMismatchError(NotFoundError)` and
  `LinkRawNotSupportedError(NotFoundError)` to `util/errors.py`
- Collapse `errors/404.html` and `errors/500.html` into `errors/page.html`
  - Receives `{"error": e, "request": req}`
  - Branches on `error.status >= 500` for debug block
- Replace `partials/error.html` with `errors/partial.html`
  - Receives `{"error": e, "role": "alert"}`
  - Uses role as CSS modifier class and ARIA attribute
- Update `browser_error(req, e)` to render `errors/page.html`
- Update `htmx_error(e, role="alert")` to render `errors/partial.html`
- Drop `_response_404`, `_response_500`, `_get_item_or_404` from `shortcode.py`
- Thin all route handlers: raise typed exceptions, catch `DepoError`,
  delegate to builders
- Fix `page_info` unexpected item type fallback to raise instead of
  calling local helper
- Refactor upload route handlers to use `web/error.py` builders

### Error handling (deferred)

- Plan logging architecture: structured logging, request IDs, middleware
- Extract validation logic from `build_plan` into a validation module
  - Validators raise typed exceptions, `build_plan` lets them bubble up
- Investigate LinkItem format field gap (isinstance workaround in
  `_upload_response`)
- Consider initial logging functionality:
  - Centralized error handling
  - Middleware for request IDs
  - Rich output formatting
- MIME response handling review
- `FormatMismatchError(ClassificationError)` when classification endpoint lands
- Improve bug report UX for `UnknownClassificationError` and `UnknownServerError`
- `StorageError` domain base for filesystem and remote storage backends

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

### Global Chrome & Layout Realignment (nav / main / footer / base.html)

**Goal:** Make the overall page shell feel like a single calm system surface.
Prefer structural honesty (borders, spacing, rhythm) over “window/dialog” cosplay.
Ensure all hierarchy works in pure grayscale; color remains semantic only.

#### Styling Refinement Pass (deferred from ft/visual-refinement)

- Merge info header row
- Fix View Raw button height
- Resolve upload page width (too narrow despite `main--wide`)
- Replace `article` with `section` on info page


#### Interaction semantics stay semantic

- Keep warm/cool meaning invariant across the shell:
  - cool = focus/state
  - warm = attention/interruption
  - red = failure only
- Do not use accent color to “decorate” global chrome.

#### Primitive audit (enforce allowed tools)

- Allowed:
  - spacing,
  - typography (mono for identifiers),
  - weight,
  - sizing steps,
  - hard borders,
  - optional dither separators.
- Disallowed by default:
  - blur shadows, gradients, large colored surfaces, decorative textures.
- If a new visual device is introduced
  - it must justify itself as structure (not vibe).

#### HTMX compatibility (no layout surprises)

- Shell (`header/main/footer`) should remain stable across HTMX swaps.
- Swaps should target interior regions only;
  - avoid global reflow by keeping consistent container widths/padding in `base.html`.

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
