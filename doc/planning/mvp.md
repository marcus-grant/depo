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

### Non-HTMX form fallback error surface (Branch: `fix/form-error-surface`)

*Problem: the `application/x-www-form-urlencoded` fallback branch in the
upload dispatcher (`web/routes/upload.py`) runs `_parse_form_upload` and
`orch.ingest` with no `except DepoError`, so expected domain errors (empty,
oversized, bad format) on a non-HTMX form POST escape to the boundary, which
wraps them as `UnknownServerError` and renders a 500. This mislabels ordinary
4xx as server errors and discards their true status and message. Compounding
it, a bad `format=` token raises a raw `ValueError` from `ContentFormat(fmt)`
at three sites (form parse file branch, form parse text branch, and
`api_upload`), which escapes even a bare `except DepoError`. Decision: the
form path renders full-page `browser_error` at the error's true status; the
success 303 redirect to `/{code}/info` is unchanged. Coercion is normalized
through `format_for_extension` (alias-tolerant, returns None on unknown), with
the web layer raising `UnsupportedFormatError` on None so the model layer stays
free of web-error semantics. Out of scope: redirect-with-flash (no flash or
session infrastructure exists, not introducing it); FormatMismatchError
(unplanned, unrelated to unsupported-token coercion); the htmx and api error
surfaces (already wired and tested).*

#### Setup and gating test

- [ ] Branch `fix/form-error-surface` from main.
- [ ] Add a skipped integration test to `tests/web/routes/test_upload.py`
      (new `TestFormFallbackError` class) asserting the end state: a non-HTMX
      form POST (`t_client.post`, `data=...`, no `HEADER_HTMX`) that triggers
      a domain error renders full-page HTML at the error's true 4xx status,
      not 500 and not plaintext. Assert `status_code == 400` for an empty
      submission (PayloadEmptyError is 400), `text/html` content-type, and the
      `errors/page.html` marker in the body via BeautifulSoup.
      `@pytest.mark.skip` until the last unit.
  - [ ] Commit: `Tst: Add skipped gating test for form fallback error surface`

#### TDD implementation

**Normalize format-token coercion through `format_for_extension`**
(`tests/web/routes/test_upload.py`)

- [ ] Red: add a parse-unit test to `TestParseFormUpload` asserting a bad
      `format` token on non-empty content raises `UnsupportedFormatError`
      (use `_test_fn("hello", "bogus")`; non-empty content avoids the
      `PayloadEmptyError` short-circuit).
- [ ] Replace the three `ContentFormat(fmt)` call sites in `upload.py`
      (`_parse_form_upload` file branch, text branch, and `api_upload`'s
      `req_fmt`) with `format_for_extension(...)`, raising
      `UnsupportedFormatError(fmt)` when it returns None. Import
      `format_for_extension` and `UnsupportedFormatError`.
- [ ] Confirm `test_request_format_for_select_option` stays green
      (refactor-under-green: canonical tokens still resolve, so the existing
      assertion is the regression guard for the swap).
- [ ] uv run ruff check && uv run pytest
- [ ] Commit: `Fix: Normalize format-token coercion, raise UnsupportedFormatError`

**Surface bad API-path format token as 422**
(`tests/web/routes/test_upload.py`)

- [ ] Red: add a test under `TestApiUploadError` asserting `?format=bogus`
      returns 422, mirroring `test_oversized_returns_413`. The coercion swap
      from the prior unit already routes this through `api_upload`'s existing
      `except DepoError`, so this asserts the now-correct API surface
      end to end.
- [ ] uv run ruff check && uv run pytest
- [ ] Commit: `Tst: Assert API-path bad format token returns 422`

**Wire form fallback branch to `browser_error`**
(`tests/web/routes/test_upload.py`)

- [ ] Red: add form-branch tests (`TestFormFallbackError`) asserting an
      oversized non-HTMX form POST renders full-page HTML at 413, and a
      bad-format one at 422 (full surface, distinct from the empty-content
      400 the gating test covers).
- [ ] In `upload.py`, wrap the form fallback branch's `_parse_form_upload` and
      `orch.ingest` in `try/except DepoError as e: return browser_error(req, e)`.
      Import `browser_error`. Catch `DepoError` broadly; `e.status` drives the
      response. Leave the 303 success path unchanged.
- [ ] uv run ruff check && uv run pytest
- [ ] Commit: `Fix: Render browser_error on non-HTMX form fallback DepoError`

#### Integration and documentation

- [ ] Unskip the `TestFormFallbackError` gating test; confirm it passes.
- [ ] Update `doc/design/errors.md` Deferred section: remove the
      form-fallback entry (closed by this PR) and mark the non-404 4xx
      browser-template entry resolved (the error rearchitecture made
      `errors/page.html` render any status generically; the note drifted
      out of sync and was never updated).
- [ ] Note in errors.md that `FormatMismatchError` (unplanned) is unrelated
      and untouched, to prevent a future reader conflating it with the
      unsupported-token coercion landed here.
- [ ] uv run ruff check && uv run pytest
- [ ] Commit: `Doc: ...`

#### PR

- [ ] gh pr create --title "Fix: Non-HTMX form fallback error surface" --body "..."

### Users table and model (Branch: `ft/users-table`)

*Problem: there is no user identity in the system. `items.uid` is an
integer referencing nothing and auth has no table to authenticate
against. Add a `users` table, a `User` domain model, and user repo CRUD,
with `items.uid` gaining a foreign key to `users(id)`. Out of scope:
password hashing and the provisioning command (owned by
`ft/credentials`); login and session infrastructure (`ft/login-session`);
the `/upload` gate (`ft/upload-gate`); `perm`/visibility enforcement
(post-MVP, column already present and defaulting to PUBLIC).*

#### Setup and gating test

- [ ] Branch `ft/users-table` from main.
- [ ] Add a skipped integration test to `tests/repo/test_sqlite.py`
      (new `TestUserPersistence` class) asserting the end state: a `User`
      inserted via the repo round-trips, fetch-by-id and fetch-by-email
      each return a `User` equal to the inserted one. `@pytest.mark.skip`
      until the last unit.
  - [ ] Commit: `Tst: Add skipped gating test for user persistence round-trip`

#### TDD implementation

**Add the User domain model**
(`tests/model/test_user.py`)

- [ ] Red: add field-spec tests mirroring `TestItem` (`test_instance_dataclass`,
      parametrized `test_fields` over `id`, `email`, `name`, `pw_hash`,
      `created_at`, `test_frozen`, `test_instantiate`).
- [ ] Add `src/depo/model/user.py`: frozen `kw_only` `User` dataclass,
      all fields required, no optionals.
- [ ] uv run ruff check && uv run pytest
- [ ] Commit: `Ft: Add User domain model`

**Add the make_user factory**
(`tests/model/test_user.py`)

- [ ] Red: add a test asserting `make_user()` returns a valid `User` and
      that overrides apply.
- [ ] Add `make_user(**overrides) -> User` to `tests/factories/models.py`
      alongside the existing model factories.
- [ ] uv run ruff check && uv run pytest
- [ ] Commit: `Tst: Add make_user factory`

**Add the users table and items.uid foreign key**
(`tests/repo/test_sqlite.py`)

- [ ] Red: add a test asserting the FK is enforced, inserting an item with
      an unknown uid raises under `PRAGMA foreign_keys = ON`; and a test
      asserting the seeded superuser row exists after `init_db`.
- [ ] Edit `src/depo/repo/schema.sql`: add the `users` table above `items`
      (`id INTEGER PRIMARY KEY`, `email TEXT NOT NULL UNIQUE`, `name TEXT
      NOT NULL UNIQUE`, `pw_hash TEXT NOT NULL`, `created_at INTEGER NOT
      NULL`); add `REFERENCES users(id)` to `items.uid`; seed the reserved
      superuser row with an idempotent `INSERT OR IGNORE` carrying a
      non-verifying `pw_hash` sentinel (no hashing exists until
      `ft/credentials`; the superuser stays un-loginable until that PR
      sets a real password) so the `uid` default has a referent.
- [ ] uv run ruff check && uv run pytest
- [ ] Commit: `Ft: Add users table and items.uid foreign key`

**Add user repo CRUD**
(`tests/repo/test_sqlite.py`)

- [ ] Red: add tests for insert, fetch-by-id, fetch-by-email, and unique
      violations on `email` and `name`; add an `insert_user` DB helper
      delegating to `make_user`.
- [ ] Add `_row_to_user`, `insert_user`, `get_user`, and
      `get_user_by_email` to `src/depo/repo/sqlite.py`, following the
      existing `_row_to_*` and insert idioms.
- [ ] uv run ruff check && uv run pytest
- [ ] Commit: `Ft: Add user repo CRUD`

#### Integration and documentation

- [ ] Unskip the `TestUserPersistence` gating test; confirm it passes.
- [ ] Update `doc/module/model.md` (User model) and `doc/module/repo.md`
      (user CRUD); note the `items.uid` foreign key wherever the schema is
      documented.
- [ ] uv run ruff check && uv run pytest
- [ ] Commit: `Doc: ...`

#### PR

- [ ] gh pr create --title "Ft: Users table and model" --body "..."

### Password credentials and provisioning (Branch: `ft/credentials`)

*Problem: users have a `pw_hash` column but nothing produces or
verifies a hash, and manual provisioning via raw SQL cannot compute
one. Add a stdlib credentials module (scrypt hashing, constant-time
verify) and a click create-user command that writes a row with a
valid hash. Depends on `ft/users-table`. Out of scope: login route
and sessions (`ft/login-session`); the `/upload` gate
(`ft/upload-gate`); email-based provisioning flows (post-MVP).
Assumes `ref/canonical-config` has landed: scalar defaults live in
`cli/defaults.py` and `DepoConfig` sources from them.*

#### Setup and gating test

- [ ] Branch `ft/credentials` from `ft/users-table`.
- [ ] Add a skipped integration test to `tests/cli/test_main.py` (new
      `TestCreateUser` class) asserting the end state: invoking the
      create-user command with email, name, and password writes a
      `users` row whose stored `pw_hash` verifies against the password
      and rejects a wrong one. `@pytest.mark.skip` until the last unit.
  - [ ] Commit: `Tst: Add skipped gating test for user provisioning`

#### TDD implementation

**Hash and verify passwords with stdlib scrypt**
(`tests/util/test_password.py`)

- [ ] Red: tests asserting `hash_password(pw, *, n, r, p)` returns a
      self-describing PHC-style string (algorithm, params, salt_hex,
      digest_hex), `verify_password(pw, stored)` is true for the right
      password and false for a wrong one, two hashes of the same
      password differ (random salt), and a tampered field fails verify.
- [ ] Add `src/depo/util/password.py`: `hash_password` using
      `hashlib.scrypt` with an `os.urandom` salt, hex-encoded
      (`bytes.hex`) into a PHC-style string; `verify_password` parsing
      it (`bytes.fromhex`), recomputing, and comparing with
      `hmac.compare_digest`. Stdlib only, no new dependency. Do not
      reuse the Crockford codec (encode-only, built for shortcodes).
- [ ] uv run ruff check && uv run pytest
- [ ] Commit: `Ft: Add scrypt password hashing and verification`

**Add scrypt cost parameters to config**
(`tests/cli/test_defaults.py`, `tests/cli/test_config.py`)

- [ ] Red: test asserting `DepoConfig` exposes scrypt cost fields with
      sane defaults sourced from `cli/defaults.py`, and a resolution
      test that an overridden value (env or TOML) coerces to int onto
      the config, mirroring the existing override tests.
- [ ] Add `DEFAULT_SCRYPT_N` (2**14), `DEFAULT_SCRYPT_R` (8),
      `DEFAULT_SCRYPT_P` (1) to `cli/defaults.py`; add
      `scrypt_n`/`scrypt_r`/`scrypt_p` fields to `DepoConfig` sourcing
      them; add the three names to the `_coerce` `int_fields` set.
- [ ] uv run ruff check && uv run pytest
- [ ] Commit: `Ft: Add scrypt cost parameters to config`

**Add the create-user click command**
(`tests/cli/test_main.py`)

- [ ] Red: tests asserting the command creates a user with a verifying
      hash, errors on duplicate email or name (surfacing the repo
      unique violation), and reads the password without echoing it.
- [ ] Add a `create-user` command on the `cli` group in
      `src/depo/cli/main.py` taking email and name as options and the
      password via a hidden prompt (`click.password_option` or
      `prompt=..., hide_input=True`); hash via `hash_password` with
      cost params from the resolved config, write the row via
      `insert_user`.
- [ ] uv run ruff check && uv run pytest
- [ ] Commit: `Ft: Add create-user admin command`

#### Integration and documentation

- [ ] Unskip the `TestCreateUser` gating test; confirm it passes.
- [ ] Update `doc/module/util.md` (password module) and
      `doc/module/cli.md` (create-user command); note the scrypt cost
      params wherever config fields are documented.
- [ ] uv run ruff check && uv run pytest
- [ ] Commit: `Doc: ...`

#### PR

- [ ] gh pr create --title "Ft: Password credentials and provisioning" --body "..."

### Login and session (Branch: `ft/login-session`)

*Problem: users can be created and their passwords verified, but no
request is ever recognized as logged in. Add a stateless signed-cookie
session, a login route that verifies credentials and starts a session, a
logout that ends it, and a single seam that reads the current user id
from a request. Branch from `ft/credentials`. Assumes `ref/canonical-config`
has landed (scalar defaults in `cli/defaults.py`, `DepoConfig` sources
from them, `_coerce` typed field sets) and that `ft/credentials` provides
`verify_password` and `ft/users-table` provides `get_user_by_email`. Out
of scope: the `/upload` gate and `require_auth` as a route dependency
(`ft/upload-gate`, which consumes the `get_current_uid` seam this PR
builds); CSRF tokens (v1, tracked); server-side session store and
revocation (post-MVP, tracked); email login and password reset (post-MVP).*

#### Setup and gating test

- [ ] Branch `ft/login-session` from `ft/credentials`.
- [ ] Add a skipped integration test to `tests/web/test_routes.py` (new
      `TestLoginSession` class) asserting the end state: POSTing valid
      credentials to `/login` establishes a session such that a subsequent
      request is recognized as that user; bad credentials are rejected and
      re-render the form; `/logout` clears the session so a following
      request is unauthenticated. `@pytest.mark.skip` until the last unit.
  - [ ] Commit: `Tst: Add skipped gating test for login and session`

#### TDD implementation

**Add the itsdangerous dependency and session config**
(`tests/cli/test_defaults.py`, `tests/cli/test_config.py`, make_config tests)

- [ ] Add `itsdangerous` to `pyproject.toml` dependencies (Starlette
      `SessionMiddleware` requires it for cookie signing); sync the env.
- [ ] Red: tests asserting `DepoConfig` exposes `session_secret` and
      `session_https_only` sourced from `cli/defaults.py`; overrides (env
      or TOML) resolve onto the config; an empty or missing
      `session_secret` hard-fails rather than signing with a known value;
      `session_https_only` coerces to bool and defaults False.
- [ ] Add `DEFAULT_SESSION_SECRET = ""` (empty force-fail sentinel) and
      `DEFAULT_SESSION_HTTPS_ONLY = False` (plain-HTTP LAN selfhost is the
      MVP deployment; secure-only cookies would never be sent) to
      `cli/defaults.py`; add `session_secret: str` and
      `session_https_only: bool` fields to `DepoConfig` sourcing them; add
      them to `_coerce` (secret as string, https_only to the bool set);
      validate `session_secret` non-empty at resolution.
- [ ] Update `make_config` in `tests/factories` to supply a non-empty
      `session_secret` default so fixtures built from it pass the
      non-empty validation; add a test that the default is present.
- [ ] uv run ruff check && uv run pytest
- [ ] Commit: `Ft: Add itsdangerous and session config`

**Wire SessionMiddleware and the current-user seam**
(`tests/web/test_app.py`, `tests/web/test_routes.py`)

- [ ] Red: test asserting `request.session` is populated inside a handler
      (fails if the middleware is not actually in the stack); an
      unauthenticated request resolves to no current user (not a default
      uid, not a 500); a tampered or forged session cookie is rejected as
      unauthenticated; and a `uid` set in the session round-trips back
      from `get_current_uid` as an `int` (PR 4 keys auth off the type).
- [ ] In `app_factory` (`web/app.py`) call `app.add_middleware(
      SessionMiddleware, secret_key=config.session_secret,
      https_only=config.session_https_only, same_site="lax")` (the cookie
      is httponly by default). `add_middleware` wraps the whole app
      including the routers regardless of call order relative to
      `include_router`, but place it explicitly in `app_factory` so it is
      unambiguous. Add `get_current_uid(request) -> int | None` to
      `web/deps.py` reading `request.session.get("uid")`; this is the only
      function aware of `request.session` and is the seam `require_auth`
      consumes in PR 4.
- [ ] uv run ruff check && uv run pytest
- [ ] Commit: `Ft: Wire SessionMiddleware and current-user seam`

**Add the login route**
(`tests/web/test_routes.py`)

- [ ] Red: tests asserting GET `/login` renders the login form page; POST
      with valid credentials clears any prior session, sets `uid`, and
      redirects; POST with a wrong password and POST with an unknown email
      both re-render the form with a generic error and identical surface
      (no user-enumeration difference); neither logs the password.
- [ ] Add `web/routes/auth.py` with a `page_login` GET handler rendering a
      new `templates/auth/login.html` (mirroring the `page_upload` +
      `upload/page.html` idiom) and a POST handler that calls
      `get_user_by_email` then `verify_password`; on success
      `request.session.clear()` then sets `request.session["uid"]` and
      redirects (302); on failure re-renders the form with an error in the
      page body (page idiom, not the error builders). Register the auth
      router in `routes/__init__.py` among the `include_router` calls but
      before `shortcode_router` (the wildcard `/{code}` must stay last).
      Add `templates/auth/login.html` extending `base.html`.
- [ ] uv run ruff check && uv run pytest
- [ ] Commit: `Ft: Add login route`

**Add the logout route**
(`tests/web/test_routes.py`)

- [ ] Red: test asserting `/logout` clears the session, a subsequent
      request is unauthenticated, and logout redirects.
- [ ] Add a logout handler to `web/routes/auth.py` that calls
      `request.session.clear()` and redirects (302). Register on the auth
      router.
- [ ] uv run ruff check && uv run pytest
- [ ] Commit: `Ft: Add logout route`

#### Integration and documentation

- [ ] Unskip the `TestLoginSession` gating test; confirm it passes.
- [ ] Update `doc/module/web.md` (session middleware, `get_current_uid`
      seam, login/logout routes), `doc/module/templates.md` (auth/login
      template), and add `/login` and `/logout` to the reserved-namespaces
      list in `doc/design/routes.md`. Note the `session_secret` and
      `session_https_only` config fields wherever config fields are
      documented.
- [ ] uv run ruff check && uv run pytest
- [ ] Commit: `Doc: ...`

#### PR

- [ ] gh pr create --title "Ft: Login and session" --body "..."

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
