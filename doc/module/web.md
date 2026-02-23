# web/ module

FastAPI application layer. Depends on service/, repo/, storage/, model/, cli/.

## app.py

Application factory. Wires dependencies from DepoConfig.

### Function

```python
app_factory(config: DepoConfig) -> FastAPI
```

Creates FastAPI instance, initializes DB and storage,
wires repo/storage/orchestrator onto `app.state`.
Includes route handlers via `APIRouter`.
Mounts static files from `src/depo/static/`.
SQLite uses `check_same_thread=False` for async handler compatibility.

## routes/

Route package. Domain routers in sub-modules, wiring in `__init__.py`.

### __init__.py

Wires domain routers and registers fixed-path handlers.
Fixed-path decorators before `include_router` calls.
Wildcard shortcode router included last.

| Method | Path | Handler | Description |
|--------|------|---------|-------------|
| GET | `/` | `root_redirect()` | 302 redirect to `/upload` |
| GET | `/health` | `health()` | Liveness probe |
| POST | `/` | `upload()` | Alias, forwards to upload dispatcher |

### shortcode.py

Shortcode router. Wildcard routes, must register last.

| Method | Path | Handler | Description |
|--------|------|---------|-------------|
| GET | `/{code}` | `item()` | Dispatcher, browser to info, API to raw |
| GET | `/{code}/info` | `info()` | Dispatcher, delegates to page_info or api_info |
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
- Unknown kind -> 500
- `NotFoundError` -> 404

Error helpers (local, pending extraction):

- `_response_404(req, code, e)` -> styled 404 page
- `_response_500(req, detail)` -> 500 with debug context

### upload.py

Upload router, handlers, and request helpers.

| Method | Path | Handler | Description |
|--------|------|---------|-------------|
| GET | `/upload` | `page_upload()` | Upload form, full page |
| POST | `/upload` | `upload()` | Dispatcher, HX-Request to hx_upload, else api_upload |

#### Types

Algebraic union, each variant corresponds to an upload path.

- `UploadMultipartParams` — payload_bytes, filename, declared_mime
- `UploadRawBodyParams` — payload_bytes, declared_mime
- `UploadFormParams` — payload_bytes, declared_mime, requested_format

#### Functions

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
```

Thin getters pulling from `request.app.state`.

## Templates

### Structure

```txt
templates/
├── base.html                # Full page layout wrapper
├── upload.html              # Upload form (extends base.html)
├── info/
│   ├── text.html            # TextItem info view
│   ├── pic.html             # PicItem info view
│   └── link.html            # LinkItem info view
├── partials/
│   ├── success.html         # Upload success (HTMX fragment)
│   └── error.html           # Validation error (HTMX fragment)
└── errors/
    ├── 404.html             # Not found page
    └── 500.html             # Internal error with debug context
```

### Conventions

__Template markers__ — every template has boundary comments for debugging and testing:

```html
<!-- BEGIN: template-name.html -->
...
<!-- END: template-name.html -->
```

Child templates note their relationship:

```html
<!-- BEGIN: upload.html -->
<!-- EXTENDS: base.html -->
```

Fragments note their role:

```html
<!-- BEGIN: partials/success.html (fragment) -->
```

#### Full pages

Extend `base.html` and fill `{% block content %}`.
Markers must be inside the block
(Jinja2 discards content outside blocks in child templates).

#### Partials/fragments

Standalone — no extends, no base layout.
Returned directly for HTMX requests (`HX-Request` header present).

__Shortcode display__ uses `<code class="shortcode">` as a project-wide convention.
The `shortcode` class is functional (tested against), not purely visual.

## HTMX Patterns

### Upload flow

1. Form at `/upload` has `hx-post="/upload"`, `hx-target="#result"`, `hx-swap="innerHTML"`
2. User submits → `upload_form()` processes
3. Success → `partials/success.html` swapped into `#result` (shortcode + info link)
4. Error → `partials/error.html` swapped into `#result` (error message)
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

Everything served comes from the deployed host — no CDN dependencies.

## Error Handling

| Error | API Response | Browser Response |
|-------|-------------|------------------|
| `ValueError` | 400 plain text | Error partial |
| `PayloadTooLargeError` | 413 plain text | Error partial (413) |
| `ImportError` | 501 plain text | Error partial |
| `NotFoundError` | 404 plain text | Styled 404 page |
| Unexpected state | — | 500 with debug context |

`PayloadTooLargeError` must be caught before `ValueError` (it inherits from it).
