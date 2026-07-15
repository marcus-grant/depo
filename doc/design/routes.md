# Routes

Item-first URL structure. The shortcode is the primary interface.

## Route surface

### Dispatchers

These negotiate request context and delegate to a specific handler.

- `GET /{code}`
  - `item()`.
  - Browser gets info page, API gets raw content.
  - LinkItem always redirects (302) regardless of context.
- `GET /{code}/info` - `info()`. Delegates to `page_info`, `hx_info`, or `api_info`.
- `POST /upload` - `upload()`
  - Delegates to `hx_upload` or `api_upload`.
  - Also handles multipart form data & file uploads with file upload element.
  - Gated by `require_auth`.
    - Threads the session uid into every ingest path.
    - So a created item carries the uploading user's id.

### Single-context routes

- `GET /{code}/raw` - `raw()`
  - Always raw bytes + metadata headers.
  - No negotiation.
- `GET /{code}.{ext}` - `raw_ext()`
  - Same as raw but extension must match item format.
  - Mismatch returns 404. Links always 404.
  - Register before `/{code}` to prevent wildcard swallowing.
- `GET /upload` - `page_upload()`.
  - Upload form, full page render.
  - File picker embedded into text area to drop files or click to pick.
  - Gated by `require_auth`.
    - An unauthenticated request gets a 401 with login link rather than form.
- `GET /health` - `health()`.
  - Liveness probe.

## Handler naming

Prefixes describe the response context:

- No prefix - dispatchers only. Negotiate and delegate.
- `page_` - full page renders (HTML, Jinja2 templates)
- `hx_` - HTMX partial responses
- `api_` - API/plain text responses

Method prefixes (like `hx_post_` or `api_get_`) are only used where the
HTTP method would otherwise be ambiguous.

## Content negotiation

Dispatchers inspect request context to choose a handler:

- `is_htmx(request)` - checks for `HX-Request` header
- `wants_html(request)` - checks Accept header for `text/html`

The negotiation is a thin dispatch, not interleaved with handler logic.
Each handler is explicitly named and does one thing.

## Authentication

Gated routes take `Depends(require_auth)`.
Dependency reads the session uid and raises `AuthRequiredError` when there is none,
so an unauthenticated request is rejected during dependency resolution.
The handler body never runs.
No bytes are parsed, nothing is persisted.

Rejection is a uniform 401 on every surface.
An unauthenticated request is not redirected to `/login`:
a redirect would launder an authorization failure into a navigation event.
The status on the wire would say the request succeeded going somewhere,
not that it was refused.

Instead, the UI surfaces carry the way forward in the body.
The browser error page and the htmx error partial both
render a link to `/login` alongside the error message.
The API surface returns the message as plaintext.

The htmx surface is the one exception to the uniform status,
and it is a temporary one:
`htmx_error` hard-codes 200 so htmx will swap the partial into the DOM.
Migrating the htmx error surfaces to honest status codes is tracked in planning.

Currently gated: `GET /upload`, `POST /upload`.

## Router organization

Routes package at `src/depo/web/routes/`.
Each domain owns its router.
`__init__.py` wires routers and holds fixed-path handlers
(health, redirects, POST / alias).
Fixed-path handlers register before domain routers.
Wild-card router (shortcode) registers last to avoid shadowing.

- `upload.py`
  - `upload_router`
  - upload dispatch and handlers
- `shortcode.py`
  - `shortcode_router`
  - item/info/raw handlers

## Reserved namespaces

These top-level prefixes are reserved and must not conflict with short-codes:

- `/upload`
- `/health`
- `/login`
- `/logout`

### Reserved Namespaces - Post-MVP additions

- `/a/{alias}` or `/alias/{alias}` - mutable references to items
- `/tag/{tag}` - discovery and grouping

## Related docs

- [Architecture](./architecture.md) - layering and web layer role
- [Shortcodes](./shortcodes.md) - how codes are generated and resolved
- [Module reference: web/](../module/web.md) - implementation details
