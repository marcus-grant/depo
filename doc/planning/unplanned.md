# Unplanned Future Features/Architecture

## P1: Important or Well Considered Priorities

### Preflight error domain

Introduce a `PreflightError(DepoError)` base class for startup-time
failures that occur before the server serves any request: invalid
config, DB missing or corrupt, unreachable file store. Reparent
`ConfigError` under it. Refine `ConfigError`'s signature with a
free-form `reason`/`hint` field for problems that are not a bad value
against a known set (malformed int, unreadable TOML), and thread
config-source provenance so messages can name the origin (env var,
TOML path, flag). post-MVP.

### Narrow per-consumer config slices

`app_factory` currently unpacks `DepoConfig` fields explicitly when
constructing inner-layer components (e.g. `IngestService`). If
per-component arg lists grow painful, introduce narrow frozen
dataclasses or Protocols carrying only the fields each component
needs, adapted from `DepoConfig` at the composition root. Do not
inject `DepoConfig` directly into inner layers; that violates the
inward-only dependency rule. post-MVP.

### Adopt humanread for formatting

Introduce `humanread` as an external dependency for human-readable output.
Time formatting needed near MVP (item timestamps, created_at).
Size formatting needed soon after (item sizes, upload limit display).
Blocks on the library existing. Consumed at the presentation edge only.
Should support adapted functions passed as jinja filters

## P2: Needs Better Scoping

### Pre-classification endpoint for guesses

- Evaluate lightweight client-side pre-classification:
  - URL reachability checks (config toggle — not always desirable,
    cookie/auth concerns on API side)
  - Base64 content detection
  - Possible URL pattern matching
- Before moving on, also consider this for a potential fold into PR or separate:
  - Post-MVP MIME mapping for LINK format (deferred — `text/uri-list`
    supports multiple URLs, needs design thought)
  - Auto-classification preview

### Async DB ramp plan

>**NOTE**: Consider this item before the next repo architecture plan.
>Very likely this could be a good ladder or a hint to one towards a better repo layer.

- MVP: `check_same_thread=False`, synchronous repo, single process
- V1: Define `RepoProtocol` (abstract interface).
  - Keep SQLite sync behind it.
  - Add WAL mode (`PRAGMA journal_mode=WAL`).
  - Consider `aiosqlite` as thin async wrapper.
- V2: PostgreSQL via `asyncpg` implements `RepoProtocol`.
  - True async, connection pooling, concurrent writes.
  - The protocol boundary from V1 makes this a new implementation, not a refactor.

### Repository Architecture

The current SQLite implementation lives in a single module (`repo/sqlite.py`).
As the system grows, consider this structure:

#### Query construction abstraction

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

#### Single-transaction dedupe

Current dedupe uses `get_by_full_hash()` before `insert()` (two transactions).
PostgreSQL supports `INSERT ... ON CONFLICT DO NOTHING RETURNING *` for
single round-trip dedupe. SQLite equivalent is `INSERT OR IGNORE` with
`changes()` check.
Consider when optimizing write path.

#### Entity-based split

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

#### Multi-database support

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

Functions requiring changes when backend abstraction lands:
`init_db`, `_row_to_text_item`, `_row_to_pic_item`, `_row_to_link_item`,
`_row_to_user`, `SqliteRepository.insert`, `get_by_code`, `get_by_full_hash`,
`resolve_code`, `delete`, `insert_user`, `get_user`, `get_user_by_email`,
`update_user_pw_hash`. Also: `web/app.py` and `cli/main.py` repo construction
sites, and `tests/fixtures/__init__.py` fixture wiring.

#### Caching as a design constraint

The repository interface should not preclude a metadata cache. An in-memory
or Redis-backed cache of item and alias metadata is a possible future
optimization, strictly a performance layer with the database remaining
authoritative. Design `RepoProtocol` so a caching implementation can wrap or
compose with it: clear read paths, explicit invalidation points on write, and
query shapes that are cacheable by key rather than arbitrary.

Not scheduled. Recorded so the interface work does not paint it out.

### Authorization enforcement boundary

Authentication is enforced only at the web perimeter. `require_auth` gates the
route; the inner layers take a `uid` as data and trust that someone upstream
checked. With a single entry path to ingest, the perimeter is the whole surface,
so this is currently sound.

It stops being sound when there is more than one path inward: a CLI command, a
job runner, a new route added without the gate. An inner layer that trusts an
unstated upstream check is a confused deputy.

The fix, when permissions land, is not to push session-awareness inward, which
would violate the inward-only dependency rule. It is to have the service layer
enforce authorization on the data it is given: uid, role, requested visibility.
The inner layer then makes its own decision rather than trusting a caller.

May never be worth doing. If depo is ever deployed per-organization on isolated
subdomains rather than as a shared multi-tenant service, cross-tenant leakage is
structurally impossible and the perimeter is genuinely enough. Recorded so the
choice is deliberate rather than an unexamined gap.

### Advanced content classification

- MVP classification uses simple priority:
  explicit request > MIME hint > magic bytes > filename extension.
- Expose `requested_format` as query param on upload endpoint.
  - Decide on interface after browser route handlers are implemented.
- Config option to allow naive image uploads without Pillow verification
  - (safe for small insular groups, potentially dangerous otherwise).

## P3 Explorations and Decisions to be Made

### Template Testing Refactor

- Evaluate separating template tests into dedicated test module
  - Currently inline in route test modules
  - Focus on logic coverage, not appearance

### Retention policies and automatic purging

- Configurable retention policies based on:
  - last access time
  - visibility (private / unlisted / public)

- Two-phase purge model
  - logical removal (no longer accessible)
  - physical deletion (storage reclaimed after grace period)
  - Purge is opt-in and disabled by default for self-hosters.

### Visual and presentation layer

- /render endpoint: clean presentation view for payload content;
  minimal UI; optimized for reading; resolves tension between
  record inspection (/info) and content viewing (/raw stays literal)
- Success state redesign: move from full-width banner to calm inline
  state near reference; success hue on text/border only
- Focus indication primitive: consistent grayscale-first focus style
  globally across all interactive elements
- Spacing token cleanup: single vertical rhythm scale; audit all
  padding/margin values

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

## P4: Post-v1.0

### Misc. Features

- Per-user response format preferences (towards v1 multi-user)

### Ephemeral access and time-limited sharing

- Support temporary access to content via:
  - aliases or access tokens with a TTL
  - optional password or shared secret
- Expiration revokes access, not content identity.
- Intended for quick, low-friction sharing between trusted users.

### Moderation and administrative deletion

- Moderators and administrators must be able to:
  - Hide or remove abusive or illegal content
  - Permanently delete content when required
    - Deletion may be:
      - Soft (tombstoned)
      - Hard (fully removed)
  - Codes are never reused, even after deletion.

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

#### Metadata and access caching

- In-memory or Redis-backed caching of item and alias metadata.
- Cache is strictly a performance optimization;
  - database remains authoritative.
