# Error handling

Centralized exception hierarchy and response builder patterns for depo.

## Exception hierarchy

All exceptions inherit from `DepoError` which carries three fields:

- `status` — HTTP status code, defaults to class attribute
- `message` — human-readable string, defaults to class attribute
- `ctx` — optional dict of domain-specific context

Domain bases group related exceptions. Subclasses override `status` and
`message` as class attributes and define constructor fields relevant to
their context.

```txt
DepoError (500)
├── RepoError (500)
│   ├── NotFoundError (404)
│   └── CodeCollisionError (409)
├── ValidationError (500)
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

Domain bases carry passthrough constructors so subclasses can call
`super().__init__()` cleanly without skipping the hierarchy.

## Response builders

`depo.web.error` provides three builders for route handlers:

- `api_error(e: DepoError)` — returns `PlainTextResponse(str(e), status_code=e.status)`
- `htmx_error(e: DepoError)` — returns kwargs dict for `TemplateResponse` handlers
- `browser_error(req, e: DepoError)` — returns full-page `TemplateResponse`,
  dispatches to `errors/404.html` or `errors/500.html` by `e.status`

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

## Deferred

- Browser error templates for 400, 409, 413, 422 status codes
- `ExtensionMismatchError` for extensioned URL contract violations
- `FormatMismatchError` when classification endpoint lands
- `StorageError` domain base for filesystem and remote storage backends
- Logging architecture: structured logging, request IDs, severity levels
- Bug report UX for `UnknownClassificationError` and `UnknownServerError`
