# Architecture

## Layering

Dependencies flow inward. Outer layers depend on inner layers, never the
reverse.

```
web -> service -> repo -> storage -> model -> util
 |
cli
```

- `web/` - FastAPI routes, templates, HTMX handlers, content negotiation
- `cli/` - configuration, Click entry point, dependency wiring
- `service/` - ingest/classification logic (writes), selectors (reads)
- `repo/` - persistence logic (SQLite, raw SQL)
- `storage/` - filesystem storage backend
- `model/` - DTOs, enums, policies, contracts
- `util/` - shortcode generation, validation, shared errors

## Rules

- No business logic in routes
- No framework objects below orchestration
- Core decisions are testable without HTTP
- Web layer talks to service layer only: orchestrator for writes, selector for reads
- Services write, selectors read

## Key boundaries

The CLI loads configuration and wires dependencies. The web layer receives
fully constructed dependencies through `app_factory(config)`. Config is the
single source of truth.

The orchestrator coordinates the write path: service builds a plan, repo
persists metadata, storage writes bytes. These are siblings coordinated
from above, not a chain.

The selector handles the read path with module-level functions that take
repo and storage as explicit parameters.

## Related docs

- [Shortcodes](./shortcodes.md) - content-addressed identity
- [Routes](./routes.md) - URL surface and handler conventions
- [Items](./items.md) - domain model
- [Ingest](./ingest.md) - write pipeline
