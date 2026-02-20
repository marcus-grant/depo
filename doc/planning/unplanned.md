# Unplanned Future Features/Architecture

## Future: Repository Architecture

The current SQLite implementation lives in a single module (`repo/sqlite.py`).
As the system grows, consider this structure:

### Query construction abstraction

Two options under consideration:

**Option A — Query constants module:** Simple string constants per dialect.
Minimal complexity, sufficient if query count stays small.

**Option B — Query builder:** Method-chaining builder supporting
SELECT, FROM, WHERE, IN, LIKE, INSERT INTO, JOIN.
Enables dialect switching (SQLite `?` vs PostgreSQL `%s`).
Higher upfront cost, pays off with PostgreSQL migration.

Additionally, a **mapper module** to handle WritePlan → query params
and row results → Item subtypes would centralize (de)serialization
currently spread across SqliteRepository.

### Single-transaction dedupe

Current dedupe uses `get_by_full_hash()` before `insert()` (two transactions).
PostgreSQL supports `INSERT ... ON CONFLICT DO NOTHING RETURNING *` for
single round-trip dedupe. SQLite equivalent is `INSERT OR IGNORE` with
`changes()` check.
Consider when optimizing write path.

### Entity-based split

```txt
repo/
├── __init__.py          # Re-exports public API
├── errors.py            # Shared exceptions
├── schema.sql           # Unified schema (FK relationships)
├── base.py              # init_db(), shared utilities
├── items.py             # ItemRepository (items + subtypes)
├── users.py             # UserRepository (future)
├── tags.py              # TagRepository (future)
```

Each repo owns its tables and row mappers. Connection injected for testability.

### Multi-database support

When adding Postgres support:

```txt
repo/
├── protocol.py          # ItemRepository Protocol (abstract interface)
├── errors.py            # Shared exceptions
├── sqlite/
│   ├── schema.sql
│   ├── items.py         # SqliteItemRepository
│   └── ...
├── postgres/
│   ├── schema.sql
│   ├── items.py         # PostgresItemRepository
│   └── ...
```

**What stays the same:**

- Row mappers (dict → domain model)
- Error types
- Method signatures
- Most queries (named params work in both)

**What differs:**

- Connection handling (sqlite3 vs asyncpg)
- Schema syntax (INTEGER PRIMARY KEY vs SERIAL)
- Async patterns for Postgres

Factory function selects implementation based on config.
Orchestrator depends on Protocol, concrete impl injected at startup.

## Future Considerations (Post–v1.0)

The following features are not required for v1.0,
but the architecture is intentionally designed so
they can be added without violating core guarantees or
requiring a rewrite.

### Ephemeral access and time-limited sharing

- Support temporary access to content via:
  - aliases or access tokens with a TTL
  - optional password or shared secret
- Expiration revokes access, not content identity.
- Intended for quick, low-friction sharing between trusted users.

### Retention policies and automatic purging

- Configurable retention policies based on:
  - last access time
  - visibility (private / unlisted / public)

- Two-phase purge model
  - logical removal (no longer accessible)
  - physical deletion (storage reclaimed after grace period)
  - Purge is opt-in and disabled by default for self-hosters.

### Moderation and administrative deletion

- Moderators and administrators must be able to:
  - Hide or remove abusive or illegal content
  - Permanently delete content when required
    - Deletion may be:
      - Soft (tombstoned)
      - Hard (fully removed)
  - Codes are never reused, even after deletion.

### Storage evolution

- Object store as origin with local filesystem cache (LRU eviction).
- Background garbage collection for unreferenced or purged payloads.
- Storage backend remains replaceable and opaque to higher layers.
- **Content/metadata separation:** Current design couples content identity
  and per-upload metadata in the `items` table. Future split:
  - `content` table: hash_full PK, format, size_b (immutable blob identity)
  - `items`/aliases become metadata pointers to content (uid, perm, tags)
  - Multiple aliases referencing same content achieves storage deduplication
    while preserving per-user metadata
  - This converges with the alias system (§2.1)—aliases *are* the per-user
    metadata layer rather than a separate concept
  - Subtype tables (text_items, pic_items, link_items) would FK to content,
    not items

#### Async DB ramp plan

- MVP: `check_same_thread=False`, synchronous repo, single process
- V1: Define `RepoProtocol` (abstract interface).
  - Keep SQLite sync behind it.
  - Add WAL mode (`PRAGMA journal_mode=WAL`).
  - Consider `aiosqlite` as thin async wrapper.
- V2: PostgreSQL via `asyncpg` implements `RepoProtocol`.
  - True async, connection pooling, concurrent writes.
  - The protocol boundary from V1 makes this a new implementation, not a refactor.

### Metadata and access caching

- In-memory or Redis-backed caching of item and alias metadata.
- Cache is strictly a performance optimization;
  - database remains authoritative.

### Richer text tooling

- Enhanced editors for text and code content.
- Optional features such as:
  - diffs between revisions
  - syntax-aware tooling
  - markdown internal linking and references
- All tooling builds on immutable items and alias-based mutability.

### Authorization expansion

- Optional group-based permissions and moderation roles.
- Invite-based registration remains the default posture.
- Configuration-first approach for self-hosted deployments.

### Advanced content classification

MVP classification uses simple priority:
explicit request > MIME hint > magic bytes > filename extension.

#### Web layer format hints

- Expose `requested_format` as query param on upload endpoint.
  - Decide on interface after browser route handlers are implemented.
- Config option to allow naive image uploads without Pillow verification
  - (safe for small insular groups, potentially dangerous otherwise).
