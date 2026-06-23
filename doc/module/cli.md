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
    session_secret: str # default: "" (force-fail sentinel; must be set)
    session_https_only: bool # default: False (plain-HTTP LAN deploy)
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
| SESSION_SECRET | "" (force-fail sentinel) |
| SESSION_HTTPS_ONLY | False |

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

`_coerce()` handles int and bool fields and `expanduser` from env/TOML
strings. Bool fields use `_coerce_bool`, which accepts truthy tokens
(`true`, `yes`, `on`, `1`) and falsy tokens (`false`, `no`, `off`, `0`)
case-insensitively, and raises `ConfigError` on unrecognized input.
`session_secret` must be non-empty after resolution or `load_config`
raises `ConfigError`; the `""` default is a deliberate sentinel that
prevents the app booting without an operator-supplied secret.
DB and store paths resolve independently.

## main.py

Click CLI entry point.

### Commands

| Command | Description |
|---------|-------------|
| `depo init` | Create dirs + apply DB schema |
| `depo serve` | Start uvicorn with app factory |
| `depo config show` | Display resolved config fields |
| `depo create-user` | Provision a new user with a hashed password |
| `depo set-password` | Update an existing user's password by email or id |

Config resolved at group level via `ctx.obj`.
`serve` calls `uvicorn.run(app, host, port)`.

## **main**.py

`python -m depo` entry point. Calls `cli()`.
