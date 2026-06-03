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
│   └── CodeCollisionError (409)
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

All other subclasses inherit from their nearest base.
A gap test in `tests/util/test_errors.py` enumerates every concrete subclass and
asserts its resolved severity,
so a new error added without a severity decision fails the suite.

## Response builders

`depo.web.error` provides three builders for route handlers:

- `api_error(e: DepoError)`: returns `PlainTextResponse(str(e), status_code=e.status)`
- `htmx_error(e: DepoError, role: str = "alert")`: returns kwargs dict for
  `TemplateResponse` handlers; role used as CSS modifier and ARIA attribute
- `browser_error(req, e: DepoError)`: returns full-page `TemplateResponse`
  using `errors/page.html`; renders debug block for 5xx errors

## Route handler pattern

API handlers catch `DepoError` broadly:

```python
except DepoError as e:
    return api_error(e)
```

HTMX handlers always return 200. Error info lives in the partial body:

```python
except DepoError as e:
    kw |= htmx_error(e)
except Exception as e:
    kw |= htmx_error(UnknownServerError(e))
```

## Logging

The three response builders are the single logging seam.
Each calls a module-level `_log(e)` first,
emitting one record on the `depo` logger at `e.severity` with `e.message`,
attaching `exc_info` when `e.exception` is set.
Routes do not log; building the response logs.

`configure_logging(level)` in `web/app.py` sets the `depo` logger level and
attaches a text handler.
`app_factory` calls it first,
driven by the `log_level` config field (see [cli](../module/cli.md)).
Propagation stays on so test capture and parent handlers still see records.

## Deferred

Browser error templates for the non-404 4xx codes (400, 409, 413, 422)

Remaining error-handling work is tracked in planning:
structured logging observability in `v0.2`,
`StorageError` and `FormatMismatchError` in unplanned.
