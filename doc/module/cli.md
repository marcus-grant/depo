# cli/ module

Command-line interface and configuration. Depends on model/, web/.

## config.py

Configuration resolution and data model.

### DepoConfig

```python
@dataclass(frozen=True, kw_only=True)
class DepoConfig:
    db_path: Path
    store_root: Path
    host: str           # default: "127.0.0.1"
    port: int           # default: 8765
    min_code_len: int   # default: 8
    max_size_bytes: int # default: 2**26 (64 MiB)
    max_url_len: int    # default: 2048
    log_level: Severity # default: Severity.WARNING
    scrypt_n: int       # default: 2**16
    scrypt_r: int       # default: 8
    scrypt_p: int       # default: 1
```

Frozen dataclass. Immutable after resolution.

## defaults.py

Default value production for DepoConfig, separate from config.py's
resolution logic.

### Constants

| Name | Default |
|------|---------|
| HOST | "127.0.0.1" |
| PORT | 8765 |
| MIN_CODE_LEN | 8 |
| MAX_SIZE_BYTES | 2**26 (64 MiB) |
| MAX_URL_LEN | 2048 |
| LOG_LEVEL | Severity.WARNING |
| SCRYPT_N | 2**16 |
| SCRYPT_R | 8 |
| SCRYPT_P | 1 |

### Functions

```python
default_store_dir() -> Path
default_db_path() -> Path
```

Resolve under `XDG_DATA_HOME/depo` when set,
else cwd-relative for containerized deploys.

### Function

```python
load_config(*, config_path: Path | None = None) -> DepoConfig
```

**Resolution order:**
defaults → XDG config.toml → ./depo.toml → DEPO_* env → --config flag.

Each layer overrides the previous.
`_coerce()` handles int fields and `expanduser` from env/TOML strings.
DB and store paths resolve independently.

## main.py

Click CLI entry point.

### Commands

| Command | Description |
|---------|-------------|
| `depo init` | Create dirs + apply DB schema |
| `depo serve` | Start uvicorn with app factory |
| `depo config show` | Display resolved config fields |

Config resolved at group level via `ctx.obj`.
`serve` calls `uvicorn.run(app, host, port)`.

## **main**.py

`python -m depo` entry point. Calls `cli()`.
