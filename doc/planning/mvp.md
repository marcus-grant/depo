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

- Apply visual system to info, error templates
  - Window containers for all info and error pages
  - Error color token, error border treatment (left rule)
  - Reading order: shortcode, action row, payload, metadata
  - Action row: copy shortcode, copy content URL, facts jump anchor
  - Metadata dl styling: dt secondary/normal, dd monospace/primary
  - Content styling: pre/code inset border, image 1px border
  - 500 details below divider, smaller type
  - Fix 404 broken p tag
- Raw/rendered toggle (separate PR)
  - Toggle control in action row
  - Document HTMX interaction patterns in doc/design/interactions.md
  - HX-Request detection, fragment vs full page response
  - _payload_info.html and _payload_raw.html partials
  - hx-get, hx-target=#payload, hx-swap, hx-push-url
- Visual refinement pass: element spacing, hierarchy, container
    proportions, nav/footer tuning, large-surface background treatment

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

#### 1) Remove false layering

- Avoid “floating dialog” framing for the primary page surface.
- Use **one primary containment surface** per page (typically `main`),
  not nested card/window stacks.
- Keep `.shadow-*` only where it communicates real stacking
  - otherwise rely on border + spacing.

#### 2) Establish a stable page frame in `base.html`

- Define one consistent layout grid: `header` (nav), `main`, `footer`.
- Set a single max-width + horizontal padding rule for `main`
  - so pages don’t invent their own.
- Standardize vertical rhythm tokens (one spacing scale); remove ad-hoc micro-gaps.

#### 3) Navbar: structural, not expressive

- Navbar exists to orient, not to brand.
- Prefer hard bottom border (or separator rule) over decorative fills/texture.
- Keep height minimal; align content to the same width/padding as `main`.
- Avoid accent surfaces; no gradients; no ornamental “chrome”.

#### 4) Main backdrop: grayscale-first

- Large surfaces remain grayscale; avoid tinted slabs.
- Ensure main content boundary reads without color: spacing + borders first.
- Dark mode parity: invert luminance, keep meaning; do not change hue roles.

#### 5) Footer: quiet + factual

- Footer content in secondary tone; low visual weight.
- Hard separator above footer if needed; no competing blocks.
- Align footer width/padding with `main` and navbar.

#### 6) Interaction semantics stay semantic

- Keep warm/cool meaning invariant across the shell:
  - cool = focus/state
  - warm = attention/interruption
  - red = failure only
- Do not use accent color to “decorate” global chrome.

#### 7) Primitive audit (enforce allowed tools)

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

#### 8) HTMX compatibility (no layout surprises)

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
