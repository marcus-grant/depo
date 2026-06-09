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

**Enable WAL journal mode and busy timeout**
(`tests/repo/test_sqlite.py`)

- [ ] Red: test asserting `PRAGMA journal_mode` resolves to `wal` after
      `init_db`, and that `busy_timeout` is set on the connection (so a
      separate-process writer, the `set-password` command in
      `ft/credentials`, can commit without `database is locked`).
- [ ] In `init_db` (`src/depo/repo/sqlite.py`) add `PRAGMA journal_mode =
      WAL`, `PRAGMA busy_timeout = <ms>`, and `PRAGMA synchronous =
      NORMAL` beside the existing `PRAGMA foreign_keys = ON`.
      `journal_mode` persists in the DB file; `busy_timeout` is
      per-connection, set on every `init_db` call (server and CLI alike).
      Out of scope: thread-safety of the web app's shared connection
      (the `app.py` thread-pooling/write-queuing note is a separate
      deferred concern; WAL does not address it).
- [ ] uv run ruff check && uv run pytest
- [ ] Commit: `Ft: Enable WAL journal mode and busy timeout`

**Add the User domain model**

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

**Add user password-hash update**
(`tests/repo/test_sqlite.py`)

- [ ] Red: test asserting `update_user_pw_hash(uid, new_hash)` changes
      the stored `pw_hash` for an existing user (fetch confirms the new
      value) and that an unknown uid raises `NotFoundError`.
- [ ] Add `update_user_pw_hash(uid, new_hash)` to
      `src/depo/repo/sqlite.py` following the existing write idioms: a
      single `UPDATE users SET pw_hash = ? WHERE id = ?`, raising
      `NotFoundError` when no row is affected.
- [ ] uv run ruff check && uv run pytest
- [ ] Commit: `Ft: Add user password-hash update`

#### Integration and documentation

- [ ] Unskip the `TestUserPersistence` gating test; confirm it passes.
- [ ] Update `doc/module/model.md` (User model) and `doc/module/repo.md`
      (user CRUD, `update_user_pw_hash`, and the WAL / busy_timeout /
      synchronous connection config); note the `items.uid` foreign key
      wherever the schema is documented.
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

**Add the set-password admin command**
(`tests/cli/test_main.py`)

- [ ] Red: tests asserting the command changes an existing user's
      password (the new password verifies via `verify_password`, the old
      no longer does), accepts either an email or a numeric id and
      resolves an email through `get_user_by_email` to a uid, errors
      cleanly if the user does not exist, and reads the new password via
      a hidden prompt without echoing it.
- [ ] Add a `set-password` command on the `cli` group in
      `src/depo/cli/main.py`: resolve the target to a uid (numeric id used
      directly; email looked up via `get_user_by_email`), hash the new
      password via `hash_password` with cost params from the resolved
      config, and write via `update_user_pw_hash`. Surface a clean CLI
      error (not a traceback) when the user is not found.
- [ ] uv run ruff check && uv run pytest
- [ ] Commit: `Ft: Add set-password admin command`

#### Integration and documentation

- [ ] Unskip the `TestCreateUser` gating test; confirm it passes.
- [ ] Update `doc/module/util.md` (password module) and
      `doc/module/cli.md` (create-user and set-password commands); note
      the scrypt cost params wherever config fields are documented.
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

### Upload gate (Branch: `ft/upload-gate`)

*Problem: any anonymous visitor can POST to `/upload` and create items
with the default `uid=0`. The MVP-critical requirement is that no
anonymous POST is ever possible. Add a web-layer `require_auth`
dependency that gates both `/upload` routes, a 401 `AuthRequiredError`,
and thread the authenticated uid into the existing ingest path so items
persist with the real uploader's id instead of 0. Branch from
`ft/login-session`. PRECONDITION: this branches only AFTER
`fix/form-error-surface` has merged (auth adds an unauthenticated path
to the same upload dispatcher and relies on that dispatcher's error
surfaces being correct); confirm it has landed before branching. Out of
scope: `perm`/visibility enforcement and any 403/ownership checks
(post-MVP, the column is present and ingest already passes the PUBLIC
default); roles and user relations (post-MVP); per-item ownership on
read/delete (post-MVP); CSRF (v1, tracked); rate limiting (post-MVP);
gating any route other than the two `/upload` routes.*

*Open decision (resolve before the require_auth and gate units): the auth
failure raises `AuthRequiredError(DepoError, status=401)`. The per-surface
response is settled in intent: plain browser 302 to `/login`, pure API a
plain 401, HTMX a client navigation to `/login` (via `HX-Redirect`) rather
than an inline error. Two coupled things are UNRESOLVED. First, the HTMX
case does NOT fit `htmx_error`'s established contract (200 + an error
partial in the body); an `HX-Redirect` navigation is a distinct response,
so either `htmx_error` learns a redirect mode or the HTMX auth failure
short-circuits to a dedicated redirect response that never enters the
error-partial path. Second, where the redirect-vs-render negotiation lives:
(a) `require_auth` raises and the three builders negotiate surface
(centralizes it but couples the generic error seam to auth-specific
redirect logic), or (b) `require_auth` returns the redirect directly for
browser/HTMX context and only raises for API (keeps the builders generic
but splits the gate's behavior by surface), or (c) `AuthRequiredError`
carries a redirect target and the builders gain a generic
redirect-instead-of-render rule (reusable, larger builder-contract change).
The require_auth unit below is written assuming (a)/(c) (it raises); if (b)
is chosen, that unit changes to return-redirect-for-browser-context. All
three interact with `fix/form-error-surface`, which reshapes the same
builders, so confirm that branch's final builder shape before implementing
either the require_auth or the gate units.*

Mechanics note on (b): a FastAPI `Depends` cannot short-circuit by
returning a `Response`; a returned value only populates the parameter.
So "return the redirect" is not directly possible. (b) in practice means
raising a redirect-carrying exception handled at the boundary, which
collapses it toward (c). Pick (b) only with that understanding.

#### Setup and gating test

- [ ] Confirm `fix/form-error-surface` has merged; branch
      `ft/upload-gate` from `ft/login-session`.
- [ ] Add a skipped integration test to `tests/web/test_routes.py` (new
      `TestUploadGate` class) asserting the MVP guarantee end to end: an
      unauthenticated POST `/upload` is rejected and creates no item; an
      authenticated client (session established via `/login`) POST
      `/upload` creates an item whose `uid` is the logged-in user, not 0.
      Assert the invariant (rejected, no item, correct uid on success),
      NOT the per-surface mechanism (302 vs `HX-Redirect` vs error
      partial) which the builder open-decision settles and the per-route
      gate units assert. `@pytest.mark.skip` until the last unit.
  - [ ] Commit: `Tst: Add skipped gating test for upload gate`

#### TDD implementation

**Add the AuthRequiredError type**
(`tests/util/test_errors.py`)

- [ ] Red: tests asserting `AuthRequiredError` is a `DepoError` subclass
      with status 401 and `Severity.INFO` (unauthenticated traffic is
      expected, not a fault), and a pass-through constructor. Add
      `AuthRequiredError: Severity.INFO` to the gap-test `EXPECTED` dict
      so `descendants(DepoError) == set(EXPECTED)` still holds (a new
      concrete error without a severity decision fails the suite).
- [ ] Add `AuthRequiredError(DepoError)` to `src/depo/util/errors.py` as
      a new top-level domain base (parallel to `RepoError` /
      `ValidationError`): `status = 401`, `severity = Severity.INFO`,
      pass-through `__init__`.
- [ ] uv run ruff check && uv run pytest
- [ ] Commit: `Ft: Add AuthRequiredError type`

**Thread authenticated uid through ingest**
(`tests/service/test_orchestrator.py`)

- [ ] Red: test asserting `ingest(uid=N)` persists an item with
      `items.uid == N` (currently `ingest` accepts `uid` but drops it:
      the `self._repo.insert(plan)` call omits it, so a non-default uid
      never reaches the row).
- [ ] In `IngestOrchestrator.ingest` (`src/depo/service/orchestrator.py`)
      pass the param through: `self._repo.insert(plan, uid=uid)`.
      `repo.insert` already accepts and writes `uid`; this is the missing
      link, not a repo change.
- [ ] uv run ruff check && uv run pytest
- [ ] Commit: `Ft: Thread authenticated uid through ingest`

**Add the require_auth dependency**
(`tests/web/test_deps.py`, new)

- [ ] Red: tests asserting `require_auth` yields the uid when a valid
      session is present, and raises `AuthRequiredError` when there is no
      session uid. Built on `get_current_uid` (PR 3); yields the bare uid
      (the upload path only needs the int, and this keeps `pw_hash` out
      of request scope). For MVP, yielding the session uid without a
      confirming user fetch is acceptable: `items.uid` is FK-checked at
      insert, so a stale-cookie / deleted-user uid fails at the FK rather
      than persisting. (If the chosen design instead fetches to validate,
      a missing row is an auth failure, raise `AuthRequiredError`, not a
      500.)
- [ ] Add `require_auth(request) -> int` to `src/depo/web/deps.py`,
      reading `get_current_uid` and raising `AuthRequiredError` on None.
      (Written assuming open-decision option (a)/(c): raises, builders
      negotiate. Under (b) this returns a redirect for browser/HTMX
      context and raises only for API.)
- [ ] uv run ruff check && uv run pytest
- [ ] Commit: `Ft: Add require_auth dependency`

**Gate POST /upload and pass uid to ingest**
(`tests/web/test_routes.py`)

- [ ] Red: tests asserting an unauthenticated POST `/upload` is rejected
      and creates no item, and an authenticated POST creates an item with
      the session user's uid. Assert the per-surface mechanism settled by
      the open decision (401 api; HTMX client-navigation to `/login`;
      302 to `/login` for a non-HTMX form). Cover the dispatcher and both
      `hx_`/`api_` paths.
- [ ] Wire `require_auth` into the `upload` dispatcher in
      `src/depo/web/routes/upload.py` via `Depends(require_auth)`, and
      pass the yielded uid into `orch.ingest(uid=...)` in the dispatcher
      and the `hx_`/`api_`/`_ingest_upload` call sites that currently call
      `ingest` with no uid.
- [ ] uv run ruff check && uv run pytest
- [ ] Commit: `Ft: Gate POST /upload and pass uid to ingest`

**Gate GET /upload (the form)**
(`tests/web/test_routes.py`)

- [ ] Red: tests asserting an unauthenticated GET `/upload` does not
      render the form and redirects to `/login` (302 for a browser; the
      HTMX-GET case, if the form is ever fetched via HTMX, uses the same
      client-navigation mechanism settled in the open decision), and an
      authenticated GET renders the form.
- [ ] Wire `require_auth` into `page_upload` in
      `src/depo/web/routes/upload.py` via `Depends(require_auth)`.
- [ ] uv run ruff check && uv run pytest
- [ ] Commit: `Ft: Gate GET /upload form`

#### Integration and documentation

- [ ] Unskip the `TestUploadGate` gating test; confirm it passes.
- [ ] Update `doc/module/web.md` (`require_auth`, the gated `/upload`
      routes), `doc/module/util.md` and `doc/design/errors.md`
      (`AuthRequiredError`, the new 401 top-level domain base), and
      `doc/module/service.md` (ingest now threads uid to the row).
- [ ] Record a post-MVP item in the post-MVP planning doc: examine
      moving `pw_hash` into a dedicated `credentials` table associated to
      a user (keeps `users`/`User` hash-free by construction, confines
      the hash to the credential layer, room for multiple auth methods
      per user). Open: one-to-one vs one-to-many; when it lands.
- [ ] uv run ruff check && uv run pytest
- [ ] Commit: `Doc: ...`

#### PR

- [ ] gh pr create --title "Ft: Upload gate" --body "..."

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
