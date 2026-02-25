# Module organization

This document describes how application code is organized and why.

The project uses a **pattern-first, layered module structure**.
Modules are organized by responsibility, not by feature.

Directory names are singular to reflect hierarchy.

## Organizing principles

- Separate domain logic from infrastructure
- Keep framework-specific code at the edges
- Prefer explicit boundaries over convenience
- Make dependencies flow inward

Lower layers must not depend on higher layers.

## Top-level modules

The application code lives under `src/depo/`.

### model/

Domain models, DTOs, and enums.
Pure Python with no I/O dependencies.

This module must not depend on:

- FastAPI
- database libraries
- filesystem or network I/O

See [model.md](./model.md) for field specifications.

### service/

Application services and use cases.

This includes:

- ingest logic
- orchestration of models, repositories, and storage
- pure decision-making code where possible

Services may depend on:

- model/
- repository interfaces
- storage interfaces

Services must not depend on:

- FastAPI
- concrete database or storage implementations

See [service.md](./service.md) for interface specifications.

### repo/

Persistence layer.

This includes:

- repository interfaces
- SQLite implementations
- transaction and collision-handling logic

This module translates between:

- database representations
- domain models

See [repo.md](./repo.md) for interface specifications.

### storage/

Payload storage backends.

This includes:

- filesystem storage implementation
- storage interfaces

This module is responsible only for bytes in and bytes out.

See [storage.md](./storage.md) for interface specifications.

### cli/

Command-line interface and configuration.

This includes:

- configuration resolution (config.py)
- Click CLI commands (main.py)
- `python -m depo` entry point

Configuration is the dependency root -
all downstream components receive config values.

See [cli.md](./cli.md) for interface specifications.

### web/

HTTP boundary of the application.
This includes:

- FastAPI app setup
- routes and handlers
- request and response schemas
- dependency wiring
- Jinja2 templates and static assets

This is the only place FastAPI should appear.
See [web.md](./web.md) for interface specifications.

### templates/

Jinja2 templates served by the web layer.
This includes:

- page layouts and inheritance hierarchy
- info page system with shared shell and type partials
- error pages
- partials and HTMX fragments

See [templates.md](./templates.md) for structure and conventions.

### util/

Shared utilities with no domain dependencies.
This includes:

- hashing and canonicalization (shortcode.py)
- input validation (validate.py)

Utilities are pure functions with no model or service imports.

See [util.md](./util.md) for function specifications.

## Tests

Tests live outside the application package under the top-level `tests/` directory.

This project uses a `src/` layout. As a result:

- tests must import the application as an installed package
- tests must not rely on relative imports or filesystem layout
- accidental coupling to implementation details is avoided

This is intentional and enforced to support strict TDD workflows.

### Test organization

Tests mirror the application structure by responsibility:

- `tests/model/`    -> tests for domain models and invariants
- `tests/service/`  -> tests for application services and use cases
- `tests/repo/`     -> tests for repository behavior
- `tests/storage/`  -> tests for storage backends
- `tests/web/`      -> tests for HTTP behavior
  - `routes/`       -> route selection, status codes, content types
  - `test_templates.py`       -> base template infrastructure
  - `test_info_templates.py`  -> info page template structure and content
  - `test_error_templates.py` -> error page template structure

`tests/factories/` provides shared test helpers:
model factories (make_link_item, make_text_item, make_pic_item),
client factories, and render_template for direct Jinja2 template rendering.

Test code should prefer black-box behavior over internal details.

If a test requires intimate knowledge of internals, that is a signal that
module boundaries may be leaking or need refinement.

## Relationship to FastAPI conventions

This structure aligns with common FastAPI community guidance:

- layered separation
- thin route handlers
- business logic outside HTTP handlers

For reference, see:

- <https://github.com/zhanymkanov/fastapi-best-practices>

This project adopts those principles while enforcing stricter
domain and framework boundaries.
