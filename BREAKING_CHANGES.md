# Breaking Changes in v2.0.0

## Import Paths

All imports have changed from flat structure to package namespace:

```python
# Old (v1.x)
from core.config import Config
from handlers.fetch import FetchHandler

# New (v2.0.0)
from gman.core.config import AppConfig
from gman.cli.commands.fetch import ...
```

## CLI Interface

The CLI has been completely redesigned using Click:

```bash
# Old
python main.py --fetch --query "is:unread"
python src/gman.py --query "is:unread" --max 1000

# New
gman fetch --query "is:unread" --max-emails 1000
gman delete --query "from:spam@example.com" --dry-run
gman analyze --report json
gman auth
gman config --show
```

### New CLI Commands

| Command | Description |
|---------|-------------|
| `gman fetch` | Fetch and backup emails |
| `gman delete` | Delete emails matching query |
| `gman analyze` | Analyze email content |
| `gman auth` | Run OAuth authentication flow |
| `gman config` | Manage configuration |

### Global Options

```bash
gman --version              # Show version
gman --config PATH          # Use custom config file
gman --allow-repo-credentials  # Allow credentials in repo
```

## Configuration

Configuration now defaults to `~/.gman/` for security:

| File | Old Location | New Location |
|------|-------------|--------------|
| Credentials | `./credentials.json` | `~/.gman/credentials.json` |
| Token | `./token.json` | `~/.gman/token.json` |
| Config | `./config.json` | `~/.gman/config.json` |
| Backups | `./gmail_backup/` | `~/.gman/backups/` |

### Using Repo-Local Credentials

If you need credentials in the repository (not recommended), use the flag:

```bash
gman --allow-repo-credentials fetch --query "is:unread"
```

## Entry Points

| Old | New |
|-----|-----|
| `python main.py` | `gman` |
| `python src/gman.py` | `gman fetch` |
| `python -m src.cli.main` | `python -m gman` |

## Exception Hierarchy

A new centralized exception hierarchy has been introduced:

```python
from gman.core.exceptions import (
    GmailAssistantError,  # Base exception
    ConfigError,          # Configuration errors (exit code 5)
    AuthError,            # Authentication errors (exit code 3)
    NetworkError,         # Network errors (exit code 4)
    APIError,             # Gmail API errors (exit code 1)
)
```

## Migration Guide

### Step 1: Update Installation

```bash
# Remove old installation
pip uninstall gman  # if previously installed

# Install new package
pip install -e .
```

### Step 2: Move Credentials

```bash
# Create new config directory
mkdir -p ~/.gman

# Move credentials (recommended)
mv credentials.json ~/.gman/
mv token.json ~/.gman/

# Or use --allow-repo-credentials flag
```

### Step 3: Update Imports

Find and replace in your code:

```python
# Old
from core.config import Config
from core.exceptions import ConfigError

# New
from gman.core.config import AppConfig
from gman.core.exceptions import ConfigError
```

### Step 4: Update Scripts

Replace old CLI calls:

```bash
# Old
python src/gman.py --query "is:unread" --max 1000

# New
gman fetch --query "is:unread" --max-emails 1000
```

### Step 5: Verify Installation

```bash
# Check version
gman --version

# Verify imports work
python -c "from gman.core.config import AppConfig; print('OK')"
```

## Getting Help

- Run `gman --help` for CLI usage
- Run `gman <command> --help` for command-specific help
- Check [README.md](README.md) for full documentation
