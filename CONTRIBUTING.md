# Contributing to Gmail Assistant

Thank you for your interest in contributing to Gmail Assistant. This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Style](#code-style)
- [Testing Guidelines](#testing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Documentation](#documentation)
- [Issue Reporting](#issue-reporting)
- [Project Structure](#project-structure)

---

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Git
- A GitHub account

### Fork and Clone

1. **Fork the repository** on GitHub

2. **Clone your fork locally**
   ```bash
   git clone https://github.com/YOUR_USERNAME/gmail-assistant.git
   cd gmail-assistant
   ```

3. **Add the upstream remote**
   ```bash
   git remote add upstream https://github.com/ORIGINAL_OWNER/gmail-assistant.git
   ```

4. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

---

## Development Setup

### Install Development Dependencies

```bash
# Install package in editable mode with development dependencies
pip install -e ".[dev]"

# Or install with all optional dependencies for full testing
pip install -e ".[all,dev]"
```

### Verify Installation

```bash
# Check CLI works
gmail-assistant --version

# Run linting
ruff check src/ tests/

# Run type checking
mypy src/gmail_assistant

# Run tests
pytest tests/ -v
```

### IDE Configuration

#### VS Code (Recommended)

Create `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.analysis.typeCheckingMode": "basic",
  "python.analysis.extraPaths": ["src"],
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": "explicit"
  },
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.rulers": [100]
  },
  "ruff.lint.args": ["--config=pyproject.toml"],
  "mypy-type-checker.args": ["--config-file=pyproject.toml"]
}
```

Recommended extensions:
- `charliermarsh.ruff` - Ruff linting and formatting
- `ms-python.mypy-type-checker` - MyPy type checking
- `ms-python.python` - Python language support

#### PyCharm

1. Mark `src` as Sources Root
2. Enable type checking (Settings > Editor > Inspections > Python > Type checker)
3. Set line length to 100 (Settings > Editor > Code Style > Python)
4. Configure Ruff as external tool

### Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Linux/macOS)
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"
```

---

## Code Style

### Linting with Ruff

This project uses [Ruff](https://docs.astral.sh/ruff/) for linting and import sorting. Configuration is in `pyproject.toml`.

```bash
# Check for issues
ruff check src/ tests/

# Auto-fix issues
ruff check src/ tests/ --fix

# Check specific file
ruff check src/gmail_assistant/core/config.py
```

#### Ruff Configuration Summary

| Setting | Value |
|---------|-------|
| Line length | 100 |
| Target Python | 3.10 |
| Rules enabled | E, F, W, I, UP, B, SIM, RUF |

#### Key Rules

- **E/W**: pycodestyle errors and warnings
- **F**: Pyflakes
- **I**: isort (import sorting)
- **UP**: pyupgrade (Python version upgrades)
- **B**: flake8-bugbear
- **SIM**: flake8-simplify
- **RUF**: Ruff-specific rules

### Type Checking with MyPy

This project uses strict type checking with [MyPy](https://mypy.readthedocs.io/).

```bash
# Run type checking
mypy src/gmail_assistant

# Check specific module
mypy src/gmail_assistant/core/config.py
```

#### MyPy Configuration Summary

| Setting | Value |
|---------|-------|
| Python version | 3.10 |
| `disallow_untyped_defs` | true |
| `warn_return_any` | true |
| `warn_unused_ignores` | true |

#### Type Annotation Requirements

- All function parameters must have type annotations
- All function return types must be annotated
- Use `from __future__ import annotations` for forward references
- Use `typing.Protocol` for structural interfaces

```python
from __future__ import annotations

from typing import Optional, Dict, Any

def process_email(
    email_id: str,
    options: Optional[Dict[str, Any]] = None
) -> bool:
    """Process an email with given options."""
    ...
```

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Modules | snake_case | `email_parser.py` |
| Classes | PascalCase | `EmailParser` |
| Functions | snake_case | `parse_email()` |
| Constants | UPPER_SNAKE_CASE | `MAX_RETRIES` |
| Private | Leading underscore | `_internal_method()` |
| Type aliases | PascalCase | `EmailData = Dict[str, Any]` |

### Import Organization

Imports are automatically sorted by Ruff with the following order:

1. Standard library imports
2. Third-party imports
3. Local application imports (`gmail_assistant`)

```python
# Standard library
import json
from pathlib import Path
from typing import Optional

# Third-party
import click
from google.oauth2.credentials import Credentials

# Local
from gmail_assistant.core.config import AppConfig
from gmail_assistant.core.exceptions import ConfigError
```

---

## Testing Guidelines

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src/gmail_assistant --cov-report=html

# Run specific test file
pytest tests/unit/test_config.py

# Run specific test function
pytest tests/unit/test_config.py::test_config_loads_defaults
```

### Test Markers

Use pytest markers to categorize tests:

| Marker | Description | When to Use |
|--------|-------------|-------------|
| `@pytest.mark.unit` | Unit tests | No external dependencies |
| `@pytest.mark.integration` | Integration tests | Mocked external services |
| `@pytest.mark.api` | API tests | Requires real Gmail credentials |
| `@pytest.mark.slow` | Slow tests | Tests taking >5 seconds |

```python
import pytest

@pytest.mark.unit
def test_config_validation():
    """Unit test for config validation."""
    ...

@pytest.mark.integration
def test_gmail_api_mock():
    """Integration test with mocked Gmail API."""
    ...

@pytest.mark.api
@pytest.mark.slow
def test_real_gmail_fetch():
    """Test with real Gmail API (slow)."""
    ...
```

### Running Tests by Marker

```bash
# Run only unit tests
pytest tests/ -m unit

# Run integration tests
pytest tests/ -m integration

# Skip slow tests
pytest tests/ -m "not slow"

# Skip API tests (default in CI)
pytest tests/ -m "not api"
```

### Coverage Requirements

- **Minimum coverage**: 70% (enforced by CI)
- **Target coverage**: 90%+

```bash
# Run with coverage and fail if below threshold
pytest tests/ --cov=src/gmail_assistant --cov-fail-under=70

# Generate HTML coverage report
pytest tests/ --cov=src/gmail_assistant --cov-report=html

# View report
open tests/htmlcov/index.html  # macOS
start tests/htmlcov/index.html  # Windows
```

### Writing Tests

#### Test File Location

All test files go in the `tests/` directory:

```
tests/
├── conftest.py          # Shared fixtures
├── fixtures/            # Test data files
├── unit/                # Unit tests
│   ├── test_config.py
│   └── test_validators.py
├── integration/         # Integration tests
│   └── test_gmail_api.py
└── security/            # Security tests
    └── test_pii_redaction.py
```

#### Test Naming

- Test files: `test_*.py`
- Test classes: `Test*`
- Test functions: `test_*`

#### Example Test

```python
"""Tests for configuration loading."""
from __future__ import annotations

import pytest
from pathlib import Path

from gmail_assistant.core.config import AppConfig
from gmail_assistant.core.exceptions import ConfigError


@pytest.mark.unit
class TestAppConfig:
    """Tests for AppConfig class."""

    def test_load_default_config(self, temp_dir: Path) -> None:
        """Test loading default configuration."""
        config = AppConfig.load()
        assert config.max_emails == 1000
        assert config.rate_limit_per_second == 10.0

    def test_load_custom_config(self, config_file: Path) -> None:
        """Test loading custom configuration file."""
        config = AppConfig.load(cli_config=config_file)
        assert config.max_emails == 100

    def test_invalid_config_raises_error(self, temp_dir: Path) -> None:
        """Test that invalid config raises ConfigError."""
        invalid_path = temp_dir / "invalid.json"
        invalid_path.write_text("not valid json")

        with pytest.raises(ConfigError):
            AppConfig.load(cli_config=invalid_path)
```

#### Using Fixtures

Common fixtures are defined in `tests/conftest.py`:

```python
def test_with_fixtures(
    temp_dir: Path,
    sample_config: dict,
    mock_gmail_service,
) -> None:
    """Test using shared fixtures."""
    assert temp_dir.exists()
    assert "credentials_path" in sample_config
    assert mock_gmail_service is not None
```

---

## Pull Request Process

### Branch Naming

Use descriptive branch names with prefixes:

| Prefix | Purpose | Example |
|--------|---------|---------|
| `feature/` | New features | `feature/async-fetching` |
| `fix/` | Bug fixes | `fix/rate-limiter-crash` |
| `docs/` | Documentation | `docs/api-reference` |
| `refactor/` | Code refactoring | `refactor/auth-module` |
| `test/` | Test additions | `test/integration-suite` |

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style (formatting, no logic change)
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

Examples:
```
feat(fetch): add async email fetching support

fix(auth): handle token refresh edge case

docs(api): update authentication guide

refactor(parsers): simplify HTML parsing strategy
```

### Before Submitting

Run the full quality check suite:

```bash
# 1. Update your branch
git fetch upstream
git rebase upstream/main

# 2. Run linting
ruff check src/ tests/

# 3. Run type checking
mypy src/gmail_assistant

# 4. Run tests with coverage
pytest tests/ --cov=src/gmail_assistant --cov-fail-under=70

# 5. Build validation (optional)
pip install build
python -m build
```

### PR Checklist

Before submitting your PR, ensure:

- [ ] Code follows the project style guide (ruff passes)
- [ ] Type annotations are complete (mypy passes)
- [ ] Tests are written for new functionality
- [ ] All tests pass locally
- [ ] Coverage is at least 70%
- [ ] Documentation is updated if needed
- [ ] Commit messages follow conventions
- [ ] Branch is up to date with main

### PR Template

When creating a PR, include:

```markdown
## Summary
Brief description of changes (1-2 sentences)

## Changes
- Bullet point list of specific changes

## Test Plan
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Related Issues
Closes #123
```

### CI Pipeline

Your PR must pass all CI checks:

| Check | Description |
|-------|-------------|
| **Test** | Unit tests on Python 3.10-3.13, Ubuntu and Windows |
| **Lint** | Ruff linting on src/ and tests/ |
| **Type Check** | MyPy type checking |
| **Coverage** | Minimum 70% code coverage |
| **Build** | Package builds and installs correctly |
| **Security** | No credentials tracked, Gitleaks scan |
| **Schema** | Config schema validation |

---

## Documentation

### Documentation Location

All documentation files go in `docs/` with timestamped naming.

### Timestamped Naming Convention

**All documentation files must use timestamped names:**

Format: `<MMDD-HHMM>_<description>.<extension>`

| Correct | Incorrect |
|---------|-----------|
| `0115-1430_api_guide.md` | `api_guide.md` |
| `0115-0900_test_report.json` | `test_report.json` |
| `0115-1600_architecture_notes.txt` | `architecture_notes.txt` |

### Documentation Types

| Type | Location | Purpose |
|------|----------|---------|
| API Reference | `docs/reference/` | Public API documentation |
| Architecture | `docs/` | System design documents |
| ADRs | `docs/adr/` | Architecture Decision Records |
| Testing | `docs/testing/` | Test documentation |
| Guides | `docs/` | User and developer guides |

### Updating Documentation

When making code changes:

1. Update docstrings for modified functions/classes
2. Update relevant documentation files in `docs/`
3. Follow the timestamped naming convention for new files
4. Update `CHANGELOG.md` for user-facing changes

### Docstring Format

Use Google-style docstrings:

```python
def fetch_emails(
    query: str,
    max_results: int = 100,
    format: str = "both",
) -> FetchResult:
    """Fetch emails matching the query.

    Downloads emails from Gmail that match the specified search query
    and saves them in the requested format.

    Args:
        query: Gmail search query string (e.g., "is:unread").
        max_results: Maximum number of emails to fetch. Defaults to 100.
        format: Output format, one of "eml", "markdown", or "both".
            Defaults to "both".

    Returns:
        FetchResult containing the count and paths of downloaded emails.

    Raises:
        AuthError: If authentication fails or token is invalid.
        NetworkError: If Gmail API is unreachable.
        ConfigError: If configuration is invalid.

    Example:
        >>> fetcher = GmailFetcher("credentials.json")
        >>> fetcher.authenticate()
        >>> result = fetcher.fetch_emails("is:unread", max_results=50)
        >>> print(f"Downloaded {result.count} emails")
    """
```

---

## Issue Reporting

### Bug Reports

When reporting bugs, include:

1. **Summary**: Clear, concise description
2. **Environment**: Python version, OS, package version
3. **Steps to reproduce**: Minimal steps to trigger the bug
4. **Expected behavior**: What should happen
5. **Actual behavior**: What actually happens
6. **Error messages**: Full traceback if applicable
7. **Configuration**: Relevant config (redact sensitive data)

Example:
```markdown
## Bug Report

### Summary
Rate limiter crashes when handling concurrent requests

### Environment
- Python: 3.11.5
- OS: Windows 11
- gmail-assistant: 2.0.0

### Steps to Reproduce
1. Configure async fetching with concurrency=10
2. Run fetch with query "is:unread"
3. Wait for ~30 seconds

### Expected Behavior
Emails should be fetched with rate limiting applied

### Actual Behavior
Application crashes with KeyError in rate_limiter.py:45

### Error Message
```
Traceback (most recent call last):
  File "...", line 45, in check_rate
    KeyError: 'last_request_time'
```

### Configuration
```json
{
  "max_emails": 1000,
  "rate_limit_per_second": 10.0
}
```
```

### Feature Requests

When requesting features, include:

1. **Summary**: Brief description of the feature
2. **Motivation**: Why this feature is needed
3. **Proposed solution**: How you envision it working
4. **Alternatives**: Other solutions considered
5. **Additional context**: Screenshots, examples, etc.

---

## Project Structure

### Directory Overview

```
gmail_assistant/
├── src/gmail_assistant/       # Main package (src-layout)
│   ├── cli/                   # Click-based CLI
│   │   ├── main.py            # Entry point
│   │   └── commands/          # Subcommands
│   ├── core/                  # Core business logic
│   │   ├── auth/              # Authentication
│   │   ├── fetch/             # Email fetching
│   │   ├── processing/        # Email processing
│   │   ├── ai/                # AI features
│   │   ├── config.py          # Configuration
│   │   ├── exceptions.py      # Exception hierarchy
│   │   └── protocols.py       # Protocol definitions
│   ├── parsers/               # Format converters
│   ├── analysis/              # Email analysis
│   ├── deletion/              # Email deletion
│   └── utils/                 # Shared utilities
├── tests/                     # Test suite
│   ├── conftest.py            # Shared fixtures
│   ├── unit/                  # Unit tests
│   ├── integration/           # Integration tests
│   └── fixtures/              # Test data
├── docs/                      # Documentation
├── config/                    # Configuration files
├── scripts/                   # Utility scripts
├── examples/                  # Usage examples
├── pyproject.toml             # Package configuration
├── ARCHITECTURE.md            # Architecture documentation
├── CHANGELOG.md               # Version history
└── CONTRIBUTING.md            # This file
```

### Key Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Package config, dependencies, tool settings |
| `CLAUDE.md` | AI assistant instructions and governance |
| `ARCHITECTURE.md` | System architecture documentation |
| `CHANGELOG.md` | Version history and release notes |

### Adding New Modules

1. Create module in appropriate `src/gmail_assistant/` subdirectory
2. Add `__init__.py` exports if needed
3. Update `core/__init__.py` for public API exposure
4. Add corresponding tests in `tests/`
5. Update documentation as needed

---

## Questions?

If you have questions about contributing:

1. Check existing documentation in `docs/`
2. Search existing issues and discussions
3. Open a new issue with your question

Thank you for contributing to Gmail Assistant!
