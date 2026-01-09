# Phase 5: Test Organization

**Duration**: ~2 hours
**Risk**: Low
**Breaking Changes**: None
**Depends On**: Phase 4

---

## Objective

Organize test suite with proper structure, create shared fixtures, and achieve ≥70% coverage gate.

---

## Instructions

### Task 1: Create Test Directory Structure

```bash
mkdir -p tests/unit
mkdir -p tests/unit/test_core
mkdir -p tests/integration
mkdir -p tests/fixtures
```

### Task 2: Create conftest.py with Shared Fixtures

Create `tests/conftest.py`:

```python
"""Shared test fixtures for Gmail Assistant."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_config(temp_dir: Path) -> dict:
    """Return a sample configuration dictionary."""
    return {
        "credentials_path": str(temp_dir / "credentials.json"),
        "token_path": str(temp_dir / "token.json"),
        "output_dir": str(temp_dir / "backups"),
        "max_emails": 100,
        "rate_limit_per_second": 5.0,
        "log_level": "DEBUG",
    }


@pytest.fixture
def config_file(temp_dir: Path, sample_config: dict) -> Path:
    """Create a temporary config file."""
    config_path = temp_dir / "config.json"
    config_path.write_text(json.dumps(sample_config))
    return config_path


@pytest.fixture
def mock_credentials(temp_dir: Path) -> Path:
    """Create mock credentials file."""
    creds_path = temp_dir / "credentials.json"
    creds_path.write_text(json.dumps({
        "installed": {
            "client_id": "test-client-id",
            "client_secret": "test-client-secret",
        }
    }))
    return creds_path
```

### Task 3: Create Test for Exceptions (AGENT RECOMMENDED)

**Use the test-suite-generator agent:**

```
Generate comprehensive unit tests for the exception hierarchy in gmail_assistant.core.exceptions.

The module defines:
- GmailAssistantError (base)
- ConfigError (inherits from base)
- AuthError (inherits from base)
- NetworkError (inherits from base)
- APIError (inherits from base)

Tests should verify:
1. All exceptions can be instantiated with a message
2. All exceptions inherit from GmailAssistantError
3. Exceptions can be caught by their specific type
4. Exceptions can be caught by the base type
5. Exception messages are preserved
6. repr and str work correctly

Save to: tests/unit/test_exceptions.py
```

### Task 4: Create Test for Config (AGENT RECOMMENDED)

**Use the test-suite-generator agent:**

```
Generate comprehensive unit tests for gmail_assistant.core.config.AppConfig.

The config loader has these features:
- Resolution order: CLI → env var → project → home → defaults
- Default directory: ~/.gmail-assistant/
- Path expansion (~ and relative paths)
- Type validation (max_emails must be int, etc.)
- Unknown key rejection
- Security check for credentials in git repos

Tests should verify:
1. Default config creation works
2. Config loads from file correctly
3. Path expansion works (~, relative paths)
4. Type validation raises ConfigError for wrong types
5. Unknown keys raise ConfigError
6. max_emails bounds are enforced (1-100000)
7. rate_limit bounds are enforced (0-100)
8. log_level must be valid level
9. Empty string paths raise ConfigError

Use the fixtures from conftest.py (temp_dir, sample_config, config_file).

Save to: tests/unit/test_config.py
```

### Task 5: Create Test for CLI (AGENT RECOMMENDED)

**Use the test-suite-generator agent:**

```
Generate unit tests for gmail_assistant.cli.main using Click's testing utilities.

The CLI has:
- Main group with --version, --config, --allow-repo-credentials options
- Subcommands: fetch, delete, analyze, auth, config
- Error handler decorator mapping exceptions to exit codes

Tests should verify:
1. --version outputs version string
2. --help shows available commands
3. Each subcommand's --help works
4. fetch command accepts --query, --max-emails, --output-dir, --format options
5. delete command requires --query, accepts --dry-run, --confirm
6. analyze command accepts --input-dir, --report options
7. config --init creates config file
8. config --show displays current config
9. config --validate validates config file

Use Click's CliRunner for testing:
from click.testing import CliRunner
from gmail_assistant.cli.main import main

runner = CliRunner()
result = runner.invoke(main, ['--version'])

Save to: tests/unit/test_cli.py
```

### Task 6: Create Sample Test Fixtures

Create `tests/fixtures/sample_emails.json`:

```json
{
  "emails": [
    {
      "id": "msg-001",
      "subject": "Test Email 1",
      "from": "sender@example.com",
      "date": "2025-01-01T10:00:00Z",
      "body": "This is a test email body."
    },
    {
      "id": "msg-002",
      "subject": "Newsletter: AI Updates",
      "from": "newsletter@ai-news.com",
      "date": "2025-01-02T14:30:00Z",
      "body": "Latest AI news and updates..."
    }
  ]
}
```

### Task 7: Update pyproject.toml Test Configuration

Verify these sections exist in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "-v",
    "--tb=short",
    "--strict-markers",
    "-m", "not integration and not api",
]
markers = [
    "unit: Unit tests (default, run always)",
    "integration: Integration tests (require setup)",
    "api: Tests requiring Gmail API credentials",
    "slow: Tests that take >5 seconds",
]

[tool.coverage.run]
source = ["src/gmail_assistant"]
branch = true

[tool.coverage.report]
fail_under = 70
```

### Task 8: Run Tests

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run with coverage
pytest tests/ -m "not integration and not api" --cov=gmail_assistant --cov-report=term --cov-fail-under=70

# Check markers are registered
pytest --markers | grep -E "(unit|integration|api)"
```

### Task 9: Fix Any Failing Tests

If tests fail, debug and fix them. Common issues:
- Import paths not updated
- Missing fixtures
- Mock setup incorrect

---

## Definition of Done

- [ ] `pytest -m unit` passes
- [ ] `pytest -m integration` runs (may skip without credentials)
- [ ] `pytest --cov` reports ≥70% coverage
- [ ] No `pytest.ini` file (config in pyproject.toml only)
- [ ] `tests/conftest.py` exists with shared fixtures
- [ ] Exception hierarchy tests pass
- [ ] Config loader tests pass
- [ ] CLI tests pass

---

## Commit

After completing all tasks:

```bash
git add -A
git commit -m "phase-5: test organization and coverage gate

Phase 5 of Gmail Assistant restructuring.
- Created test directory structure (unit/integration)
- Added shared fixtures in conftest.py
- Implemented tests for exceptions, config, CLI
- Achieved ≥70% code coverage (required gate)
- Configured pytest markers for test categorization

See: Implementation_Plan_Final_Release_Edition.md Section 6.6

Co-Authored-By: Claude <noreply@anthropic.com>"

git tag migration/phase-5-complete
```

---

## Rollback (if needed)

```powershell
git revert $(git rev-parse migration/phase-5-complete) --no-edit
```
