# Gmail Fetcher Implementation-Grade Restructuring Plan

**Document ID**: 0109-1600_implementation_grade_restructuring_plan.md
**Date**: 2026-01-09
**Version**: 2.0 (Addresses review feedback)
**Status**: Implementation-Ready

---

## Table of Contents

1. [Measurement Methodology](#1-measurement-methodology)
2. [Target pyproject.toml Specification](#2-target-pyprojecttoml-specification)
3. [Entry Point Strategy](#3-entry-point-strategy)
4. [Branch & PR Strategy](#4-branch--pr-strategy)
5. [Security Checklist (Phase 0)](#5-security-checklist-phase-0)
6. [Config Loader Contract](#6-config-loader-contract)
7. [CLI Compatibility Contract](#7-cli-compatibility-contract)
8. [Test Organization Policy](#8-test-organization-policy)
9. [Documentation Governance](#9-documentation-governance)
10. [Risk Mitigations](#10-risk-mitigations)
11. [Phase Definitions of Done](#11-phase-definitions-of-done)
12. [Migration Phases](#12-migration-phases)
13. [Compatibility Shim Strategy](#13-compatibility-shim-strategy)

---

## 1. Measurement Methodology

### Baseline Measurements (Run Before Migration)

**PowerShell Commands** (Windows):
```powershell
# Store baseline in docs/audit/0109-baseline.json

# 1. Folder depth measurement
$maxDepth = (Get-ChildItem -Recurse -Directory |
    Where-Object { $_.FullName -notmatch '__pycache__|\.git|node_modules|backups' } |
    ForEach-Object { ($_.FullName -split '\\').Count - ($PWD.Path -split '\\').Count } |
    Measure-Object -Maximum).Maximum
Write-Output "max_folder_depth: $maxDepth"

# 2. sys.path.insert count
$sysPathCount = (Get-ChildItem -Recurse -Filter "*.py" |
    Select-String -Pattern "sys\.path\.insert" -AllMatches |
    Measure-Object).Count
Write-Output "sys_path_inserts: $sysPathCount"

# 3. Config location count
$configLocations = @(
    "config/app",
    "config/analysis",
    "src/analysis"
) | Where-Object { Test-Path $_ } | Measure-Object
Write-Output "config_locations: $($configLocations.Count)"

# 4. Python file count
$pyFiles = (Get-ChildItem -Recurse -Filter "*.py" -Path "src" | Measure-Object).Count
Write-Output "python_source_files: $pyFiles"

# 5. Test file count
$testFiles = (Get-ChildItem -Recurse -Filter "test_*.py" -Path "tests" | Measure-Object).Count
Write-Output "test_files: $testFiles"

# 6. Entry points count
$entryPoints = @("main.py", "src/cli/main.py") | Where-Object { Test-Path $_ } | Measure-Object
Write-Output "entry_points: $($entryPoints.Count)"

# 7. Hidden documentation files
$hiddenDocs = (Get-ChildItem -Recurse -Path "docs/claude-docs" -Filter "*.md" | Measure-Object).Count
Write-Output "hidden_docs: $hiddenDocs"
```

**Bash Commands** (Linux/macOS):
```bash
#!/bin/bash
# Store baseline in docs/audit/0109-baseline.json

echo "=== Baseline Measurements ==="

# 1. Folder depth
max_depth=$(find . -type d ! -path '*/__pycache__/*' ! -path '*/.git/*' ! -path '*/backups/*' | \
    awk -F/ '{print NF-1}' | sort -rn | head -1)
echo "max_folder_depth: $max_depth"

# 2. sys.path.insert count
sys_path_count=$(grep -r "sys\.path\.insert" --include="*.py" | wc -l | tr -d ' ')
echo "sys_path_inserts: $sys_path_count"

# 3. Config locations
config_locs=0
for dir in "config/app" "config/analysis" "src/analysis"; do
    [ -d "$dir" ] && ((config_locs++))
done
echo "config_locations: $config_locs"

# 4. Python source files
py_files=$(find src -name "*.py" | wc -l | tr -d ' ')
echo "python_source_files: $py_files"

# 5. Test files
test_files=$(find tests -name "test_*.py" | wc -l | tr -d ' ')
echo "test_files: $test_files"

# 6. Entry points
entry_points=0
[ -f "main.py" ] && ((entry_points++))
[ -f "src/cli/main.py" ] && ((entry_points++))
echo "entry_points: $entry_points"

# 7. Hidden docs
hidden_docs=$(find docs/claude-docs -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
echo "hidden_docs: $hidden_docs"
```

### Baseline Output Format

Store in `docs/audit/0109-1600_baseline_measurements.json`:
```json
{
  "timestamp": "2026-01-09T16:00:00Z",
  "commit_sha": "<HEAD commit SHA>",
  "measurements": {
    "max_folder_depth": 4,
    "sys_path_inserts": "MEASURED",
    "config_locations": "MEASURED",
    "python_source_files": "MEASURED",
    "test_files": "MEASURED",
    "entry_points": 2,
    "hidden_docs": "MEASURED"
  },
  "notes": "Run before migration starts"
}
```

### Target Metrics (Post-Migration)

| Metric | Baseline (Measured) | Target | How Verified |
|--------|---------------------|--------|--------------|
| max_folder_depth | TBD | ≤3 | Re-run measurement script |
| sys_path_inserts | TBD | 0 | `grep -r "sys\.path\.insert" --include="*.py"` returns empty |
| config_locations | TBD | 1 | Only `config/` exists |
| entry_points | 2 | 1 (console script) | `main.py` removed or marked legacy |
| hidden_docs | TBD | 0 | All user docs in `docs/` root |

**Note**: Percentages like "40% reduction" are **estimates** until baseline measured. Final report will use actual before/after numbers.

---

## 2. Target pyproject.toml Specification

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "gmail-fetcher"
version = "2.0.0"
description = "Gmail backup, analysis, and management suite"
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.9"
authors = [
    {name = "Project Author", email = "author@example.com"}
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Environment :: Console",
    "Intended Audience :: End Users/Desktop",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Communications :: Email",
]

dependencies = [
    "google-api-python-client>=2.140.0",
    "google-auth>=2.27.0",
    "google-auth-oauthlib>=1.2.0",
    "google-auth-httplib2>=0.2.0",
    "html2text>=2024.2.26",
    "tenacity>=8.2.0",
]

[project.optional-dependencies]
analysis = [
    "pandas>=2.1.0",
    "numpy>=1.26.0",
    "pyarrow>=15.0.0",
]
ui = [
    "rich>=13.7.0",
    "tqdm>=4.66.0",
]
advanced-parsing = [
    "beautifulsoup4>=4.12.3",
    "markdownify>=0.13.0",
    "lxml>=5.0.0",
]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.12.0",
    "ruff>=0.4.0",
    "mypy>=1.10.0",
]
all = [
    "gmail-fetcher[analysis,ui,advanced-parsing]",
]

[project.scripts]
gmail-fetcher = "gmail_fetcher.cli.main:main"

[project.urls]
Homepage = "https://github.com/user/gmail-fetcher"
Documentation = "https://github.com/user/gmail-fetcher/docs"
Repository = "https://github.com/user/gmail-fetcher"

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-data]
gmail_fetcher = ["py.typed"]

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
    "integration: Integration tests (require network/external services)",
    "api: Tests requiring Gmail API credentials",
    "slow: Tests that take >5 seconds",
]
filterwarnings = [
    "error",
    "ignore::DeprecationWarning:gmail_fetcher._compat:*",
]

[tool.coverage.run]
source = ["src/gmail_fetcher"]
branch = true
omit = [
    "*/__pycache__/*",
    "*/tests/*",
    "*/_compat.py",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
]

[tool.ruff]
target-version = "py39"
line-length = 100
src = ["src"]

[tool.ruff.lint]
select = ["E", "F", "W", "I", "UP", "B", "SIM"]
ignore = ["E501"]

[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_ignores = true
disallow_untyped_defs = true
packages = ["gmail_fetcher"]
```

### Config Strategy Decision: (A) External Config

Config files remain **outside the package** at project root (`config/`).

**Resolution Order** (highest to lowest priority):
1. `--config` CLI argument
2. `GMAIL_FETCHER_CONFIG` environment variable
3. `./config/default.json` (project root)
4. `~/.gmail-fetcher/config.json` (user home)
5. Hardcoded defaults in `gmail_fetcher.core.constants`

**Implementation**: See [Section 6: Config Loader Contract](#6-config-loader-contract)

---

## 3. Entry Point Strategy

### Decision: Console Script is Canonical

**Canonical entry point**: `gmail-fetcher` (console script)
**Dev parity**: `python -m gmail_fetcher`
**Legacy shim**: `main.py` (deprecated, removal in v2.1.0)

### Deprecation Timeline

| Version | Status |
|---------|--------|
| v2.0.0 | `main.py` emits `DeprecationWarning`, delegates to `gmail_fetcher.cli.main` |
| v2.0.x | Warning severity unchanged |
| v2.1.0 | `main.py` removed from repo |

### Legacy Shim Implementation (`main.py`)

```python
#!/usr/bin/env python3
"""
DEPRECATED: Use `gmail-fetcher` command or `python -m gmail_fetcher` instead.
This shim will be removed in v2.1.0.
"""
import warnings
import sys

warnings.warn(
    "Running via main.py is deprecated. "
    "Use 'gmail-fetcher' command or 'python -m gmail_fetcher' instead. "
    "main.py will be removed in v2.1.0.",
    DeprecationWarning,
    stacklevel=2
)

if __name__ == "__main__":
    from gmail_fetcher.cli.main import main
    sys.exit(main())
```

### `__main__.py` Implementation

```python
# src/gmail_fetcher/__main__.py
"""Entry point for python -m gmail_fetcher."""
from gmail_fetcher.cli.main import main

if __name__ == "__main__":
    raise SystemExit(main())
```

---

## 4. Branch & PR Strategy

### Branch Structure

```
main (protected)
  └── refactor/package-layout (migration branch)
        ├── phase-0-security
        ├── phase-1-critical-fixes
        ├── phase-2-packaging
        ├── phase-3-cli-consolidation
        ├── phase-4-config-docs
        └── phase-5-test-reorg
```

### Workflow

1. **Create migration branch**: `git checkout -b refactor/package-layout`
2. **Phase branches**: Create from migration branch, merge back
3. **Squash merge phases**: Each phase = 1 squash commit to migration branch
4. **Final PR**: `refactor/package-layout` → `main` (regular merge, preserves history)

### Commit Convention

```
<phase>(<scope>): <description>

phase-0(security): remove credentials from git history
phase-1(fix): remove log file, fix doc naming
phase-2(package): convert to installable package
phase-3(cli): consolidate CLI entry points
phase-4(config): flatten config, restructure docs
phase-5(test): organize test structure
```

### Automated Refactor Plan

**Import Rewrite Strategy**:
1. **NOT using**: `lib2to3` (deprecated), manual find-replace (error-prone)
2. **Using**: IDE refactor + validation script

**Validation Script** (`scripts/validate_imports.py`):
```python
#!/usr/bin/env python3
"""Validate all imports resolve correctly."""
import ast
import sys
from pathlib import Path

def check_imports(file_path: Path) -> list[str]:
    """Return list of import errors for a file."""
    errors = []
    try:
        tree = ast.parse(file_path.read_text())
    except SyntaxError as e:
        return [f"{file_path}: SyntaxError: {e}"]

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            # Check for old-style imports
            module = getattr(node, 'module', '') or ''
            for alias in getattr(node, 'names', []):
                name = alias.name
                # Flag old import patterns
                if module.startswith(('src.', 'analysis.', 'deletion.', 'handlers.')):
                    errors.append(f"{file_path}:{node.lineno}: Old import pattern: {module}.{name}")
                if 'sys.path' in file_path.read_text():
                    errors.append(f"{file_path}: Contains sys.path manipulation")
    return errors

def main():
    src_dir = Path("src/gmail_fetcher")
    all_errors = []
    for py_file in src_dir.rglob("*.py"):
        all_errors.extend(check_imports(py_file))

    if all_errors:
        print("Import validation FAILED:")
        for err in all_errors:
            print(f"  {err}")
        sys.exit(1)
    print("Import validation PASSED")
    sys.exit(0)

if __name__ == "__main__":
    main()
```

### CI Integration

Add to `.github/workflows/test.yml` (or equivalent):
```yaml
- name: Validate imports
  run: python scripts/validate_imports.py

- name: Compile check
  run: python -m compileall src/gmail_fetcher -q

- name: Import timing (detect cycles)
  run: python -X importtime -c "import gmail_fetcher" 2>&1 | head -50
```

### Dependency Source of Truth

**Decision**: `pyproject.toml` is source of truth

**requirements.txt Strategy**:
```bash
# Generate from pyproject.toml for legacy compatibility
pip-compile pyproject.toml -o requirements.txt
pip-compile pyproject.toml --extra=dev -o requirements-dev.txt
```

Or document in README:
```markdown
## Installation
pip install -e .           # Core dependencies
pip install -e ".[dev]"    # With dev tools
pip install -e ".[all]"    # All optional features
```

---

## 5. Security Checklist (Phase 0)

### Pre-Migration Security Audit

| Check | Command/Action | Pass Criteria |
|-------|----------------|---------------|
| **Credentials in repo** | `git log --all -p -- '*credentials*' '*token*' '*.env'` | No matches or all in .gitignore |
| **Secrets in code** | `grep -r "AIza\|sk-\|ghp_\|AKIA" --include="*.py"` | No hardcoded API keys |
| **Log files tracked** | `git ls-files '*.log'` | Empty result |
| **OAuth tokens location** | Verify `token.json` path | Outside repo, in gitignore |
| **.env files** | `git ls-files '.env*'` | Empty (use .env.example) |
| **Backup data** | `git ls-files 'backups/*' 'data/*'` | Empty or explicitly allowed |

### Secret Scanning Setup

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.0
    hooks:
      - id: gitleaks

  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
```

### Gitignore Additions

```gitignore
# Credentials (CRITICAL)
credentials.json
token.json
*.pem
*.key
.env
.env.*
!.env.example

# Data (PII risk)
backups/
data/fetched_emails/
*.eml

# Logs
*.log
logs/

# Cache
__pycache__/
*.py[cod]
.pytest_cache/
.mypy_cache/
.ruff_cache/
```

### Data Retention Policy

Document in `docs/security.md`:
- `backups/`: User responsibility, not version-controlled
- `data/`: Transient, cleared on `gmail-fetcher clean`
- `logs/`: Rotated, max 10MB per file, 5 files retained
- **PII in logs**: PROHIBITED - use message IDs only, no subjects/bodies

---

## 6. Config Loader Contract

### Resolution Order

```
Priority 1: --config CLI argument
Priority 2: GMAIL_FETCHER_CONFIG env var
Priority 3: ./config/default.json (project root)
Priority 4: ~/.gmail-fetcher/config.json (user home)
Priority 5: Built-in defaults (gmail_fetcher.core.constants)
```

### Implementation

```python
# src/gmail_fetcher/core/config.py
"""Configuration loader with resolution order and validation."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional
import warnings

@dataclass
class AppConfig:
    """Validated application configuration."""
    credentials_path: Path = field(default_factory=lambda: Path("credentials.json"))
    token_path: Path = field(default_factory=lambda: Path("token.json"))
    output_dir: Path = field(default_factory=lambda: Path("gmail_backup"))
    max_emails: int = 1000
    rate_limit_per_second: float = 8.0
    log_level: str = "INFO"

    @classmethod
    def load(cls, cli_config: Optional[Path] = None) -> "AppConfig":
        """Load config following resolution order."""
        config_path = cls._resolve_config_path(cli_config)

        if config_path and config_path.exists():
            data = json.loads(config_path.read_text())
            return cls._from_dict(data, config_path)

        return cls()  # Built-in defaults

    @classmethod
    def _resolve_config_path(cls, cli_config: Optional[Path]) -> Optional[Path]:
        """Resolve config path by priority."""
        # Priority 1: CLI argument
        if cli_config:
            return cli_config

        # Priority 2: Environment variable
        env_config = os.environ.get("GMAIL_FETCHER_CONFIG")
        if env_config:
            return Path(env_config)

        # Priority 3: Project root
        project_config = Path("config/default.json")
        if project_config.exists():
            return project_config

        # Priority 3b: LEGACY - old paths (emit warning)
        legacy_paths = [
            Path("config/app/gmail_fetcher_config.json"),
            Path("config/app/config.json"),
        ]
        for legacy in legacy_paths:
            if legacy.exists():
                warnings.warn(
                    f"Config at {legacy} is deprecated. "
                    f"Move to config/default.json. "
                    f"Legacy paths will stop working in v2.1.0.",
                    DeprecationWarning,
                    stacklevel=3
                )
                return legacy

        # Priority 4: User home
        user_config = Path.home() / ".gmail-fetcher" / "config.json"
        if user_config.exists():
            return user_config

        return None

    @classmethod
    def _from_dict(cls, data: dict[str, Any], source: Path) -> "AppConfig":
        """Create config from dict with validation."""
        return cls(
            credentials_path=Path(data.get("credentials_path", "credentials.json")),
            token_path=Path(data.get("token_path", "token.json")),
            output_dir=Path(data.get("output_dir", "gmail_backup")),
            max_emails=int(data.get("max_emails", 1000)),
            rate_limit_per_second=float(data.get("rate_limit_per_second", 8.0)),
            log_level=str(data.get("log_level", "INFO")).upper(),
        )
```

### Config Schema (JSON Schema for validation)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Gmail Fetcher Configuration",
  "type": "object",
  "properties": {
    "credentials_path": {"type": "string", "description": "Path to OAuth credentials"},
    "token_path": {"type": "string", "description": "Path to OAuth token cache"},
    "output_dir": {"type": "string", "description": "Default output directory"},
    "max_emails": {"type": "integer", "minimum": 1, "maximum": 10000},
    "rate_limit_per_second": {"type": "number", "minimum": 0.1, "maximum": 100},
    "log_level": {"type": "string", "enum": ["DEBUG", "INFO", "WARNING", "ERROR"]}
  },
  "additionalProperties": false
}
```

---

## 7. CLI Compatibility Contract

### Command Mapping (Old → New)

| Old Invocation | New Invocation | Status |
|----------------|----------------|--------|
| `python main.py fetch ...` | `gmail-fetcher fetch ...` | DEPRECATED v2.0, REMOVED v2.1 |
| `python main.py --query "..."` | `gmail-fetcher fetch --query "..."` | CHANGED (subcommand required) |
| `python main.py analyze ...` | `gmail-fetcher analyze ...` | UNCHANGED |
| `python main.py delete ...` | `gmail-fetcher delete ...` | UNCHANGED |
| `python main.py config ...` | `gmail-fetcher config ...` | UNCHANGED |
| `python -m src.cli.main` | `python -m gmail_fetcher` | CHANGED (package name) |

### Flag Compatibility

| Old Flag | New Flag | Notes |
|----------|----------|-------|
| `--auth-only` | `gmail-fetcher auth` | Now a subcommand |
| `--max` | `--max-emails` | RENAMED for clarity |
| `--output` | `--output-dir` | RENAMED for clarity |
| `--format eml` | `--format eml` | UNCHANGED |
| `--organize date` | `--organize-by date` | RENAMED for clarity |

### Exit Code Convention

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error (runtime) |
| 2 | CLI usage error (bad arguments) |
| 3 | Authentication error |
| 4 | Network/API error |
| 5 | Configuration error |

### Deprecation Warnings

```python
# In CLI argument parsing
def parse_args():
    parser = argparse.ArgumentParser()

    # Deprecated flags with warnings
    parser.add_argument('--max', type=int, dest='max_emails',
                        help=argparse.SUPPRESS)  # Hidden from help
    parser.add_argument('--max-emails', type=int)

    args = parser.parse_args()

    # Emit warning for deprecated flag
    if '--max' in sys.argv:
        warnings.warn(
            "--max is deprecated, use --max-emails instead. "
            "Will be removed in v2.1.0.",
            DeprecationWarning
        )

    return args
```

---

## 8. Test Organization Policy

### Directory Structure

```
tests/
├── conftest.py              # Shared fixtures, pytest plugins
├── pytest.ini               # REMOVED (config in pyproject.toml)
├── __init__.py
│
├── unit/                    # No external dependencies
│   ├── __init__.py
│   ├── test_core/
│   │   ├── test_config.py
│   │   ├── test_protocols.py
│   │   └── test_container.py
│   ├── test_parsers/
│   │   ├── test_eml_parser.py
│   │   └── test_markdown_converter.py
│   └── test_utils/
│       ├── test_validators.py
│       └── test_rate_limiter.py
│
├── integration/             # Require external services (mocked)
│   ├── __init__.py
│   ├── test_gmail_api.py    # Uses VCR cassettes
│   └── test_end_to_end.py
│
├── api/                     # Require real Gmail credentials
│   ├── __init__.py
│   └── test_live_gmail.py   # Only runs locally with credentials
│
└── fixtures/
    ├── emails/              # Sample .eml files
    ├── configs/             # Test config files
    └── cassettes/           # VCR recorded API responses
```

### conftest.py

```python
# tests/conftest.py
"""Shared pytest fixtures and configuration."""
from __future__ import annotations

import json
import pytest
from pathlib import Path
from typing import Any, Generator
from unittest.mock import Mock

# Register markers
def pytest_configure(config):
    config.addinivalue_line("markers", "unit: Unit tests (no external deps)")
    config.addinivalue_line("markers", "integration: Integration tests (mocked external)")
    config.addinivalue_line("markers", "api: Tests requiring real Gmail API credentials")
    config.addinivalue_line("markers", "slow: Tests taking >5 seconds")


@pytest.fixture
def fixtures_dir() -> Path:
    """Path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_email_path(fixtures_dir: Path) -> Path:
    """Path to sample email fixture."""
    return fixtures_dir / "emails" / "sample.eml"


@pytest.fixture
def sample_config(fixtures_dir: Path) -> dict[str, Any]:
    """Sample configuration dict."""
    config_path = fixtures_dir / "configs" / "test_config.json"
    return json.loads(config_path.read_text())


@pytest.fixture
def mock_gmail_service() -> Generator[Mock, None, None]:
    """Mock Gmail API service."""
    mock = Mock()
    mock.users.return_value.messages.return_value.list.return_value.execute.return_value = {
        "messages": [{"id": "msg1"}, {"id": "msg2"}],
        "resultSizeEstimate": 2
    }
    mock.users.return_value.messages.return_value.get.return_value.execute.return_value = {
        "id": "msg1",
        "threadId": "thread1",
        "payload": {
            "headers": [
                {"name": "Subject", "value": "Test Email"},
                {"name": "From", "value": "test@example.com"},
                {"name": "Date", "value": "Mon, 09 Jan 2026 10:00:00 +0000"},
            ],
            "body": {"data": "VGVzdCBib2R5"}  # "Test body"
        }
    }
    yield mock


@pytest.fixture
def clean_env(monkeypatch) -> Generator[None, None, None]:
    """Clean environment without gmail-fetcher variables."""
    monkeypatch.delenv("GMAIL_FETCHER_CONFIG", raising=False)
    yield
```

### Running Tests

**PowerShell**:
```powershell
# Unit tests only (default, fast)
pytest

# All tests including integration (with mocks)
pytest -m "unit or integration"

# Only integration tests
pytest -m integration

# Live API tests (requires credentials)
pytest -m api --credentials=path/to/credentials.json

# With coverage
pytest --cov=gmail_fetcher --cov-report=html
```

**Bash**:
```bash
# Same commands work
pytest
pytest -m "unit or integration"
pytest -m api --credentials=path/to/credentials.json
```

### Secrets Handling for Tests

1. **No credentials in repo**: Use `--credentials` CLI flag or `GMAIL_FETCHER_TEST_CREDENTIALS` env var
2. **CI/CD**: Use GitHub Secrets or equivalent, inject as env var
3. **VCR cassettes**: Pre-recorded API responses for integration tests (scrub tokens before commit)
4. **Local template**: `tests/fixtures/configs/credentials.json.template`

---

## 9. Documentation Governance

### Required Documentation Structure

```
docs/
├── index.md                 # Hub: links to all other docs
├── getting-started.md       # 5-min quickstart
├── installation.md          # Detailed install options
├── configuration.md         # All config options
├── commands.md              # CLI reference
├── troubleshooting.md       # Common issues
├── security.md              # Security practices
├── CHANGELOG.md             # Version history (symlink from root)
│
├── guides/                  # Task-specific guides
│   ├── email-backup.md
│   ├── email-deletion.md
│   └── ai-newsletter-cleanup.md
│
├── adr/                     # Architectural Decision Records
│   ├── 0001-packaging-layout.md
│   ├── 0002-config-resolution.md
│   └── template.md
│
└── internal/                # Claude-generated, timestamped
    └── YYYYMMDD-HHMM_topic.md
```

### ADR Template

```markdown
# ADR-NNNN: Title

**Status**: Proposed | Accepted | Deprecated | Superseded
**Date**: YYYY-MM-DD
**Deciders**: [list]

## Context

What is the issue that we're seeing that is motivating this decision?

## Decision

What is the change that we're proposing?

## Consequences

What becomes easier or harder as a result?

## Alternatives Considered

1. Alternative A: [description] - Rejected because [reason]
2. Alternative B: [description] - Rejected because [reason]
```

### Docs PR Checklist

Add to PR template:
```markdown
## Documentation
- [ ] User-facing changes documented in relevant guide
- [ ] CLI changes reflected in `docs/commands.md`
- [ ] Config changes reflected in `docs/configuration.md`
- [ ] Breaking changes noted in CHANGELOG.md
- [ ] New features have usage examples
```

### Naming Conventions

| Location | Format | Example |
|----------|--------|---------|
| `docs/*.md` | `kebab-case.md` | `getting-started.md` |
| `docs/adr/` | `NNNN-title.md` | `0001-packaging-layout.md` |
| `docs/internal/` | `YYYYMMDD-HHMM_topic.md` | `20260109-1600_migration_notes.md` |

---

## 10. Risk Mitigations

### Targeted Mitigations for Common Refactor Failures

| Risk | Probability | Mitigation |
|------|-------------|------------|
| **Relative path assumptions** | High | Audit all `Path(__file__)` and `os.path.dirname` usages; convert to package-relative |
| **Runtime string imports** | Medium | Grep for `importlib.import_module`, `__import__`; update module paths |
| **Plugin discovery breaks** | Medium | Test plugin registration after each phase; use `importlib.metadata` entry points |
| **Circular imports revealed** | High | Run `python -X importtime` after Phase 2; refactor if cycles detected |
| **pytest sys.path pollution** | High | Run tests from outside repo root in clean venv |
| **Editable install conflicts** | Medium | `pip uninstall gmail-fetcher` before re-installing |
| **Config path resolution** | High | Test config loading from all 5 resolution levels |

### Test-in-Clean-Venv Script

**PowerShell** (`scripts/test_clean_venv.ps1`):
```powershell
# Create fresh venv and run tests
$ErrorActionPreference = "Stop"

$venvPath = ".test-venv"
$repoRoot = $PWD

# Clean up existing
if (Test-Path $venvPath) { Remove-Item -Recurse -Force $venvPath }

# Create venv
python -m venv $venvPath
& "$venvPath\Scripts\Activate.ps1"

# Install package
pip install -e ".[dev]"

# Run tests from DIFFERENT directory (catches sys.path issues)
Set-Location $env:TEMP
pytest "$repoRoot/tests" -v

# Cleanup
Set-Location $repoRoot
deactivate
Remove-Item -Recurse -Force $venvPath
```

**Bash** (`scripts/test_clean_venv.sh`):
```bash
#!/bin/bash
set -e

VENV_PATH=".test-venv"
REPO_ROOT="$PWD"

# Clean up existing
rm -rf "$VENV_PATH"

# Create venv
python -m venv "$VENV_PATH"
source "$VENV_PATH/bin/activate"

# Install package
pip install -e ".[dev]"

# Run tests from DIFFERENT directory
cd /tmp
pytest "$REPO_ROOT/tests" -v

# Cleanup
cd "$REPO_ROOT"
deactivate
rm -rf "$VENV_PATH"
```

### Import Timing Check

```bash
# Run after Phase 2 to detect import cycles/slowness
python -X importtime -c "import gmail_fetcher" 2>&1 | head -50

# If any import takes >100ms, investigate
python -X importtime -c "import gmail_fetcher" 2>&1 | \
    awk '/cumulative/ && $2 > 100000 {print}'
```

---

## 11. Phase Definitions of Done

### Universal DoD (Every Phase)

- [ ] `pip uninstall gmail-fetcher` (if previously installed)
- [ ] `pip install -e .` in clean venv succeeds
- [ ] `python -m gmail_fetcher --help` works
- [ ] `gmail-fetcher --help` works (after console script installed)
- [ ] `python -m compileall src/gmail_fetcher -q` succeeds (no syntax errors)
- [ ] `pytest tests/unit/` green
- [ ] `python scripts/validate_imports.py` passes (no old-style imports)
- [ ] `git status` clean (no untracked changes)
- [ ] Commit message follows convention

### Phase-Specific DoD

**Phase 0 (Security)**:
- [ ] `git log --all -p -- '*credentials*' '*token*'` returns no secrets
- [ ] `.gitignore` updated with security patterns
- [ ] `gitleaks detect` passes (if installed)

**Phase 2 (Packaging)**:
- [ ] `pyproject.toml` validates (`pip install . --dry-run`)
- [ ] No `sys.path.insert` in codebase
- [ ] All imports use `gmail_fetcher.` prefix

**Phase 3 (CLI)**:
- [ ] `gmail-fetcher fetch --help` shows expected flags
- [ ] `gmail-fetcher analyze --help` shows expected flags
- [ ] `gmail-fetcher delete --help` shows expected flags
- [ ] Deprecation warnings emit for old patterns

**Phase 4 (Config/Docs)**:
- [ ] `docs/index.md` exists and all links work
- [ ] Config loads from all 5 resolution levels
- [ ] README.md paths match actual structure

**Phase 5 (Tests)**:
- [ ] `pytest -m unit` passes
- [ ] `pytest -m integration` passes (with mocks)
- [ ] `pytest --cov` reports >70% coverage

---

## 12. Migration Phases (Revised)

### Phase 0: Security Audit (Pre-Migration)
**Time**: 1 hour | **Risk**: Low | **Breaking**: None

| Task | Validation |
|------|------------|
| Run security checklist | All checks pass |
| Update `.gitignore` | Secrets patterns added |
| Remove log file | `git ls-files '*.log'` empty |
| Scan for hardcoded secrets | `grep` patterns return empty |

**DoD**: Phase 0 checklist complete, no secrets in repo

---

### Phase 1: Critical Fixes
**Time**: 1 hour | **Risk**: Low | **Breaking**: None

| Task | Command |
|------|---------|
| Remove log from source | `git rm src/core/email_classifier.log` |
| Fix doc typo | `git mv docs/fulll_project_documentation.md docs/0109-1600_full_project_documentation.md` |
| Move test runner | `git mv tests/docs/run_comprehensive_tests.py tests/` |
| Run baseline measurements | Save to `docs/audit/` |

**DoD**: Universal + baseline measurements saved

---

### Phase 2: Packaging Foundation
**Time**: 4 hours | **Risk**: Medium | **Breaking**: Import paths

| Task | Notes |
|------|-------|
| Create `pyproject.toml` | Use spec from Section 2 |
| Create package namespace | `mkdir -p src/gmail_fetcher` |
| Move source files | `mv src/* src/gmail_fetcher/` (except `__init__.py`) |
| Create `__main__.py` | Entry point for `python -m` |
| Remove `sys.path.insert` | All files |
| Update all imports | Absolute from `gmail_fetcher.` |
| Create compatibility shims | See Section 13 |

**DoD**: Universal + import validation passes

---

### Phase 3: CLI Consolidation
**Time**: 3 hours | **Risk**: Medium | **Breaking**: CLI behavior

| Task | Notes |
|------|-------|
| Create `cli/commands/` | Subcommand modules |
| Move handlers | `src/gmail_fetcher/cli/handlers/` |
| Update main CLI | Single entry point |
| Add deprecation warnings | Old flags/patterns |
| Update `main.py` | Legacy shim with warning |

**DoD**: Universal + CLI compatibility table validated

---

### Phase 4: Config & Docs
**Time**: 2 hours | **Risk**: Low | **Breaking**: Config paths

| Task | Notes |
|------|-------|
| Flatten `config/` | Merge `app/` contents |
| Implement config loader | Resolution order contract |
| Create `docs/index.md` | Documentation hub |
| Restructure docs | Promote from `internal/` |
| Update README | Accurate paths |
| Create ADR-0001 | Document packaging decision |

**DoD**: Universal + config loads from all levels + docs links work

---

### Phase 5: Test Organization
**Time**: 2 hours | **Risk**: Low | **Breaking**: None

| Task | Notes |
|------|-------|
| Create `conftest.py` | Shared fixtures |
| Organize `unit/` | Move unit tests |
| Organize `integration/` | Move integration tests |
| Add VCR cassettes | Recorded API responses |
| Update CI config | pytest paths |

**DoD**: Universal + >70% coverage + all markers work

---

## 13. Compatibility Shim Strategy

### Temporary Re-export Modules

Create thin modules at old import paths that re-export from new locations with deprecation warnings.

**Location**: `src/gmail_fetcher/_compat.py` (centralized warnings)

```python
# src/gmail_fetcher/_compat.py
"""Compatibility utilities for deprecated import paths."""
import warnings
from typing import Any

def deprecated_import(old_path: str, new_path: str, obj: Any) -> Any:
    """Emit deprecation warning for old import path."""
    warnings.warn(
        f"Importing from '{old_path}' is deprecated. "
        f"Use '{new_path}' instead. "
        f"This import path will be removed in v2.1.0.",
        DeprecationWarning,
        stacklevel=3
    )
    return obj
```

### Example Shim (if keeping old paths temporarily)

```python
# src/gmail_fetcher/analysis/__init__.py
"""Analysis module with backward-compatible imports."""
from gmail_fetcher.analysis.engine import EmailAnalysisEngine
from gmail_fetcher.analysis.classifier import EmailClassifier

# Re-export for old import paths (temporary)
# from analysis.email_data_converter import EmailDataConverter  # OLD
# Now handled by proper package structure
```

### Shim Removal Timeline

| Version | Action |
|---------|--------|
| v2.0.0 | Shims active, emit `DeprecationWarning` |
| v2.0.x | Warnings remain, no changes |
| v2.1.0 | Shims removed, old paths break with `ImportError` |

### CI Warning Detection

Add to CI to catch deprecation usage:
```yaml
- name: Check for deprecation warnings
  run: |
    python -W error::DeprecationWarning -c "import gmail_fetcher" || \
      echo "Warning: DeprecationWarnings present (expected during migration)"
```

---

## Summary: Gap Remediation Status

| Gap | Section | Status |
|-----|---------|--------|
| 1. Claims without evidence | §1 Measurement Methodology | ✅ Addressed |
| 2. Packaging incomplete | §2 pyproject.toml Spec | ✅ Addressed |
| 3. Entry point ambiguity | §3 Entry Point Strategy | ✅ Addressed |
| 4. Missing repo mechanics | §4 Branch & PR Strategy | ✅ Addressed |
| 5. Tests underspecified | §8 Test Organization Policy | ✅ Addressed |
| 6. Security narrow | §5 Security Checklist | ✅ Addressed |
| 7. Config breaking change | §6 Config Loader Contract | ✅ Addressed |
| 8. CLI compatibility | §7 CLI Compatibility Contract | ✅ Addressed |
| 9. Docs governance | §9 Documentation Governance | ✅ Addressed |
| 10. Risks generic | §10 Risk Mitigations | ✅ Addressed |

### Specific Improvements Status

| Improvement | Section | Status |
|-------------|---------|--------|
| A. Definition of Done per phase | §11 | ✅ Addressed |
| B. Target pyproject.toml | §2 | ✅ Addressed |
| C. Compatibility shim strategy | §13 | ✅ Addressed |
| D. Cross-platform commands | §1, throughout | ✅ Addressed |

---

**Document Version**: 2.0
**Status**: Implementation-Ready
**Next Action**: Run baseline measurements (§1), then begin Phase 0
