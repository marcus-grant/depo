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

## routes.py

Route definitions for API and browser layers.
TODO: Split into per-concern routers (near post-MVP).

### Routes

| Method | Path | Handler | Description |
|--------|------|---------|-------------|
| GET | `/` | `root_redirect()` | 302 redirect to `/upload` |
| GET | `/upload` | `upload_page()` | Serves upload form (HTML) |
| POST | `/upload` | `upload_form()` | Browser form upload (HTMX) |
| POST | `/api/upload` | `upload()` | API upload (multipart/raw/URL) |
| POST | `/` | `upload()` | API upload shortcut |
| GET | `/health` | `health()` | Liveness probe |
| GET | `/api/{code}/info` | `get_info()` | Key=value metadata (plain text) |
| GET | `/api/{code}/raw` | `get_raw()` | Raw content with correct MIME |
| GET | `/{code}/info` | `info_page()` | HTML info view (per-type template) |
| GET | `/{code}` | `shortcut()` | Negotiate → redirect to canonical |

Route ordering matters: specific paths before wildcards.
`/{code}` and `/{code}/info` must be last to avoid shadowing:
/health`,`/upload`, etc.

### Shortcut routing

`GET /{code}` uses `wants_html()` to detect client type:

- Browser (`Accept: text/html`) → 302 to `/{code}/info`
- API client (`Accept: */*` or absent) → 302 to `/api/{code}/raw`

No DB lookup on shortcut — canonical routes handle validation/404.

### Upload handlers

Two separate handlers for different input shapes:

**`upload()` — API path:**
Handles multipart file, raw body, URL param.
Delegates to `ingest_upload()`, returns `PlainTextResponse`.

**`upload_form()` — Browser path:**
Handles textarea content + format override from HTML form.
Delegates to `parse_form_upload()`, returns HTMX partials.

### Info page dispatch

`info_page()` dispatches to per-type templates based on item kind:

- `TextItem` → `info/text.html` (inline content + metadata)
- `PicItem` → `info/pic.html` (image display + metadata)
- `LinkItem` → `info/link.html` (clickable URL + metadata)
- Unknown kind → 500 (unexpected state)
- `NotFoundError` → 404

### Error helpers

```python
_response_404(req, code, e) -> Response   # Styled 404 page
_response_500(req, detail) -> Response     # 500 with debug context
```

## upload.py

Upload request parsing and response building.

### Types

```python
class UploadMultipartParams(TypedDict):
    payload_bytes: bytes
    filename: str
    declared_mime: str

class UploadUrlParams(TypedDict):
    link_url: str

class UploadRawBodyParams(TypedDict):
    payload_bytes: bytes
    declared_mime: str

class UploadFormParams(TypedDict):
    payload_bytes: bytes
    declared_mime: str
    requested_format: ContentFormat | None

UploadParams = UploadMultipartParams | UploadUrlParams | UploadRawBodyParams | UploadFormParams
```

Algebraic union — each variant corresponds to an upload path.
`UploadFormParams` added in PR 9 for browser form submissions.

### Functions

```python
async def parse_upload(file, url, request) -> UploadParams
```

Extracts orchestrator kwargs from API HTTP request. Branches:

- `file` present → `UploadMultipartParams`
- `url` present → `UploadUrlParams`
- Raw body detected as URL → `UploadUrlParams`
- Raw body otherwise → `UploadRawBodyParams`

```python
async def parse_form_upload(request) -> UploadFormParams
```

Extracts orchestrator kwargs from browser form submission.
Reads `content` (textarea) and `format` (select) from form data.
Empty/whitespace content raises `ValueError`.
Non-empty format string converted to `ContentFormat` enum.

```python
def upload_response(result: PersistResult) -> PlainTextResponse
```

Builds response with short code body and
`X-Depo-Code`, `X-Depo-Kind`, `X-Depo-Created` headers.
201 for new, 200 for dedupe.

```python
async def ingest_upload(file, url, request, orchestrator) -> PersistResult
```

Parse API request and ingest. Returns `PersistResult`.
Raises `ValueError`, `ImportError`, or `PayloadTooLargeError` on failure.
Replaces former `execute_upload()` — response formatting moved to route handlers.

### Helper

```python
_looks_like_url(data: bytes) -> bool
```

Naive URL detection via regex. TODO: Move to ingestion pipeline.

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

**Template markers** — every template has boundary comments for debugging and testing:

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

**Shortcode display** uses `<code class="shortcode">` as a project-wide convention.
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
