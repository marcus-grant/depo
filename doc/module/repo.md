# repo/ module

Persistence logic for items.
Depends on model/.
No framework dependencies.

## errors.py

Repository-specific exceptions.

### CodeCollisionError

```python
class RepoError(Exception):
    """Base class for repository errors."""

class CodeCollisionError(RepoError):
    """Insert attempted with duplicate code. Indicates application bug."""
    def __init__(self, code: str):
        self.code = code
```

Raised when `insert()` violates the unique code constraint.
This should never happen if `resolve_code()` is correct—existence indicates a bug.

## schema.sql

SQLite schema definition.

```sql
CREATE TABLE items (
    hash_full   TEXT PRIMARY KEY,
    code        TEXT UNIQUE NOT NULL,
    kind        TEXT NOT NULL,
    size_b      INTEGER NOT NULL,
    uid         INTEGER NOT NULL DEFAULT 0,
    perm        TEXT NOT NULL DEFAULT 'pub',
    upload_at   INTEGER NOT NULL,
    origin_at   INTEGER
);

CREATE TABLE text_items (
    hash_full   TEXT PRIMARY KEY REFERENCES items(hash_full),
    format      TEXT NOT NULL
);

CREATE TABLE pic_items (
    hash_full   TEXT PRIMARY KEY REFERENCES items(hash_full),
    format      TEXT NOT NULL,
    width       INTEGER NOT NULL,
    height      INTEGER NOT NULL
);

CREATE TABLE link_items (
    hash_full   TEXT PRIMARY KEY REFERENCES items(hash_full),
    url         TEXT NOT NULL
);

CREATE INDEX idx_items_uid ON items(uid);
CREATE INDEX idx_items_kind ON items(kind);
CREATE INDEX idx_items_upload ON items(upload_at);
```

### Schema notes

- `hash_full` is true identity (content-addressed, immutable)
- `code` is URL identifier (unique, 8-24 chars)
- `uid` has no FK constraint until User table exists
- Subtype tables share PK with items table (1:1 relationship)
  - There is exactly one of LinkItem, TextItem, PicItem per Item
  - Item is exactly one of its subtypes

## sqlite.py

SQLite implementation of Repository protocol.

### init_db

```python
def init_db(conn: sqlite3.Connection) -> None:
    """Apply schema to connection. Idempotent."""
```

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
        code: str,
        *,
        uid: int = 0,
        perm: Visibility = Visibility.PUBLIC,
    ) -> TextItem | PicItem | LinkItem:
        """
        Insert new item and subtype record.
        Code must be pre-resolved via resolve_code().
        
        Raises:
            CodeCollisionError: If code already exists (application bug).
        """
        ...
```

### Row mappers

```python
def _row_to_text_item(self, row: sqlite3.Row) -> TextItem: ...
def _row_to_pic_item(self, row: sqlite3.Row) -> PicItem: ...
def _row_to_link_item(self, row: sqlite3.Row) -> LinkItem: ...
```

Map DB rows to frozen domain models.

### Design decisions

- **Raw SQL** — no ORM, explicit queries, full control
- **Manual mapping** — row mappers convert to domain models
- **Trusts input** — assumes `code` is canonicalized, `plan` is valid
- **Connection injection** — testable with `:memory:` SQLite
- **Transactional** — insert writes items + subtype in single transaction
