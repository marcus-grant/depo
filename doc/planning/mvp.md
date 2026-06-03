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

### Unexpected-error boundary (Branch: `ref/error-boundary`)

*Problem: non-DepoError exceptions slip past the per-route `except DepoError`
catches and reach FastAPI's default 500 unlogged, and `hx_upload` guards its
own HTMX case with a bare except. Centralize unexpected errors in one
app-level handler that wraps, negotiates surface, and delegates to a builder.
The builders already log (PR 1), so the handler must not log again. Depends on
`ft/error-logging`.*

#### Setup and gating test

- [ ] `git checkout -b ref/error-boundary`
- [ ] `tests/web/test_errors.py`: skipped integration test. Monkeypatch a
      selector call to raise `OSError`, hit a shortcode GET, assert a logged
      controlled 500; repeat with `HX-Request` and assert 200 plus the error
      partial. Needs the no-reraise client. Mark
      `@pytest.mark.skip("boundary not implemented")`.
- [ ] `uv run ruff check && uv run pytest`
- [ ] Commit: `Tst: Add skipped boundary integration test`

**Carryover from ft/error-logging** (`web/error.py`, `util/errors.py`, `tests/cli/test_config.py`)

- [ ] Extract `_log(e)` helper in `web/error.py`: rename the module logger to
      `_logger`, add `_log(e)` emitting at `e.severity` with
      `exc_info=e.exception`, replace the inline calls in all three builders
      with `_log(e)`. Covered by existing builder-logging tests.
- [ ] Annotate `severity: Severity` on `DepoError` to match the slot intent.
- [ ] Add a TOML resolution test for `log_level` in `test_config.py`.
- [ ] `uv run ruff check && uv run pytest`
- [ ] Commit: `Ref: Extract _log helper, close ft/error-logging gaps`

#### TDD implementation

**Uniform builder return** (`tests/web/test_error_responses.py`)

- [ ] Change `htmx_error` to `htmx_error(req, e, role="alert") -> Response`,
      returning the `errors/partial.html` TemplateResponse hardcoded at
      `status_code=200` (the HTMX contract, unlike `browser_error` which uses
      `e.status`).
- [ ] Update `hx_upload`: error branch becomes `return htmx_error(request, e)`,
      success path returns its TemplateResponse directly, the `kw` merge goes
      away. Leave the `except Exception` branch for now as
      `return htmx_error(request, UnknownServerError(e))`.
- [ ] Rewrite the 4 `TestHtmxError` tests to assert on the Response (status
      200, partial marker, error in context) instead of dict keys.
- [ ] `uv run ruff check && uv run pytest`
- [ ] Commit: `Ref: Make htmx_error return a Response`

**Boundary handler** (`tests/web/test_errors.py`, fixture in `tests/fixtures/__init__.py`)

- [ ] Add `unhandled(request, exc) -> Response` to `web/error.py`: wrap in
      `UnknownServerError(exc)`, then `is_htmx` -> `htmx_error`, `wants_html`
      -> `browser_error`, else `api_error`. No log call here; the builders log.
- [ ] Register in `app_factory`: `app.add_exception_handler(Exception, unhandled)`.
- [ ] Add a `TestClient(client.app, raise_server_exceptions=False)` fixture
      mirroring `t_client`, so the handler's response is observable.
- [ ] Tests: non-DepoError through a shortcode GET gives a logged controlled
      500 (api and browser surfaces); with `HX-Request`, 200 plus partial.
      Confirm `_500_response()` in `test_errors.py:52` still holds; adjust if
      it leaned on the default 500.
- [ ] `uv run ruff check && uv run pytest`
- [ ] Commit: `Ft: Add app-level boundary handler for unexpected errors`

**Thin hx_upload** (`tests/web/routes/test_upload.py`)

- [ ] Remove `hx_upload`'s `except Exception`; unexpected upload errors now
      bubble to the boundary.
- [ ] Test: inject a non-DepoError into the upload path through the no-reraise
      client, assert 200 plus partial via the boundary.
- [ ] `uv run ruff check && uv run pytest`
- [ ] Commit: `Ref: Remove hx_upload bare except, defer to boundary`

#### Integration and documentation

- [ ] Remove the skip from the gating test, verify it passes.
- [ ] Update `doc/design/errors.md` and `doc/module/web.md` (boundary handler,
      uniform builders, hx_upload thinning), kept linked from their READMEs.
- [ ] `uv run ruff check && uv run pytest`
- [ ] Commit: `Doc: Document unexpected-error boundary`

#### PR

- [ ] `gh pr create --title "Ref: Unexpected-error boundary" --body "..."`

### Config and limits

- Raise default upload limit to 64MiB (`max_size_bytes` = 67_108_864);
  - guests disabled by default
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
