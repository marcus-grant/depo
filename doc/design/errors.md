# Error handling

Centralized exception hierarchy and response builder patterns for depo.

## Exception hierarchy

All exceptions inherit from `DepoError` which carries:

- `status`: HTTP status code, defaults to class attribute
- `message`: human-readable string, defaults to class attribute
- `ctx`: optional dict of domain-specific context
- `severity`: logging severity, a `Severity` level, defaults per class
- `exception`: optional wrapped exception, `None` by default

Domain bases group related exceptions. Subclasses override `status` and
`message` as class attributes and define constructor fields relevant to
their context.

```txt
DepoError (500)
├── RepoError (500)
│   ├── NotFoundError (404)
│   │   ├── ExtensionMismatchError (404)
│   │   └── LinkRawNotSupportedError (404)
│   ├── CodeCollisionError (409)
│   ├── InsertFailedError (500)
│   └── UniqueViolationError (500)
├── ValidationError (400)
│   ├── PayloadTooLargeError (413)
│   ├── PayloadEmptyError (400)
│   └── PayloadSourceError (400)
├── ClassificationError (422)
│   ├── ImageDecodeError (422)
│   ├── UnsupportedFormatError (422)
│   └── UnknownClassificationError (500)
└── ServerError (500)
    └── MissingDependencyError (501)
```

Domain bases carry pass-through constructors so subclasses can call
`super().__init__()` cleanly without skipping the hierarchy.

## Severity

Each error carries a `severity` from `Severity`,
an `IntEnum` in `util/errors.py` mirroring stdlib logging levels
(DEBUG 10 through CRITICAL 50).
It is a class attribute resolved by inheritance,
with explicit decisions at a few nodes:

- `DepoError` defaults to ERROR
- `RepoError` and `MissingDependencyError` are WARNING
- `NotFoundError`, `ValidationError`, `ClassificationError` are INFO
- `UnknownClassificationError` is ERROR
- `InsertFailedError` is ERROR (driver-level fault, not a domain condition)
- `UniqueViolationError` is WARNING (expected user-facing condition)

All other subclasses inherit from their nearest base.
A gap test in `tests/util/test_errors.py` enumerates every concrete subclass and
asserts its resolved severity,
so a new error added without a severity decision fails the suite.

## Response builders

`depo.web.error` provides three builders.
Each returns a finished `Response`,
so route handlers and the boundary pick a builder rather than
assemble responses themselves:

- `api_error(e: DepoError)`: returns `PlainTextResponse(str(e), status_code=e.status)`
- `htmx_error(req, e: DepoError, role: str = "alert")`: returns the
  `errors/partial.html` `TemplateResponse` hardcoded at `status_code=200`,
  the HTMX contract. `role` is used as CSS modifier and ARIA attribute
- `browser_error(req, e: DepoError)`: returns full-page `TemplateResponse`
  using `errors/page.html` at `e.status`; renders debug block for 5xx errors

## Route handler pattern

API handlers catch `DepoError` broadly and return a builder:

```python
except DepoError as e:
    return api_error(e)
```

HTMX handlers always return 200, with error info in the partial body:

```python
except DepoError as e:
    return htmx_error(request, e)
```

Routes catch only `DepoError`.
Non-`DepoError` exceptions are left to escape to the app-level boundary,
which removes the need for per-route bare `except Exception` guards.

## Unexpected-error boundary

`unhandled(request, exc)` in `depo.web.error` is registered on the app via
`add_exception_handler(Exception, unhandled)` in `app_factory`.
It catches any non-DepoError that escapes a route,
wraps it in `UnknownServerError`, negotiates surface
(`is_htmx` to `htmx_error`, `wants_html` to `browser_error`, otherwise `api_error`),
and delegates.
It does not log: the builder it delegates to is the logging seam.

## Logging

The three response builders are the single logging seam.
Each calls `log_error(e)` first, emitting one record at `e.severity` with `e.message`,
attaching `exc_info` when `e.exception` is set.
The helper logs on `getLogger(__name__)`,
a child of the `depo` logger, so there is no stored module logger to keep in sync.
Routes do not log; building the response logs.
The boundary handler does not log, since it delegates to a builder.
`configure_logging(level)` in `web/app.py` sets the `depo` logger level and
attaches a text handler. `app_factory` calls it first,
driven by the `log_level` config field (see [cli](../module/cli.md)).
Propagation stays on so test capture and parent handlers still see records.

## Deferred

Remaining error-handling work is tracked in planning: structured logging
observability in `v0.2`, `StorageError` and `FormatMismatchError` in
unplanned. `FormatMismatchError` is unrelated to unsupported-token coercion
(landed in `fix/form-error-surface`); it concerns declared-vs-inferred
format conflicts post-classification.
