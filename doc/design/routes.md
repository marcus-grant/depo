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
- `POST /upload` - `upload()`. Delegates to `hx_upload` or `api_upload`.

### Single-context routes

- `GET /{code}/raw` - `raw()`
  - Always raw bytes + metadata headers.
  - No negotiation.
- `GET /upload` - `page_upload()`.
  - Upload form, full page render.
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

### Reserved Namespaces - Post-MVP additions

- `/a/{alias}` or `/alias/{alias}` - mutable references to items
- `/tag/{tag}` - discovery and grouping

## Related docs

- [Architecture](./architecture.md) - layering and web layer role
- [Shortcodes](./shortcodes.md) - how codes are generated and resolved
- [Module reference: web/](../module/web.md) - implementation details
