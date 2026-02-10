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

SQLite uses `check_same_thread=False` for async handler compatibility.

## routes.py

Thin route definitions. Maps URLs to handler functions.

### Routes

| Method | Path | Handler | Description |
|--------|------|---------|-------------|
| POST | `/api/upload` | `upload()` | Canonical upload endpoint |
| POST | `/upload` | `upload()` | Shortcut alias |
| POST | `/` | `upload()` | Shortcut alias |
| GET | `/api/{code}/raw` | `get_raw()` | Raw content with correct MIME |
| GET | `/api/{code}/info` | `get_info()` | Key=value metadata |
| GET | `/health` | `health()` | Liveness probe |

Upload handler delegates to `execute_upload()` in upload.py.
Read handlers use `selector.get_item()` and `selector.get_raw()`.
LinkItem raw requests return 307 redirect.

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

UploadParams = UploadMultipartParams | UploadUrlParams | UploadRawBodyParams
```

Algebraic union — each variant corresponds to an upload path.

### upload.py - functions

```python
async def parse_upload(file, url, request) -> UploadParams
```

Extracts orchestrator kwargs from HTTP request. Branches:

- `file` present → `UploadMultipartParams`
- `url` present → `UploadUrlParams`
- Raw body detected as URL → `UploadUrlParams`
- Raw body otherwise → `UploadRawBodyParams`

```python
def upload_response(result: PersistResult) -> PlainTextResponse
```

Builds response with short code body and
`X-Depo-Code`, `X-Depo-Kind`, `X-Depo-Created` headers.
201 for new, 200 for dedupe.

```python
async def execute_upload(file, url, request, orchestrator) -> PlainTextResponse
```

Glue: parse → ingest → respond. Catches `ValueError` → 400.

### Helper

```python
_looks_like_url(data: bytes) -> bool
```

Naive URL detection via regex. TODO: Move to ingestion pipeline.

## deps.py

FastAPI dependency providers via `Depends()`.

### deps.py - functions

```python
get_repo(request) -> SqliteRepository
get_storage(request) -> StorageBackend
get_orchestrator(request) -> IngestOrchestrator
```

Thin getters pulling from `request.app.state`.
