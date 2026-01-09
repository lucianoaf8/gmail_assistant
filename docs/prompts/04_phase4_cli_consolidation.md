# Phase 4: CLI Consolidation

**Duration**: ~3 hours
**Risk**: Medium
**Breaking Changes**: CLI interface
**Depends On**: Phase 3 (config and exceptions must exist)

---

## Objective

Implement the Click-based CLI with all subcommands. Commands are argument-parsing skeletons with TODO placeholders - functional behavior is deferred to v2.1.0.

---

## Instructions

### Task 1: Create Commands Directory

```bash
mkdir -p src/gmail_assistant/cli/commands
```

### Task 2: Create CLI Main Module

Create `src/gmail_assistant/cli/main.py` with the complete content from Implementation Plan Section 10.2.

Key features:
- Click group with version option
- Global options: `--config`, `--allow-repo-credentials`
- Error handler decorator mapping exceptions to exit codes
- Subcommands: fetch, delete, analyze, auth, config

### Task 3: Create Subcommand Modules

Create individual subcommand files in `src/gmail_assistant/cli/commands/`:

**fetch.py:**
```python
"""Fetch command implementation."""
from __future__ import annotations

# NOTE: Functional implementation deferred to v2.1.0
# This module will contain the actual fetch logic
```

**delete.py:**
```python
"""Delete command implementation."""
from __future__ import annotations

# NOTE: Functional implementation deferred to v2.1.0
# This module will contain the actual delete logic
```

**analyze.py:**
```python
"""Analyze command implementation."""
from __future__ import annotations

# NOTE: Functional implementation deferred to v2.1.0
# This module will contain the actual analysis logic
```

**auth.py:**
```python
"""Auth command implementation."""
from __future__ import annotations

# NOTE: Functional implementation deferred to v2.1.0
# This module will contain the OAuth flow
```

**config_cmd.py:**
```python
"""Config command implementation."""
from __future__ import annotations

# NOTE: Functional implementation deferred to v2.1.0
# Additional config management features go here
```

### Task 4: Update Commands __init__.py

Create `src/gmail_assistant/cli/commands/__init__.py`:

```python
"""CLI subcommand modules."""
from __future__ import annotations

__all__ = [
    "fetch",
    "delete",
    "analyze",
    "auth",
    "config_cmd",
]
```

### Task 5: Update CLI __init__.py

Create/update `src/gmail_assistant/cli/__init__.py`:

```python
"""Command Line Interface for Gmail Assistant."""
from __future__ import annotations

from gmail_assistant.cli.main import main

__all__ = ["main"]
```

### Task 6: Update Package __main__.py

Verify `src/gmail_assistant/__main__.py` exists with:

```python
"""Entry point for python -m gmail_assistant."""
from gmail_assistant.cli.main import main

if __name__ == "__main__":
    raise SystemExit(main())
```

### Task 7: Update Package __init__.py

Verify `src/gmail_assistant/__init__.py` has:

```python
"""Gmail Assistant - Gmail backup, analysis, and management suite."""
__version__ = "2.0.0"
__all__ = ["__version__"]
```

### Task 8: Reinstall Package

```bash
pip install -e .
```

### Task 9: Validate CLI

```bash
# Version check
gmail-assistant --version

# Help check
gmail-assistant --help

# Subcommand help checks
gmail-assistant fetch --help
gmail-assistant delete --help
gmail-assistant analyze --help
gmail-assistant auth --help
gmail-assistant config --help

# Python module invocation
python -m gmail_assistant --version
python -m gmail_assistant --help
```

### Task 10: Validate Exit Codes

```python
# Test exit codes (in Python)
python -c "
import subprocess
import sys

def test_exit(cmd, expected):
    result = subprocess.run(cmd, capture_output=True, shell=True)
    actual = result.returncode
    status = '✓' if actual == expected else '✗'
    print(f'{status} {cmd}: exit {actual} (expected {expected})')
    return actual == expected

# These should succeed (exit 0)
test_exit('gmail-assistant --version', 0)
test_exit('gmail-assistant --help', 0)
test_exit('gmail-assistant fetch --help', 0)

# Usage errors should exit 2 (Click default)
# test_exit('gmail-assistant delete', 2)  # missing required --query
"
```

---

## Exit Code Reference

| Code | Meaning | Exception |
|------|---------|-----------|
| 0 | Success | None |
| 1 | General error | GmailAssistantError, Exception |
| 2 | Usage/argument error | Click default |
| 3 | Authentication error | AuthError |
| 4 | Network error | NetworkError |
| 5 | Configuration error | ConfigError |

---

## Definition of Done

- [ ] `gmail-assistant --version` shows version
- [ ] `gmail-assistant --help` shows all commands
- [ ] `gmail-assistant fetch --help` shows expected flags
- [ ] `gmail-assistant delete --help` shows expected flags
- [ ] `gmail-assistant analyze --help` shows expected flags
- [ ] `gmail-assistant auth --help` shows expected flags
- [ ] `gmail-assistant config --help` shows expected flags
- [ ] `python -m gmail_assistant --version` works
- [ ] All exception types imported from `gmail_assistant.core.exceptions`

---

## Commit

After completing all tasks:

```bash
git add -A
git commit -m "phase-4: CLI consolidation with Click

Phase 4 of Gmail Assistant restructuring.
- Implemented Click-based CLI with subcommands
- Added fetch, delete, analyze, auth, config commands
- Implemented error handler with exit code mapping
- Commands are argument-parsing skeletons (functional in v2.1.0)
- All exceptions imported from core.exceptions

BREAKING CHANGE: CLI interface completely redesigned with Click

See: Implementation_Plan_Final_Release_Edition.md Section 6.5

Co-Authored-By: Claude <noreply@anthropic.com>"

git tag migration/phase-4-complete
```

---

## Rollback (if needed)

```powershell
git revert $(git rev-parse migration/phase-4-complete) --no-edit
pip install -e .
```
