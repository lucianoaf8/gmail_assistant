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
mkdir -p src/gman/cli/commands
```

### Task 2: Create CLI Main Module

Create `src/gman/cli/main.py` with the complete content from Implementation Plan Section 10.2.

Key features:
- Click group with version option
- Global options: `--config`, `--allow-repo-credentials`
- Error handler decorator mapping exceptions to exit codes
- Subcommands: fetch, delete, analyze, auth, config

### Task 3: Create Subcommand Modules

Create individual subcommand files in `src/gman/cli/commands/`:

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

Create `src/gman/cli/commands/__init__.py`:

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

Create/update `src/gman/cli/__init__.py`:

```python
"""Command Line Interface for Gman."""
from __future__ import annotations

from gman.cli.main import main

__all__ = ["main"]
```

### Task 6: Update Package __main__.py

Verify `src/gman/__main__.py` exists with:

```python
"""Entry point for python -m gman."""
from gman.cli.main import main

if __name__ == "__main__":
    raise SystemExit(main())
```

### Task 7: Update Package __init__.py

Verify `src/gman/__init__.py` has:

```python
"""Gman - Gmail backup, analysis, and management suite."""
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
gman --version

# Help check
gman --help

# Subcommand help checks
gman fetch --help
gman delete --help
gman analyze --help
gman auth --help
gman config --help

# Python module invocation
python -m gman --version
python -m gman --help
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
test_exit('gman --version', 0)
test_exit('gman --help', 0)
test_exit('gman fetch --help', 0)

# Usage errors should exit 2 (Click default)
# test_exit('gman delete', 2)  # missing required --query
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

- [ ] `gman --version` shows version
- [ ] `gman --help` shows all commands
- [ ] `gman fetch --help` shows expected flags
- [ ] `gman delete --help` shows expected flags
- [ ] `gman analyze --help` shows expected flags
- [ ] `gman auth --help` shows expected flags
- [ ] `gman config --help` shows expected flags
- [ ] `python -m gman --version` works
- [ ] All exception types imported from `gman.core.exceptions`

---

## Commit

After completing all tasks:

```bash
git add -A
git commit -m "phase-4: CLI consolidation with Click

Phase 4 of Gman restructuring.
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
