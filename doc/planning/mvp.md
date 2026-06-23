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

### Login and session (Branch: `ft/login-session`)

*Problem: users can be created and their passwords verified, and session
config infrastructure is in place, but no request is ever recognized as
logged in. Wire the signed-cookie SessionMiddleware, a login route that
verifies credentials and starts a session, a logout route that ends it,
and a seam that reads the current user id from a request. Branch from
`ft/login-config`, which provides `session_secret`, `session_https_only`,
and the non-empty secret validation. Requires `verify_password` from
`ft/credentials` and `get_user_by_email` from `ft/users-table`, both
already merged. Out of scope: the `/upload` gate and `require_auth` as a
route dependency (`ft/upload-gate`, which consumes the `get_current_uid`
seam this PR builds); CSRF tokens (v1, tracked); server-side session
store and revocation (post-MVP, tracked); email login and password reset
(post-MVP).*

#### Setup and gating test

- [x] Branch `ft/login-session` from `ft/credentials`.
- [x] Add a skipped integration test to `tests/web/test_routes.py` (new
      `TestLoginSession` class) asserting the end state: POSTing valid
      credentials to `/login` establishes a session such that a subsequent
      request is recognized as that user; bad credentials are rejected and
      re-render the form; `/logout` clears the session so a following
      request is unauthenticated. `@pytest.mark.skip` until the last unit.
  - [x] Commit: `Tst: Add skipped gating test for login and session`

#### TDD implementation

*Note: the session config unit originally planned here was split into a
separate `ft/login-config` PR. That PR delivered `session_secret` and
`session_https_only` config fields, `_coerce_bool` with strict token
validation, empty-secret validation in `load_config`, `make_config`
factory secret default, and all associated test infrastructure. The
remaining work below assumes `ft/login-config` is merged.*

- [x] Commit: `Ft: Add session config fields and bool coercion`
- [x] Commit: `Ref: Extract _coerce_bool and DRY out bool coercion tests`
- [x] Commit: `Ref: DRY out TestLoadConfigEnv boilerplate`
- [x] Commit: `Ref: DRY out TestLoadConfigToml and TestLoadConfigFlag`
- [x] Commit: `Ft: Add non-empty session_secret default to make_config`

**Add the itsdangerous dependency**

- [ ] Add `itsdangerous` to `pyproject.toml` dependencies (Starlette
      `SessionMiddleware` requires it for cookie signing); sync the env.
- [ ] Commit: `Chr: Add itsdangerous dependency`

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
      list in `doc/design/routes.md`.
- [ ] uv run ruff check && uv run pytest
- [ ] Commit: `Doc: Update web and template docs for ft/login-session`

#### PR

- [ ] gh pr create --title "Ft: Login and session" --body "..."

### Upload gate (Branch: `ft/upload-gate`)

*Problem: any anonymous visitor can POST to `/upload` and create items
with the default `uid=0`. The MVP-critical requirement is that no
anonymous POST is ever possible. Add a web-layer `require_auth`
dependency that gates both `/upload` routes, a 401 `AuthRequiredError`,
and thread the authenticated uid into the existing ingest path so items
persist with the real uploader's id instead of 0. Branch from `ft/login-session`.
Out of scope: `perm`/visibility enforcement and any 403/ownership checks
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
is chosen, that unit changes to return-redirect-for-browser-context.
`fix/form-error-surface` has landed; the builder shape is settled.

Mechanics note on (b): a FastAPI `Depends` cannot short-circuit by
returning a `Response`; a returned value only populates the parameter.
So "return the redirect" is not directly possible. (b) in practice means
raising a redirect-carrying exception handled at the boundary, which
collapses it toward (c). Pick (b) only with that understanding.

#### Setup and gating test

- [ ] Branch `ft/upload-gate` from `ft/login-session`.
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

### Pre-MVP housecleaning

- Rename `tests/factories/db.py::insert_user` to `seed_user` to resolve
  naming overlap with `SqliteRepository.insert_user`
- Split `src/depo/repo/sqlite.py` into per-concern submodules (items,
  users, schema) once the auth sequence lands
- Standardize scrypt cost params in password tests to minimum values
  (n=2, r=1, p=1); some tests still use n=2**14 making the suite slow
- Revisit scrypt N=2**16 choice against a timing benchmark on target
  hardware; OWASP floor is 2**17, current value is a split-the-difference
  estimate without a measured baseline
- Replace empirical maxmem formula (256*n*r*p + 1MiB) in password.py
  with a principled bound once OpenSSL's internal buffer requirement is
  confirmed
- Plan session secret management UX and dev/prod mode: a `DEPO_MODE`
  config field (`dev`/`prod`), a `gen-secret` CLI command printing a
  suitable random secret to stdout, and adjusted `load_config` behaviour
  per mode (dev auto-generates an ephemeral secret with a warning; prod
  keeps the hard-fail sentinel)
- Write a deployment/ops doc covering required config for a running
  instance: DEPO_SESSION_SECRET, WAL journal mode, store directory
  setup, and recommended depo.toml fields

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
