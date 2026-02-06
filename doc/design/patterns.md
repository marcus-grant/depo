# Design Patterns

Recurring patterns and learnings from depo development.

## Data-Driven Classification

Complex classification behavior built from simple data structures.

### Pattern: Enum as Source of Truth

```python
class ContentFormat(StrEnum):
    PLAINTEXT = "txt"
    PNG = "png"
    # ...
```

The enum value *is* the canonical extension.
MIME types, kinds, and variants derive from it.

### Pattern: Declarative Mappings

```python
_FORMAT_TO_MIME: dict[ContentFormat, str] = {
    ContentFormat.PLAINTEXT: "text/plain",
    ContentFormat.PNG: "image/png",
}
```

Thin lookup functions over declarative dicts.
Adding a format means adding data, not logic.

### Pattern: Accept Variants, Output Canonical (Postel's Law)

```python
# Outbound: always canonical
def mime_for_format(fmt: ContentFormat) -> str:
    return _FORMAT_TO_MIME[fmt]

# Inbound: accept variants
_MIME_TO_FORMAT["application/x-yaml"] = ContentFormat.YAML
_EXT_TO_FORMAT["jpeg"] = ContentFormat.JPEG
```

### Pattern: Strategy Chain with `or`

```python
result = (
    _from_requested_format(requested_format)
    or _from_declared_mime(declared_mime)
    or _from_magic_bytes(data)
    or _from_filename(filename)
)
```

Each strategy returns `ContentClassification | None`.
Priority is explicit in order.
Orchestrator stays thin.

### Pattern: Isolated Detectors

```python
_MAGIC_DETECTORS = [_detect_png_magic, _detect_jpeg_magic, _detect_webp_magic]

def _from_magic_bytes(data: bytes) -> ContentClassification | None:
    for detector in _MAGIC_DETECTORS:
        fmt = detector(data)
        if fmt is not None:
            return ContentClassification(kind_for_format(fmt), fmt)
    return None
```

Each detector handles one format's variants.
Adding format = add detector + append to list.

## Service Layer Patterns

### Pattern: Services Write, Selectors Read

Inspired by HackSoft's Django Styleguide services/selectors pattern,
adapted for FastAPI with explicit dependency passing.

**Services** coordinate write operations (ingest, delete):

```python
class IngestOrchestrator:
    def __init__(self, ingest_service, repo, storage): ...
    def ingest(self, ...) -> PersistResult: ...
```

**Selectors** coordinate read operations as module-level functions:

```python
def get_item(repo, code: str) -> TextItem | PicItem | LinkItem: ...
def get_raw(repo, storage, code: str) -> tuple[BinaryIO | None, Item]: ...
```

Key differences from Django Styleguide:

- Selectors take repo/storage as explicit parameters (no Django ORM globals)
- No class needed for selectors — read coordination is simple
- Naming is `selector.py` not `selectors.py` (matches depo's singular convention)

The web layer talks exclusively to services/selectors.
Routes never touch repo or storage directly.

## Coordination Patterns

### Pattern: Orchestrator Coordinates Siblings

```python
class IngestOrchestrator:
    def __init__(self, ingest_service, repo, storage):
        self._ingest = ingest_service
        self._repo = repo
        self._storage = storage

    def ingest(self, ...) -> PersistResult:
        plan = self._ingest.build_plan(...)
        existing = self._repo.get_by_full_hash(plan.hash_full)
        if existing:
            return PersistResult(existing, created=False)

        try:
            item = self._repo.insert(plan, ...)
        except:
            self._repo.delete(code=item.code, ...)
            raise
        self._storage.put(code=code, ...)
        return PersistResult(item, created=True)
```

Repo and storage are siblings, not nested. Orchestrator owns:

- Ordering (storage before DB)
- Rollback on failure
- Dedupe decision

Components stay simple and independently testable.

### Pattern: DTOs as Boundary Contracts

```python
@dataclass(frozen=True)
class WritePlan:
    hash_full: str
    kind: ItemKind
    ...

@dataclass(frozen=True)
class PersistResult:
    item: TextItem | PicItem | LinkItem
    created: bool
```

DTOs at layer boundaries enable:

- Serialization for future decoupling (microservices, queues)
- Clear contracts between components
- No framework bleed (no ORM objects, no request objects)
- Testability without mocks

If orchestrator becomes a separate service,
interface stays identical—only transport changes.

### Pattern: Conditional Skip for Item Kinds

```python
if plan.kind != ItemKind.LINK:
    self._storage.put(...)
```

Some item kinds (LinkItem) have no payload.
Simple conditional in orchestrator until multiple kinds need special handling,
then refactor to strategy pattern.

YAGNI: don't abstract until the second case emerges.

## Configuration Patterns

### Pattern: Layered Config Resolution

```python
def load_config(*, config_path: Path | None = None) -> DepoConfig:
    """Resolution: defaults → XDG → local → env → config_path"""
```

Each layer overrides the previous. Supports both containerized deployments
(project-local `./depo.toml`) and traditional installs (XDG config path).

- **Defaults** are hardcoded in a frozen dataclass
- **Files** parsed via `tomllib` (stdlib, zero dependencies)
- **Env vars** use `DEPO_` prefix with type coercion
- **CLI flag** (`--config`) replaces file discovery entirely

The config dataclass is the single source of truth for dependency wiring:

```txt
CLI loads DepoConfig → app_factory(config) → FastAPI app
```

### Pattern: Frozen Config as Dependency Root

```python
@dataclass(frozen=True)
class DepoConfig:
    db_path: Path
    storage_root: Path
    host: str
    port: int
    max_size_bytes: int
    max_url_len: int
```

Frozen dataclass ensures config is immutable after resolution.
All downstream components receive config values, never mutate them.
App factory consumes config to wire all dependencies.

## Schema Patterns

### Pattern: Derived Fields at Read Time

```python
# DB stores
hash_full = "ABCD1234XXXXXXXXXXXXXXXX"
code = "ABCD1234"
```

Store canonical data. Derive redundant fields when mapping to domain model.
Avoids update anomalies (3NF) and keeps storage minimal.

### Pattern: Defaults for Future Features

```python
def insert(
    self,
    plan: WritePlan,
    code: str,
    *,
    uid: int = 0,
    perm: Visibility = Visibility.PUBLIC,
) -> Item:
```

Parameters with defaults for features not yet implemented (auth, permissions).
Interface is stable—when feature lands, callers start passing real values.
No signature change, no migration.

## Test Patterns

### Pattern: Centralized Fixtures with `t_` Prefix

```python
# tests/fixtures/__init__.py

@pytest.fixture
def t_conn() -> Generator[sqlite3.Connection, None, None]:
    """Raw in-memory SQLite connection (no schema)."""
    c = sqlite3.connect(":memory:")
    yield c
    c.close()

@pytest.fixture
def t_db() -> Generator[sqlite3.Connection, None, None]:
    """In-memory SQLite repository with schema."""
    c = sqlite3.connect(":memory:")
    init_db(c)
    yield c
    c.close()

@pytest.fixture
def t_repo(t_db) -> SqliteRepository:
    """SqliteRepository instance using in-memory DB."""
    return SqliteRepository(t_db)

@pytest.fixture
def t_store(tmp_path) -> FilesystemStorage:
    """FilesystemStorage instance with temporary root."""
    return FilesystemStorage(root=tmp_path / "depo-test-store")

@pytest.fixture
def t_orch_env(
    t_repo, t_store
) -> tuple[IngestOrchestrator, SqliteRepository, FilesystemStorage]:
    service = IngestService()
    orch = IngestOrchestrator(service, t_repo, t_store)
    return (orch, t_repo, t_store)
```

Fixtures compose upward: `t_conn` → `t_db` → `t_repo` → `t_orch_env`.
Each layer adds one concern (schema, repository wrapper, orchestrator wiring).

Key conventions:

- `t_` prefix distinguishes first-party from pytest/third-party fixtures
- `t_orch_env` returns a tuple so tests can access repo/storage for assertions
- `t_store` uses `tmp_path` for automatic cleanup
- `t_conn` exists for raw schema/SQL tests that don't need the full repo
- Registered via `conftest.py` `pytest_plugins` for project-wide availability

### Pattern: Central Test Specs

```python
_FORMAT_SPECS = [
    (ContentFormat.PLAINTEXT, "text/plain", "txt", ItemKind.TEXT),
    (ContentFormat.PNG, "image/png", "png", ItemKind.PICTURE),
]

_FMT_MIME = [(f, m) for f, m, _, _ in _FORMAT_SPECS]
_FMT_EXT = [(f, e) for f, _, e, _ in _FORMAT_SPECS]
```

One tuple defines all relationships.
Derived lists feed parametrized tests.
Adding format = one row.

### Pattern: Gap Detection Tests

```python
def test_all_formats_have_mime(self):
    for fmt in ContentFormat:
        result = mime_for_format(fmt)
        assert isinstance(result, str)
```

Loops over enum catch missing implementations.
Fails when someone adds a format but forgets the mapping.

### Pattern: Test Helper for Repeated Assertions

```python
def _assert_content_class(result, expected_format, msg_prefix=""):
    assert isinstance(result, ContentClassification)
    assert result.format == expected_format
    assert result.kind == kind_for_format(expected_format)
```

Centralizes multi-field assertions. Reduces boilerplate, improves error messages.

## Principles

- **Data structures are the spec**
  - Mappings define behavior, functions just navigate them.
- **Exhaustive tests over examples**
  - Loop over enums, not cherry-picked cases.
- **Fail at boundaries**
  - Validate input at edges (web layer), trust types internally.
- **Thin orchestrators**
  - Complex behavior emerges from composing simple parts.
- **Services write, selectors read**
  - Clear separation between mutation and query paths.
