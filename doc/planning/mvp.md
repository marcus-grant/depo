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

### Canonical config (Branch: `ref/canonical-config`)

*Problem: DepoConfig mixes value production with override-resolution
logic, and the resolved config never reaches IngestService.
Scalar defaults are inline literals on the dataclass;
the path factories (_default_store_dir, _default_db_path)
compute defaults but live beside the resolution chain;
and app_factory builds IngestService() with no arguments,
so its local defaults for min_code_length, max_size_bytes,
and max_url_len govern at runtime while the resolved config values are dead.
Extract all value production into a new cli/defaults.py
(scalar constants plus the renamed public path helpers and their tests),
leaving config.py as slim structuring and override logic.
Source DepoConfig fields from defaults.py,
raise the max_size_bytes default to 64 MiB (2**26),
add min_code_length as a config field,
and wire all three resolved fields into IngestService at app_factory,
dropping the service's local defaults so they are required.
Out of scope:
the override chain and config-file discovery
(_xdg_config_home, load_config layering), confirmed working and untouched;
guests-disabled-by-default (moved to Auth).*

#### Setup and gating test

- [ ] Add `**overrides` to the make_config factory; small green test
      that an override reaches the returned config.
  - [ ] Commit: `Tst: Add overrides to make_config factory`
- [ ] Add skipped TestConfigWiring class to tests/web/test_app.py: three
      tests, one per field, each asserting the config value governs the
      live API upload path (tiny max_size_bytes rejects any upload, tiny
      max_url_len rejects a link, raised min_code_length yields a code of
      exactly that length on an empty repo via X-Depo-Code).
  - [ ] Commit: `Tst: Add skipped gating tests for canonical config`

#### TDD implementation

**Relocate path-discovery helpers to cli/defaults.py**
(`tests/cli/test_defaults.py`)

- [ ] Stub cli/defaults.py with module header; move and rename
      _default_store_dir -> default_store_dir,_default_db_path ->
      default_db_path; reference via defaults namespace in config.py.
- [ ] Move the four path-factory tests from test_config.py to
      test_defaults.py (refactor-under-green).
- [ ] uv run ruff check && uv run pytest
- [ ] Commit: `Ref: Relocate path-discovery helpers to cli/defaults.py`

**Source DepoConfig scalars from cli/defaults.py**
(`tests/cli/test_config.py`, `tests/cli/test_defaults.py`)

- [ ] Add scalar constants to defaults.py: DEFAULT_HOST, DEFAULT_PORT,
      DEFAULT_MAX_SIZE_BYTES = 2**26, DEFAULT_MAX_URL_LEN,
      DEFAULT_LOG_LEVEL.
- [ ] Update test_config.py default assertions: max_size_bytes
      10_485_760 -> 2**26 (the bump red).
- [ ] Rewire DepoConfig scalar fields to reference the constants.
- [ ] uv run ruff check && uv run pytest
- [ ] Commit: `Ref: Source DepoConfig scalars from cli/defaults.py`

**Add min_code_length to DepoConfig**
(`tests/cli/test_config.py`, `tests/cli/test_defaults.py`)

- [ ] Add DEFAULT_MIN_CODE_LENGTH = 8 to defaults.py; add
      min_code_length field to DepoConfig sourcing it; add
      min_code_length to_coerce int_fields.
- [ ] Red: resolution test that an overridden min_code_length (env or
      TOML) resolves onto the config, mirroring existing override tests.
- [ ] uv run ruff check && uv run pytest
- [ ] Commit: `Ref: Add min_code_length to DepoConfig`

**Route test IngestService construction through a factory**
(`tests/factories/`, `tests/service/`, `tests/fixtures/`)

- [ ] Add make_ingest_service(**overrides) to tests/factories with sane
      defaults for the three limit fields.
- [ ] Migrate all IngestService() / IngestService(...) sites in
      test_ingest.py and test_orchestrator.py, and t_orch_env, to the
      factory (refactor-under-green: production defaults still exist).
- [ ] uv run ruff check && uv run pytest
- [ ] Commit: `Tst: Route IngestService construction through factory`

**Wire resolved config into IngestService** (`tests/web/test_app.py`)

- [ ] Drop the local defaults from IngestService.**init**; make
      min_code_length, max_size_bytes, max_url_len required.
- [ ] In app_factory, construct IngestService with all three threaded
      from app.state.config.
- [ ] Unskip the three TestConfigWiring gating tests (the red for this
      unit); minimal green.
- [ ] uv run ruff check && uv run pytest
- [ ] Commit: `Ref: Wire resolved config into IngestService`

#### Integration and documentation

- [ ] Confirm the three gating tests pass unskipped.
- [ ] Update affected doc/module reference docs (cli.md and service.md
      carry stale max_size_bytes values; new cli/defaults.py needs an
      entry linked from the cli module README). Dev decides final scope.
- [ ] uv run ruff check && uv run pytest
- [ ] Commit: `Doc: ...`

#### PR

- [ ] gh pr create --title "Ref: Canonical config" --body "..."

### Non-HTMX form fallback error handling (needs planning)

Problem: the `application/x-www-form-urlencoded` fallback branch in the
upload dispatcher (`web/routes/upload.py`) runs `_parse_form_upload` and
`orch.ingest` with no `except DepoError`. Expected domain errors (empty,
oversized, bad format) on a non-HTMX form POST escape to the app-level
boundary, which wraps them as `UnknownServerError` and renders a 500. This
mislabels ordinary 4xx domain errors as server errors and discards their
real status and message.

This was assumed closed by the `ref/error-boundary` boundary handler. It is
not: the boundary is for unexpected errors and must not be the catch path
for expected ones. The fix is entangled with the fallback's success shape
(currently a 303 redirect, no error render of its own), so the surface and
flow need a design decision, not a patch.

To plan: what the non-HTMX form path renders on a DepoError (full-page
browser_error, redirect-with-flash, or other), whether the success redirect
stays, and how this interacts with the deferred non-404 4xx browser
templates. Plan alongside request access logging.

### Auth

Minimal auth to prevent open uploads on the public internet.

- No anonymous uploads
  - Guests disabled by default
    - *(the config default to enforce once a guest/role concept exists)*
    - moved here from Config and limits
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
