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

### Browser UI and styling


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
- Extract error response helpers (_response_404, _response_500) from
  shortcode.py into shared error response module
- Centralize standard error response builders alongside typed exceptions
- Investigate LinkItem format field gap (isinstance workaround in
  _upload_response), consider adding format to base Item or LinkItem
- Consider initial logging functionality and how to tie it into:
  - Centralized error handling
  - The web server in use (e.g. middleware for request IDs)
  - Rich output formatting
- How to use MIME for responses

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

### Styling Refinement Pass

- These next 2 might be better in final preMVP manual test/visual refinement tsk
  - House cleaning to include:
    - Split template tests from test_upload.py into test_upload_templates.py
  - Rename .titlebar-inner to .page-column (or similar): used as a
    generic layout column wrapper in nav and footer but named after
    a nav-specific concept; rename for clarity post-MVP
- Success state redesign: replace full-width banner with calm inline
  state near the reference; small label with success hue on text/border
  only; primary action is copy reference; no colored background fill
- Focus indication primitive: consistent focus style (thick outline or
  inset border) that works in grayscale; color is additive only, not
  load-bearing; applies globally to all interactive elements
- Spacing token cleanup: define a single vertical rhythm scale
  (e.g. 0.5/1/1.5/2rem steps); replace ad-hoc micro-gaps throughout;
  audit all padding/margin values for consistency

>**NOTE:** Shortcode truncation: deferred;
>references are primary objects so hiding characters is risky;
>if overflow occurs in practice, prefer overflow-wrap:
>anywhere over ellipsis; JS prefix+suffix logic is out of scope pre-MVP

- Info page header row: merge shortcode and action row into single
  flex row; shortcode left, record actions right; wrap on narrow
  viewports
- View Raw anchor button height: border thickness insufficient to
  match adjacent button height; fix in final visual refinement pass
- Reorganize depo.css into logical sections: tokens, base elements,
  typography, page shell, structural utilities, components,
  content primitives, upload components
- Rename .titlebar-inner to .page-column (or similar); currently
  reused as generic layout column wrapper in nav and footer
- Upload page window width: too narrow at --depo-measure; needs
  wider working surface; investigate Pico article/main constraints
- Convert info page article.window to section.window; article
  implies self-contained distributable content which is incorrect

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
