# Logging Configuration

## Overview

Depo uses context-aware logging that automatically adjusts verbosity based on
the environment:

- **Tests**: Quiet by default (no noise pollution)
- **Development**: Normal logging to console
- **Production**: Normal logging to console

## Test Logging

### Default Behavior (Quiet)

```bash
python manage.py test
```

Output shows only:

- Test progress dots
- Actual failures with tracebacks
- Final summary
- No upload messages, request logs, or system warnings

### Verbose Test Debugging

```bash
DEPO_VERBOSE_LOGGING=1 python manage.py test
```

Shows all logging including:

- "Upload initiated" / "Upload completed" messages
- "Base-64 image upload detected" messages
- File validation logs
- Django request logging (404, 500, etc.)

## Development/Production Logging

### Normal Operation

```bash
python manage.py runserver
```

Logs all application events at INFO level:

- Upload processing
- File validation results
- Error conditions
- Security events

### Example Log Messages

```text
Upload initiated
Base-64 image upload detected, content length: 118 bytes
Base-64 image validation successful: png, size: 70 bytes
Upload completed: ABC123.png in 0.01seconds
File size 101 exceeds limit of 100 bytes
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DEPO_VERBOSE_LOGGING` | `false` | Force verbose logging in any context |
| `DEPO_TESTING` | auto-detect | Manually override test mode detection |

## Technical Details

- Test mode detected by `'test'` in `sys.argv`
- All `depo.*` loggers follow consistent rules
- Suppresses Django system check warnings during tests
- Uses `NullHandler` for quiet mode, `StreamHandler` for normal mode

