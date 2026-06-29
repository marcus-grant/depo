# web/ module

FastAPI application layer.
Depends on service/, repo/, storage/, model/, cli/.

## app.py

Application factory and logging setup.
Wires dependencies from DepoConfig.

### Functions

```python
app_factory(config: DepoConfig) -> FastAPI
configure_logging(level: str) -> None
```

`app_factory` creates the FastAPI instance, initializes DB and storage,
wires repo/storage/orchestrator onto `app.state`.
Includes route handlers via `APIRouter`.
Registers the `unhandled` boundary via
`add_exception_handler(Exception, ...)` to
catch non-DepoError exceptions that escape routes.
Mounts static files from `src/depo/static/`.
SQLite uses `check_same_thread=False` for async handler compatibility.
Also wires `SessionMiddleware` (itsdangerous signed cookies) using
`config.session_secret` and `config.session_https_only`.

`configure_logging` sets the `depo` logger level and attaches a text handler.
`app_factory` calls it as its first step, driven by `config.log_level`.

## routes/

Route package. Domain routers in sub-modules, wiring in `__init__.py`.

### init.py

Wires domain routers and registers fixed-path handlers.
Fixed-path decorators before `include_router` calls.
Wildcard shortcode router included last.

| Method | Path | Handler | Description |
|--------|------|---------|-------------|
| GET | `/` | `root_redirect()` | 302 redirect to `/upload` |
| GET | `/health` | `health()` | Liveness probe |
| POST | `/` | `upload()` | Alias, forwards to upload dispatcher |

### auth.py

Authentication router. Login and logout routes.

| Method | Path | Handler | Description |
|--------|------|---------|-------------|
| GET | `/login` | `page_login()` | Render login form; redir. `/` if auth'd |
| POST | `/login` | `handle_login()` | *`^`* |
| GET | `/logout` | `handle_logout()` | Clears session and redirects to `/` |

>`^`: Check credentials, start session on ack, re-renders form with error if fail

`_render_login(request, error)` unifies all login-page renders.
GET and both failure paths call it; `error` is `None` on the GET and
an `AuthenticationError` instance on failure.
Both failure paths (unknown email, wrong password) produce an identical 401 surface.

### shortcode.py

Shortcode router. Wildcard routes, must register last.

| Method | Path | Handler | Description |
|--------|------|---------|-------------|
| GET | `/{code}` | `item()` | Dispatcher, browser to info, API to raw |
| GET | `/{code}/info` | `info()` | Dispatcher, delegate page_info or api_info |
| GET | `/{code}/raw` | `raw()` | Raw content with correct MIME, no negotiation |

Item dispatch (`item()`):

- Browser (`Accept: text/html`) -> 302 to `/{code}/info`
- API client -> 302 to `/{code}/raw`
- No DB lookup, canonical routes handle validation/404.

Info dispatch (`info()`):

- `wants_html` -> `page_info` (per-type template)
- Otherwise -> `api_info` (key=value plaintext)

Page info dispatches to per-type templates:

- `TextItem` -> `info/text.html` (inline content + metadata)
- `PicItem` -> `info/pic.html` (image display + metadata)
- `LinkItem` -> `info/link.html` (clickable URL + metadata)

### upload.py

Upload router, handlers, and request helpers.

| Method | Path | Handler | Description |
|--------|------|---------|-------------|
| GET | `/upload` | `page_upload()` | Upload form, full page |
| POST | `/upload` | `upload()` | Dispatcher, HX to hx_upload else api_upload |

#### Types

Algebraic union, each variant corresponds to an upload path.

- `UploadMultipartParams` - payload_bytes, filename, declared_mime
- `UploadRawBodyParams` - payload_bytes, declared_mime
- `UploadFormParams` - payload_bytes, declared_mime, requested_format

#### upload.py - functions

- `_parse_upload(file, url, request)`:
  - extract orchestrator kwargs from API request
- `_parse_form_upload(request)`
  - extract kwargs from browser form submission
- `_upload_response(result)`
  - build PlainTextResponse with:
  - X-Depo-Code, X-Depo-Kind, X-Depo-Format, X-Depo-Created headers.
  - 201 new, 200 dedupe.
- `_ingest_upload(file, url, request, orchestrator)`
  - parse and ingest, returns PersistResult

## negotiate.py

Content negotiation utilities.

```python
def wants_html(request: Request) -> bool
```

Checks if `text/html` appears in the `Accept` header.
Browsers always include it; curl and API clients do not.
Used by shortcut route to dispatch to canonical endpoint.

## templates.py

Template rendering utilities.

```python
def get_templates() -> Jinja2Templates
```

Returns `Jinja2Templates` instance pointing at `src/depo/templates/`.

```python
def is_htmx(request: Request) -> bool
```

Checks for `HX-Request` header. Used to decide between
full page response and HTMX fragment/partial.

## deps.py

FastAPI dependency providers via `Depends()`.

```python
get_repo(request) -> SqliteRepository
get_storage(request) -> StorageBackend
get_orchestrator(request) -> IngestOrchestrator
get_current_uid(request) -> int | None
```

Thin getters pulling from `request.app.state`.

`get_current_uid` reads request.session.get("uid");
the only function in the web layer that touches `request.session` directly.
`require_auth` in `ft/upload-gate` calls it to enforce authenticated access.

## Templates

See [templates.md](./templates.md) for
template structure, inheritance, conventions, and testing patterns.

## HTMX Patterns

### Upload flow

1. Form at `/upload` has `hx-post="/upload"`, `hx-target="#result"`, `hx-swap="innerHTML"`
2. User submits → `upload_form()` processes
3. Success → `partials/success.html` swapped into `#result` (shortcode + info link)
4. Error → `errors/partial.html` swapped into `#result` (error message)
5. User stays on form, ready for next upload (multi-upload workflow)

### Request detection

`is_htmx(request)` checks `HX-Request` header.
Currently used implicitly by `upload_form()` always returning partials.
Future: may need full-page fallback for non-JS browsers.

## Static Assets

Bundled locally, served via FastAPI `StaticFiles` mount at `/static`.

```txt
static/
├── css/
│   ├── pico.min.css         # Pico CSS framework
│   └── depo.css             # Palette B custom property overrides
└── js/
    └── htmx.min.js          # HTMX library
```

Everything served comes from the deployed host; no CDN dependencies.

## Error Handling

Error handling is centralized in
`depo.util.errors` with a typed exception hierarchy rooted at `DepoError`.
All exceptions carry
`status`, `message`, `ctx`, `severity`, and `exception` fields.
Route handlers catch `DepoError` broadly using `e.status` for response codes.

Response builders live in `depo.web.error`. Each returns a finished
`Response`:

- `api_error(e)`
  - `PlainTextResponse` with `e.status`
- `htmx_error(req, e, role="alert")`
  - `errors/partial.html` `TemplateResponse` hardcoded at `status_code=200`
  - role as CSS modifier and ARIA attribute
- `browser_error(req, e)`
  - full-page `TemplateResponse` using `errors/page.html` at `e.status`

These builders are also the single logging seam:
each calls `log_error(e)`, emitting one record at `e.severity`,
attaching `exc_info` when `e.exception` is set.

Non-DepoError exceptions that escape a route are caught by
the app-level boundary `unhandled`, registered in `app_factory`.
It wraps the exception in `UnknownServerError`, negotiates surface,
and delegates to a builder.
It does not log; the builder does.

See [errors.md](../design/errors.md) for the full hierarchy and patterns.
