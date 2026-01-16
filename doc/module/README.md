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

Domain models and contracts.

This includes:

- core entities (Item, TextItem, PicItem, LinkItem)
- DTOs (WritePlan)
- enums and value objects
- invariants and structural rules

This module must not depend on:

- FastAPI
- database libraries
- filesystem or network I/O

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

### repo/

Persistence layer.

This includes:

- repository interfaces
- SQLite implementations
- transaction and collision-handling logic

This module translates between:

- database representations
- domain models

### storage/

Payload storage backends.

This includes:

- filesystem storage implementation
- storage interfaces

This module is responsible only for bytes in and bytes out.

### web/

HTTP boundary of the application.

This includes:

- FastAPI app setup
- routes and handlers
- request and response schemas
- dependency wiring

This is the only place FastAPI should appear.

### util/

Shared utilities.

This includes:

- hashing utilities
- small helpers with no domain meaning

If a utility becomes domain-specific, it should move into model/ or service/.

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
