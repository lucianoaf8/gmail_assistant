# Phase 3: Configuration & Exceptions

**Duration**: ~2 hours
**Risk**: Low
**Breaking Changes**: Config file paths
**Depends On**: Phase 2

---

## Objective

Establish the configuration system and exception taxonomy. These must exist BEFORE CLI implementation because CLI imports and uses them.

---

## Instructions

### Task 1: Create Exception Taxonomy (SINGLE SOURCE OF TRUTH)

Create `src/gmail_assistant/core/exceptions.py` with the content from Implementation Plan Section 9.2.

This file defines:
- `GmailAssistantError` - Base exception
- `ConfigError` - Config issues (exit code 5)
- `AuthError` - Auth issues (exit code 3)
- `NetworkError` - Network issues (exit code 4)
- `APIError` - Gmail API issues (exit code 1)

**CRITICAL**: This is the ONLY place exceptions are defined. All other modules MUST import from here.

### Task 2: Create Configuration Loader

Create `src/gmail_assistant/core/config.py` with the content from Implementation Plan Section 9.1.

Key features:
- Resolution order: CLI → env var → project → home → defaults
- Security: Credentials default to `~/.gmail-assistant/`
- Repo-safety check (warns if credentials in git repo)
- Type validation on all fields
- Unknown keys rejected

**IMPORTANT**: ConfigError must be imported from exceptions.py, NOT defined in config.py:

```python
from gmail_assistant.core.exceptions import ConfigError
```

### Task 3: Create Configuration Schema

Create the directory and schema file:

```bash
mkdir -p config/schema
```

Create `config/schema/config.schema.json` with the content from Implementation Plan Section 9.3.

### Task 4: Create Configuration Template

Create `config/default.json.template` with the content from Implementation Plan Section 9.4.

### Task 5: Create Constants File (if needed)

Create `src/gmail_assistant/core/constants.py`:

```python
"""Application constants."""
from __future__ import annotations

# Application metadata
APP_NAME = "gmail-assistant"
APP_VERSION = "2.0.0"

# Default paths
DEFAULT_CONFIG_DIR_NAME = ".gmail-assistant"
DEFAULT_CONFIG_FILE_NAME = "config.json"

# Gmail API
GMAIL_READONLY_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"
GMAIL_MODIFY_SCOPE = "https://www.googleapis.com/auth/gmail.modify"

# Rate limiting
DEFAULT_RATE_LIMIT = 10.0  # requests per second
MAX_RATE_LIMIT = 100.0

# Limits
MAX_EMAILS_LIMIT = 100000
DEFAULT_MAX_EMAILS = 1000
```

### Task 6: Create ADR Documents

Create `docs/adr/` directory and ADR files:

```bash
mkdir -p docs/adr
```

Create the following ADRs (you can use the documentation-generator agent or write directly):

**ADR-0001-package-layout.md** - Decision to use src-layout with Hatchling
**ADR-0002-compatibility.md** - Decision for clean break (no shims)
**ADR-0003-cli-framework.md** - Decision to use Click
**ADR-0004-exception-taxonomy.md** - Decision for single exception hierarchy

Each ADR should follow the format:
```markdown
# ADR-000X: Title

## Status
Accepted

## Context
[Why this decision was needed]

## Decision
[What was decided]

## Consequences
[Positive and negative outcomes]
```

### Task 7: Create ADR Index

Create `docs/adr/README.md`:

```markdown
# Architecture Decision Records

| ADR | Title | Status |
|-----|-------|--------|
| [ADR-0001](ADR-0001-package-layout.md) | Package Layout and Build Backend | Accepted |
| [ADR-0002](ADR-0002-compatibility.md) | Compatibility Strategy (Clean Break) | Accepted |
| [ADR-0003](ADR-0003-cli-framework.md) | CLI Framework (Click) | Accepted |
| [ADR-0004](ADR-0004-exception-taxonomy.md) | Exception Taxonomy (Single Hierarchy) | Accepted |
```

### Task 8: Update Core __init__.py

Update `src/gmail_assistant/core/__init__.py` to export key items:

```python
"""Core functionality for Gmail Assistant."""
from gmail_assistant.core.config import AppConfig
from gmail_assistant.core.exceptions import (
    GmailAssistantError,
    ConfigError,
    AuthError,
    NetworkError,
    APIError,
)

__all__ = [
    "AppConfig",
    "GmailAssistantError",
    "ConfigError",
    "AuthError",
    "NetworkError",
    "APIError",
]
```

### Task 9: Validate

```python
# Test exception imports
python -c "from gmail_assistant.core.exceptions import ConfigError, AuthError, NetworkError; print('Exceptions OK')"

# Test config imports
python -c "from gmail_assistant.core.config import AppConfig; print('Config OK')"

# Verify no duplicate ConfigError
python -c "
from gmail_assistant.core import config, exceptions
assert not hasattr(config, 'ConfigError') or config.ConfigError is exceptions.ConfigError
print('No duplicate ConfigError')
"

# Test config loading
python -c "
from gmail_assistant.core.config import AppConfig
cfg = AppConfig._defaults()
print(f'Default credentials: {cfg.credentials_path}')
print(f'Default token: {cfg.token_path}')
"
```

---

## Definition of Done

- [ ] `from gmail_assistant.core.exceptions import ConfigError, AuthError, NetworkError` works
- [ ] Config loads from: CLI arg → env var → project → home → defaults
- [ ] `docs/adr/` directory exists with ADR-0001 through ADR-0004
- [ ] `docs/adr/README.md` exists with working links
- [ ] `config/schema/config.schema.json` is valid JSON Schema
- [ ] No duplicate ConfigError class (only in exceptions.py)

---

## Commit

After completing all tasks:

```bash
git add -A
git commit -m "phase-3: configuration system and exception taxonomy

Phase 3 of Gmail Assistant restructuring.
- Created centralized exception hierarchy (exceptions.py)
- Implemented secure config loader with resolution order
- Added JSON Schema for configuration validation
- Created ADR documents for key decisions
- ConfigError is single source of truth

BREAKING CHANGE: Config file paths changed, credentials now default to ~/.gmail-assistant/

See: Implementation_Plan_Final_Release_Edition.md Section 6.4

Co-Authored-By: Claude <noreply@anthropic.com>"

git tag migration/phase-3-complete
```

---

## Rollback (if needed)

```powershell
git revert $(git rev-parse migration/phase-3-complete) --no-edit
```
