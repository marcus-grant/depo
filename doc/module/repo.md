# repo/ module

Persistence logic for items.
Depends on model/.
No framework dependencies.

## Errors

Repository errors are defined in `util/errors.py`. Relevant types:

- `NotFoundError`: raised when a fetch by id or email finds no row
- `CodeCollisionError`: raised when insert violates unique code constraint
- `InsertFailedError`: raised when an insert returns no row id (driver fault)
- `UniqueViolationError`: raised when insert violates a unique column constraint

## schema.sql

SQLite schema definition.

```sql
CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY,
    email       TEXT NOT NULL UNIQUE,
    name        TEXT NOT NULL UNIQUE,
    pw_hash     TEXT NOT NULL,
    created_at  INTEGER NOT NULL
);

INSERT OR IGNORE INTO users (id, email, name, pw_hash, created_at)
VALUES (0, 'superuser@localhost', 'Superuser', 'UNSET', 0);

CREATE TABLE IF NOT EXISTS items (
    hash_full   TEXT PRIMARY KEY,
    code        TEXT UNIQUE NOT NULL,
    kind        TEXT NOT NULL,
    size_b      INTEGER NOT NULL,
    uid         INTEGER NOT NULL DEFAULT 0 REFERENCES users(id),
    perm        TEXT NOT NULL DEFAULT 'pub',
    upload_at   INTEGER NOT NULL,
    origin_at   INTEGER
);

CREATE TABLE IF NOT EXISTS text_items (
    hash_full   TEXT PRIMARY KEY REFERENCES items(hash_full) ON DELETE CASCADE,
    format      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS pic_items (
    hash_full   TEXT PRIMARY KEY REFERENCES items(hash_full) ON DELETE CASCADE,
    format      TEXT NOT NULL,
    width       INTEGER NOT NULL,
    height      INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS link_items (
    hash_full   TEXT PRIMARY KEY REFERENCES items(hash_full) ON DELETE CASCADE,
    url         TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_items_uid ON items(uid);
CREATE INDEX IF NOT EXISTS idx_items_kind ON items(kind);
CREATE INDEX IF NOT EXISTS idx_items_upload ON items(upload_at);
```

### Schema notes

- `hash_full` is true identity (content-addressed, immutable)
- `code` is URL identifier (unique, 8-24 chars)
- `users` must be defined before `items` due to the FK on `items.uid`
- `uid` defaults to 0, referencing the seeded superuser row
- Superuser (id=0) is seeded via `INSERT OR IGNORE`; safe to run repeatedly
- Subtype tables share PK with items table (1:1 relationship)
  - There is exactly one of LinkItem, TextItem, PicItem per Item
  - Item is exactly one of its subtypes

## sqlite.py

SQLite implementation of Repository protocol.

### init_db

```python
def init_db(conn: sqlite3.Connection) -> None:
    """
    Apply schema to connection. Idempotent.
    Args:
        conn: SQLite connection to initialize.
    """
    schema = resources.files("depo.repo").joinpath("schema.sql").read_text()
    conn.executescript(schema)
    conn.commit()
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA busy_timeout = 5000")
```

- `foreign_keys`: enables FK enforcement and `ON DELETE CASCADE` behavior
- `journal_mode = WAL`: persistent, stored in the DB file; allows concurrent
  reads and writes from separate processes (required for the `set-password`
  CLI command running alongside the server)
- `synchronous = NORMAL`: per-connection; safe durability tradeoff under WAL
- `busy_timeout = 5000`: per-connection; waits up to 5000ms before raising
  on a locked database instead of failing immediately
- All PRAGMAs are set after `executescript` and `commit` to avoid the
  "safety level may not be changed inside a transaction" error that arises
  when DML in the schema leaves an implicit transaction open

### SqliteRepository

```python
class SqliteRepository:
    def __init__(self, conn: sqlite3.Connection) -> None: ...

    def get_by_code(self, code: str) -> TextItem | PicItem | LinkItem | None:
        """
        Lookup by exact code.
        Assumes input is already canonicalized via canonicalize_code().
        Returns None if not found.
        """
        ...

    def get_by_full_hash(
            self, hash_full: str) -> TextItem | PicItem | LinkItem | None:
        """
        Dedupe lookup by content hash.
        Returns None if not found.
        """
        ...

    def resolve_code(self, hash_full: str, min_len: int) -> str:
        """
        Find shortest unique code prefix.
        Starts at min_len, extends until no collision.
        Returns code string (8-24 chars).
        """
        ...

  def insert(
        self,
        plan: WritePlan,
        *,
        uid: int = 0,
        perm: Visibility = Visibility.PUBLIC,
    ) -> TextItem | PicItem | LinkItem:
        """
        Insert new item and subtype record.
        Resolves code internally from plan.hash_full and plan.code_min_len.
        Raises:
            CodeCollisionError: If resolved code collides (indicates bug).
        """
        ...


  def delete(self, hash_full: str) -> None:
      """Delete item by hash.

      Subtype row cascades automatically via FK constraint.

      Args:
          hash_full: Full hash of item to delete.

      Note:
          No-op if item doesn't exist (idempotent for rollback).
      """
      ...
```

### User CRUD

```python
def insert_user(self, user: User) -> User:
    """
    Insert a new user row and return the persisted User with db-assigned id.
    Raises:
        InsertFailedError: If the database does not return a row id.
        UniqueViolationError: If email or name already exists.
    """
    ...

def get_user(self, uid: int) -> User:
    """
    Fetch a User by id.
    Raises:
        NotFoundError: If no user with that id exists.
    """
    ...

def get_user_by_email(self, email: str) -> User:
    """
    Fetch a User by email.
    Raises:
        NotFoundError: If no user with that email exists.
    """
    ...

def update_user_pw_hash(self, uid: int, pw_hash: str) -> None:
    """
    Update the pw_hash for an existing user.
    Raises:
        NotFoundError: If no user with that id exists.
    """
    ...
```

`_row_to_user(row: sqlite3.Row) -> User` maps a users table row to a
`User` domain object, following the same pattern as `_row_to_text_item`
and siblings.

### Row mappers

```python
def _row_to_text_item(self, row: sqlite3.Row) -> TextItem: ...
def _row_to_pic_item(self, row: sqlite3.Row) -> PicItem: ...
def _row_to_link_item(self, row: sqlite3.Row) -> LinkItem: ...
```

Map DB rows to frozen domain models.

## Design decisions

- **Raw SQL** — no ORM, explicit queries, full control
- **Manual mapping** — row mappers convert to domain models
- **Trusts input** — assumes `code` is canonicalized, `plan` is valid
- **Connection injection** — testable with `:memory:` SQLite
- **Transactional** — insert writes items + subtype in single transaction

## Future Considerations

- Repo refactor:
  query construction/execution layers
- Query builder:
  simple constants vs method chaining
  *(SELECT, FROM, WHERE, IN, LIKE, INSERT INTO, JOIN)*
- Mapper module:
  WritePlan ↔ SQL, rows → Items
- INSERT ON CONFLICT for single-transaction dedupe (PostgreSQL)
- Content/metadata separation:
  sparse content table + per-user item table
- Subtype tables FK to content, not item
