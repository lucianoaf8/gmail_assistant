# Breaking Changes in v2.0.0

## Import Paths

All imports have changed from flat structure to package namespace:

```python
# Old (v1.x)
from core.config import Config
from handlers.fetch import FetchHandler

# New (v2.0.0)
from gmail_assistant.core.config import AppConfig
from gmail_assistant.cli.commands.fetch import ...
```

## CLI Interface

The CLI has been completely redesigned using Click:

```bash
# Old
python main.py --fetch --query "is:unread"
python src/gmail_assistant.py --query "is:unread" --max 1000

# New
gmail-assistant fetch --query "is:unread" --max-emails 1000
gmail-assistant delete --query "from:spam@example.com" --dry-run
gmail-assistant analyze --report json
gmail-assistant auth
gmail-assistant config --show
```

### New CLI Commands

| Command | Description |
|---------|-------------|
| `gmail-assistant fetch` | Fetch and backup emails |
| `gmail-assistant delete` | Delete emails matching query |
| `gmail-assistant analyze` | Analyze email content |
| `gmail-assistant auth` | Run OAuth authentication flow |
| `gmail-assistant config` | Manage configuration |

### Global Options

```bash
gmail-assistant --version              # Show version
gmail-assistant --config PATH          # Use custom config file
gmail-assistant --allow-repo-credentials  # Allow credentials in repo
```

## Configuration

Configuration now defaults to `~/.gmail-assistant/` for security:

| File | Old Location | New Location |
|------|-------------|--------------|
| Credentials | `./credentials.json` | `~/.gmail-assistant/credentials.json` |
| Token | `./token.json` | `~/.gmail-assistant/token.json` |
| Config | `./config.json` | `~/.gmail-assistant/config.json` |
| Backups | `./gmail_backup/` | `~/.gmail-assistant/backups/` |

### Using Repo-Local Credentials

If you need credentials in the repository (not recommended), use the flag:

```bash
gmail-assistant --allow-repo-credentials fetch --query "is:unread"
```

## Entry Points

| Old | New |
|-----|-----|
| `python main.py` | `gmail-assistant` |
| `python src/gmail_assistant.py` | `gmail-assistant fetch` |
| `python -m src.cli.main` | `python -m gmail_assistant` |

## Exception Hierarchy

A new centralized exception hierarchy has been introduced:

```python
from gmail_assistant.core.exceptions import (
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
pip uninstall gmail-fetcher  # if previously installed

# Install new package
pip install -e .
```

### Step 2: Move Credentials

```bash
# Create new config directory
mkdir -p ~/.gmail-assistant

# Move credentials (recommended)
mv credentials.json ~/.gmail-assistant/
mv token.json ~/.gmail-assistant/

# Or use --allow-repo-credentials flag
```

### Step 3: Update Imports

Find and replace in your code:

```python
# Old
from core.config import Config
from core.exceptions import ConfigError

# New
from gmail_assistant.core.config import AppConfig
from gmail_assistant.core.exceptions import ConfigError
```

### Step 4: Update Scripts

Replace old CLI calls:

```bash
# Old
python src/gmail_assistant.py --query "is:unread" --max 1000

# New
gmail-assistant fetch --query "is:unread" --max-emails 1000
```

### Step 5: Verify Installation

```bash
# Check version
gmail-assistant --version

# Verify imports work
python -c "from gmail_assistant.core.config import AppConfig; print('OK')"
```

## Getting Help

- Run `gmail-assistant --help` for CLI usage
- Run `gmail-assistant <command> --help` for command-specific help
- Check [README.md](README.md) for full documentation
