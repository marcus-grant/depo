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
    port: int           # default: 8000
    max_size_bytes: int # default: 10_485_760
    max_url_len: int    # default: 2048
```

Frozen dataclass. Immutable after resolution.

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
