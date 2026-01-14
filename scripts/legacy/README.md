# Legacy Scripts

This directory contains deprecated entry points preserved for reference.

## Files

### main_v1.py (DEPRECATED)
- **Status**: Deprecated as of v2.0.0
- **Reason**: Contains `sys.path.insert` manipulation, replaced by proper packaging
- **Migration**: Use `gman` CLI or `python -m gman` instead

## Migration Guide

| Old Command | New Command |
|-------------|-------------|
| `python main.py fetch --query "..."` | `gman fetch --query "..."` |
| `python main.py analyze --yesterday` | `gman analyze --yesterday` |
| `python main.py delete unread` | `gman delete --query "is:unread"` |

## Why Deprecated?

The v2.0.0 restructure:
1. Eliminates `sys.path` manipulation for proper package imports
2. Uses Click-based CLI with better UX
3. Supports `pip install` for proper dependency management
4. Enables `python -m gman` invocation

See [BREAKING_CHANGES.md](../../BREAKING_CHANGES.md) for full migration details.
