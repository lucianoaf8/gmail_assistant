# Gmail Fetcher Architecture Restructuring - Final Implementation Plan

**Document ID**: 0109-2300_final_implementation_plan_consolidated.md
**Date**: 2026-01-09
**Version**: Final (consolidated from v1-v7)
**Release Version**: 2.0.0
**Status**: Implementation-Ready

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Version Alignment](#2-version-alignment)
3. [Current State Analysis](#3-current-state-analysis)
4. [Critical Decisions](#4-critical-decisions)
5. [Proposed Structure](#5-proposed-structure)
6. [Technical Specifications](#6-technical-specifications)
7. [Migration Phases](#7-migration-phases)
8. [Validation & Testing](#8-validation--testing)
9. [CI/CD Configuration](#9-cicd-configuration)
10. [Security](#10-security)
11. [Breaking Changes](#11-breaking-changes)
12. [Architectural Decision Records](#12-architectural-decision-records)
13. [Implementation Checklist](#13-implementation-checklist)
14. [Success Metrics](#14-success-metrics)
15. [Risk Mitigation](#15-risk-mitigation)

---

## 1. Executive Summary

### 1.1 Current State Overview

| Metric | Value | Assessment |
|--------|-------|------------|
| Max Directory Depth | 4 levels | Acceptable |
| Python Source Files | 78 | Moderate complexity |
| Test Files | 26 | Good coverage ratio |
| Overall Score | 7.5/10 | Good with improvements needed |

### 1.2 Key Problems Identified

| Problem | Priority | Resolution |
|---------|----------|------------|
| `sys.path.insert` everywhere | **Critical** | Remove all, use proper packaging |
| Import path inconsistencies | **Critical** | Absolute imports from `gmail_fetcher` |
| Dual CLI entry points | **High** | Single `gmail-fetcher` console script |
| Configuration scattered | **High** | Centralized config loader |
| README paths outdated | **High** | Update documentation |
| Missing `pyproject.toml` | **High** | Modern Hatchling-based packaging |
| Documentation hidden | **High** | Promote to docs/ root |
| Log file in source code | **Critical** | Move to logs/, gitignore |

### 1.3 Expected Benefits

- **Zero `sys.path` manipulation** after migration
- **Single source of truth** for CLI, config, and docs
- **10-15 minute** new developer onboarding (vs. 30-45 min current)
- **Standard Python packaging** enabling `pip install -e .`
- **Clean import paths** (`from gmail_fetcher.x import y`)
- **Cross-platform CI/CD** with Windows-first development

### 1.4 Platform Contract

This project is **Windows-first** with cross-platform CI support:
- Primary development environment: Windows
- CI runs on: Ubuntu + Windows (GitHub Actions)
- PowerShell scripts work under `pwsh` on both platforms
- Dev prerequisite for non-Windows contributors: PowerShell Core (`pwsh`)

---

## 2. Version Alignment

| Artifact | Version | Notes |
|----------|---------|-------|
| This document | Final (v7-based) | Consolidated from all revisions |
| Release | **2.0.0** | Major bump for breaking changes |
| `pyproject.toml` | `version = "2.0.0"` | Single source of truth |
| `gmail_fetcher/__init__.py` | `__version__ = "2.0.0"` | Fallback for editable installs |
| CHANGELOG.md | `## [2.0.0]` | Document all changes |
| BREAKING_CHANGES.md | References v2.0.0 | Migration guide |
| Classifier | `Development Status :: 4 - Beta` | Appropriate for major restructure |

---

## 3. Current State Analysis

### 3.1 Folder Hierarchy (Pre-Migration)

```
gmail_fetcher/                      # ROOT
├── main.py                         # Entry point 1 (465 lines)
├── requirements.txt
├── CLAUDE.md / README.md
│
├── src/                            # SOURCE CODE
│   ├── cli/                        # Entry point 2
│   │   └── main.py
│   ├── handlers/                   # Duplicates CLI logic
│   ├── core/
│   │   ├── fetch/
│   │   ├── auth/
│   │   ├── processing/
│   │   └── ai/
│   ├── parsers/
│   ├── plugins/
│   ├── analysis/
│   ├── deletion/
│   ├── tools/
│   └── utils/
│
├── tests/                          # TESTS
│   ├── docs/
│   │   └── run_comprehensive_tests.py  # Misplaced
│   └── test_*.py                   # Flat structure
│
├── config/                         # CONFIGURATION
│   ├── app/                        # Nested
│   ├── analysis/                   # Duplicates src/analysis/config
│   └── security/
│
├── scripts/                        # SCRIPTS
│   ├── analysis/
│   ├── backup/
│   ├── setup/
│   └── *.py                        # Loose scripts
│
├── docs/                           # DOCUMENTATION
│   ├── fulll_project_documentation.md  # Typo + no timestamp
│   └── claude-docs/                # All docs hidden here
│
└── src/core/email_classifier.log   # Log in source!
```

### 3.2 Complexity Metrics

| Category | Current | Target | Improvement |
|----------|---------|--------|-------------|
| Max folder depth | 4 | 3 | -25% |
| Entry points | 2 | 2 (cli + __main__) | Consolidated |
| Config locations | 3+ | 1 | -67% |
| `sys.path` manipulations | 15+ | 0 | -100% |
| Hidden documentation | 27 files | 0 | -100% |

---

## 4. Critical Decisions (Locked)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Compatibility strategy** | **Clean break** (no shims) | Shims add complexity, testing burden, and delay cleanup. Bump to v2.0.0 with documented breaking changes. |
| **CLI framework** | **Click** | Better UX than argparse, widespread, good subcommand support, explicit over implicit. |
| **Config default location** | **User home** (`~/.gmail-fetcher/`) | Security-first; repo-local requires explicit opt-in. |
| **Build backend** | **Hatchling** | Modern, fast, better defaults than setuptools for src-layout. |
| **Python version** | **>=3.10** | Realistic minimum for 2026, enables `|` union types, match statements. |
| **Scripting language** | **PowerShell only** | Windows-first project, `pwsh` is cross-platform for CI. |

---

## 5. Proposed Structure

### 5.1 Post-Migration Layout

```
gmail_fetcher/
│
├── main.py                         # REMOVED (or legacy shim with deprecation)
├── pyproject.toml                  # Modern Hatchling packaging
├── README.md
├── CLAUDE.md
├── CHANGELOG.md
├── BREAKING_CHANGES.md
│
├── src/
│   └── gmail_fetcher/              # Installable package namespace
│       ├── __init__.py             # __version__ = "2.0.0"
│       ├── __main__.py             # python -m gmail_fetcher
│       ├── py.typed                # Type hints marker
│       │
│       ├── cli/                    # CONSOLIDATED CLI
│       │   ├── __init__.py
│       │   ├── main.py             # Click-based entry point
│       │   └── handlers/           # MOVED from src/handlers/
│       │
│       ├── core/                   # Core functionality
│       │   ├── __init__.py
│       │   ├── config.py           # Centralized config loader
│       │   ├── protocols.py
│       │   ├── container.py
│       │   ├── constants.py
│       │   ├── exceptions.py
│       │   ├── auth/
│       │   ├── fetch/
│       │   └── processing/
│       │
│       ├── plugins/
│       ├── parsers/
│       ├── analysis/
│       ├── deletion/
│       └── utils/
│
├── tests/
│   ├── conftest.py                 # Shared fixtures
│   ├── __init__.py
│   ├── unit/
│   │   ├── test_core/
│   │   ├── test_parsers/
│   │   └── test_utils/
│   ├── integration/
│   │   ├── test_gmail_api.py
│   │   └── test_end_to_end.py
│   └── fixtures/
│
├── config/                         # FLATTENED
│   ├── default.json
│   ├── analysis.json
│   └── templates/
│       └── credentials.json.template
│
├── scripts/
│   ├── audit/
│   │   └── baseline.ps1            # PowerShell only
│   ├── migration/
│   │   └── move_to_package.ps1
│   └── validation/
│       ├── check_import_policy.py
│       └── release_checks.ps1
│
├── docs/
│   ├── index.md
│   ├── getting-started.md
│   ├── configuration.md
│   ├── commands.md
│   ├── security.md
│   ├── adr/
│   │   ├── 0001-package-layout.md
│   │   ├── 0002-compatibility-strategy.md
│   │   └── 0003-cli-framework.md
│   └── internal/
│       └── [timestamped files]
│
├── logs/                           # gitignored
├── data/
├── backups/
└── examples/
```

### 5.2 Navigation Paths Improvement

| Action | Before | After | Improvement |
|--------|--------|-------|-------------|
| Find CLI entry | 2 options, confusing | 1 clear path | -50% |
| Find config | 3 locations to check | 1 location | -67% |
| Find user docs | Navigate claude-docs/ | docs/index.md | -80% |
| Run tests | Scattered, no fixtures | `pytest` works | -70% effort |
| Install package | Manual sys.path | `pip install -e .` | Standard |

---

## 6. Technical Specifications

### 6.1 pyproject.toml

```toml
[build-system]
requires = ["hatchling>=1.21.0"]
build-backend = "hatchling.build"

[project]
name = "gmail-fetcher"
version = "2.0.0"
description = "Gmail backup, analysis, and management suite"
readme = "README.md"
license = "MIT"
requires-python = ">=3.10"
authors = [
    {name = "Project Author", email = "author@example.com"}
]
keywords = ["gmail", "email", "backup", "google-api"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Environment :: Console",
    "Intended Audience :: End Users/Desktop",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Communications :: Email",
    "Typing :: Typed",
]

dependencies = [
    "click>=8.1.0",
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
    "responses>=0.25.0",
    "ruff>=0.4.0",
    "mypy>=1.10.0",
    "build>=1.0.0",
]

[project.scripts]
gmail-fetcher = "gmail_fetcher.cli.main:main"

[project.urls]
Homepage = "https://github.com/user/gmail-fetcher"
Documentation = "https://github.com/user/gmail-fetcher#readme"
Repository = "https://github.com/user/gmail-fetcher"
Changelog = "https://github.com/user/gmail-fetcher/blob/main/CHANGELOG.md"

# Hatchling src-layout configuration
[tool.hatch.build.targets.wheel]
packages = ["src/gmail_fetcher"]

[tool.hatch.build.targets.sdist]
include = [
    "src/gmail_fetcher/**/*.py",
    "src/gmail_fetcher/py.typed",
    "README.md",
    "CHANGELOG.md",
    "LICENSE",
]

[tool.hatch.build.targets.wheel.force-include]
"src/gmail_fetcher/py.typed" = "gmail_fetcher/py.typed"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = ["-v", "--tb=short", "--strict-markers"]
markers = [
    "unit: Unit tests (no external deps)",
    "integration: Integration tests (mocked external services)",
    "api: Tests requiring real Gmail API credentials",
    "slow: Tests taking >5 seconds",
]
filterwarnings = [
    "error",
    "ignore::DeprecationWarning:google.*:",
]

[tool.coverage.run]
source = ["src/gmail_fetcher"]
branch = true
omit = ["*/__pycache__/*", "*/tests/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
    "@overload",
]
fail_under = 70

[tool.ruff]
target-version = "py310"
line-length = 100
src = ["src"]

[tool.ruff.lint]
select = ["E", "F", "W", "I", "UP", "B", "SIM", "RUF"]
ignore = ["E501"]

[tool.ruff.lint.isort]
known-first-party = ["gmail_fetcher"]

[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_ignores = true
disallow_untyped_defs = true
mypy_path = "src"
packages = ["gmail_fetcher"]

[[tool.mypy.overrides]]
module = [
    "google.*",
    "googleapiclient.*",
    "html2text",
    "tenacity",
]
ignore_missing_imports = true
```

### 6.2 Configuration Loader

The configuration loader follows a strict resolution order:

1. `--config` CLI argument
2. `GMAIL_FETCHER_CONFIG` environment variable
3. `~/.gmail-fetcher/config.json` (user home)
4. Built-in defaults (all paths in `~/.gmail-fetcher/`)

Key features:
- Paths resolve relative to config file location (not CWD)
- Security checks against credentials in git repos
- Strict schema validation (fails on unknown keys)
- Type validation before Path() construction
- Cross-drive path safety on Windows

### 6.3 CLI Structure

```
gmail-fetcher
├── fetch      # Download emails
├── delete     # Delete emails
├── analyze    # Analyze email data
├── auth       # Authenticate with Gmail
└── config     # Show/validate config
```

### 6.4 Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | CLI usage error |
| 3 | Authentication error |
| 4 | Network/API error |
| 5 | Configuration error |
| 130 | Interrupted (Ctrl+C) |

---

## 7. Migration Phases

### Phase 0: Security Audit (Pre-Migration)
**Time**: 1 hour | **Risk**: Low | **Breaking**: None

| Task | Validation |
|------|------------|
| Run security checklist | All checks pass |
| Update `.gitignore` | Secrets patterns added |
| Remove log file from source | `git ls-files '*.log'` empty |
| Scan for hardcoded secrets | Grep patterns return empty |

### Phase 1: Critical Fixes
**Time**: 1 hour | **Risk**: Low | **Breaking**: None

| Task | Command |
|------|---------|
| Remove log from source | `git rm src/core/email_classifier.log` |
| Fix doc typo | `git mv docs/fulll_project_documentation.md docs/0109-1500_full_project_documentation.md` |
| Move test runner | `git mv tests/docs/run_comprehensive_tests.py tests/` |
| Run baseline measurements | Save to `docs/audit/` |

### Phase 2: Packaging Foundation
**Time**: 4 hours | **Risk**: Medium | **Breaking**: Import paths

| Task | Notes |
|------|-------|
| Create `pyproject.toml` | Use spec from Section 6.1 |
| Create package namespace | `mkdir -p src/gmail_fetcher` |
| Move source files | Use migration script |
| Create `__main__.py` | Entry point for `python -m` |
| Remove `sys.path.insert` | All files |
| Update all imports | Absolute from `gmail_fetcher.` |

### Phase 3: CLI Consolidation
**Time**: 3 hours | **Risk**: Medium | **Breaking**: CLI behavior

| Task | Notes |
|------|-------|
| Create `cli/commands/` | Subcommand modules |
| Move handlers | `src/gmail_fetcher/cli/handlers/` |
| Update main CLI | Click-based single entry point |
| Add deprecation warnings | Old flags/patterns |

### Phase 4: Config & Docs
**Time**: 2 hours | **Risk**: Low | **Breaking**: Config paths

| Task | Notes |
|------|-------|
| Flatten `config/` | Merge `app/` contents |
| Implement config loader | Resolution order contract |
| Create `docs/index.md` | Documentation hub |
| Restructure docs | Promote from `internal/` |
| Update README | Accurate paths |

### Phase 5: Test Organization
**Time**: 2 hours | **Risk**: Low | **Breaking**: None

| Task | Notes |
|------|-------|
| Create `conftest.py` | Shared fixtures |
| Organize `unit/` | Move unit tests |
| Organize `integration/` | Move integration tests |
| Update CI config | pytest paths |

---

## 8. Validation & Testing

### 8.1 Import Policy Checker

Location: `scripts/validation/check_import_policy.py`

Validates:
- No `sys.path.insert` or `sys.path.append`
- No imports from old package roots (`analysis`, `deletion`, `handlers`, etc.)
- No imports from `src` (never a valid package)
- Relative imports don't escape package boundary

### 8.2 Baseline Measurements

Location: `scripts/audit/baseline.ps1`

Metrics collected:
- `max_folder_depth`: Maximum directory nesting
- `sys_path_inserts`: Count of sys.path manipulations
- `config_locations`: Number of config directories
- `python_source_files`: Count of .py files in src/
- `test_files`: Count of test_*.py files
- `entry_points`: Number of entry point files
- `hidden_docs`: Count of docs in claude-docs/

### 8.3 Targets (Post-Migration)

| Metric | Target | Rationale |
|--------|--------|-----------|
| `max_folder_depth` | 3 | Keep structure shallow |
| `sys_path_inserts` | 0 | No sys.path hacks allowed |
| `config_locations` | 1 | Only `src/gmail_fetcher/analysis` expected |
| `entry_points` | 2 | `cli/main.py` + `__main__.py` |
| `hidden_docs` | 0 | No docs/claude-docs files |

### 8.4 Release DoD Checks

Three must-pass checks before release:

1. **Build and install wheel**: Build package, install in clean venv, verify imports
2. **Tests from outside repo**: Run pytest from temp directory with absolute paths
3. **Security checks**: No credentials tracked, gitignore reviewed, gitleaks pass

---

## 9. CI/CD Configuration

### 9.1 GitHub Actions Workflow

```yaml
name: CI

on:
  push:
    branches: [main, "refactor/**"]
  pull_request:
    branches: [main]

jobs:
  test:
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest]
        python-version: ["3.10", "3.11", "3.12"]

    runs-on: ${{ matrix.os }}

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"

      - name: Policy check
        run: python scripts/validation/check_import_policy.py

      - name: Compile check
        run: python -m compileall src/gmail_fetcher -q

      - name: Import resolution check
        shell: pwsh
        run: |
          $tempDir = [System.IO.Path]::GetTempPath()
          Push-Location $tempDir
          try {
              python -c "import gmail_fetcher; print('Version:', gmail_fetcher.__version__)"
              if ($LASTEXITCODE -ne 0) { throw 'Import check failed' }
          } finally {
              Pop-Location
          }

      - name: Run tests
        run: pytest -m "not integration and not api" --cov --cov-report=xml

      - name: Type check
        run: mypy src/gmail_fetcher

      - name: Lint
        run: ruff check src/gmail_fetcher tests

  build-validation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Build and verify
        run: |
          rm -rf dist/
          pip install build
          python -m build
          python -m venv /tmp/test-venv
          /tmp/test-venv/bin/pip install dist/gmail_fetcher-*.whl
          cd /tmp
          /tmp/test-venv/bin/python -c "import gmail_fetcher; assert gmail_fetcher.__version__ == '2.0.0'"
          /tmp/test-venv/bin/gmail-fetcher --version

  baseline-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run baseline measurements
        shell: pwsh
        run: pwsh -NoProfile -File ./scripts/audit/baseline.ps1 -OutputDir "docs/audit"

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Run gitleaks
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## 10. Security

### 10.1 Gitignore Patterns

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

### 10.2 Gitleaks Configuration

```toml
[extend]
useDefault = true

[allowlist]
description = "Allowlist for gmail-fetcher"
paths = [
    '''\.env\.example$''',
    '''credentials\.json\.template$''',
    '''token\.json\.template$''',
]

[[rules]]
id = "gmail-oauth-client-id"
description = "Gmail OAuth Client ID"
regex = '''[0-9]+-[a-z0-9]+\.apps\.googleusercontent\.com'''
entropy = 3.0

[[rules]]
id = "gmail-oauth-client-secret"
description = "Gmail OAuth Client Secret"
regex = '''GOCSPX-[a-zA-Z0-9_-]{28}'''
```

### 10.3 Credential Safety

The config loader enforces credential safety:
- Default paths point to user home (`~/.gmail-fetcher/`)
- Credentials inside git repos require explicit `--allow-repo-credentials` flag
- Emits warning when credentials are in repo (even with flag)
- Checks both config directory and CWD for repo detection

---

## 11. Breaking Changes

### 11.1 Import Paths

All imports have changed. There is no backward compatibility.

| Before (v1.x) | After (v2.0) |
|---------------|--------------|
| `from analysis.x import y` | `from gmail_fetcher.analysis.x import y` |
| `from core.fetch.gmail_fetcher import GmailFetcher` | `from gmail_fetcher.core.fetch.fetcher import GmailFetcher` |
| `from deletion.deleter import GmailDeleter` | `from gmail_fetcher.deletion.deleter import GmailDeleter` |
| `from handlers.x import y` | Removed - handlers merged into `gmail_fetcher.cli` |
| `from src.x import y` | `from gmail_fetcher.x import y` |

### 11.2 Entry Points

| Before | After |
|--------|-------|
| `python main.py fetch ...` | `gmail-fetcher fetch ...` |
| `python main.py --query "..."` | `gmail-fetcher fetch --query "..."` |
| `python main.py --auth-only` | `gmail-fetcher auth` |

### 11.3 CLI Flags

| Before | After |
|--------|-------|
| `--max` | `--max-emails` |
| `--output` | `--output-dir` |
| `--organize` | `--organize-by` |

### 11.4 Configuration

Default credential paths changed from repo-relative to user home:

| Before | After |
|--------|-------|
| `./credentials.json` | `~/.gmail-fetcher/credentials.json` |
| `./token.json` | `~/.gmail-fetcher/token.json` |
| `./gmail_backup` | `~/.gmail-fetcher/backups` |

### 11.5 Removed

- `main.py` entry point (use `gmail-fetcher` command)
- `src/handlers/` directory (merged into CLI)
- `sys.path` manipulation in all files
- Python 3.9 support (minimum is now 3.10)

### 11.6 Migration Steps

1. Install new version: `pip install gmail-fetcher>=2.0.0`
2. Update all import statements
3. Move credentials to `~/.gmail-fetcher/` or use `--allow-repo-credentials`
4. Update scripts: `python main.py` -> `gmail-fetcher`
5. Update CLI flags per table above

---

## 12. Architectural Decision Records

### ADR-0001: Package Layout and Build System

**Status**: Accepted
**Date**: 2026-01-09

**Decision**:
1. Build system: Hatchling (modern, fast, good src-layout support)
2. Package location: `src/gmail_fetcher/` (src-layout)
3. Entry point: Console script `gmail-fetcher` via Click
4. Python version: >=3.10 (enables modern syntax)

**Consequences**:
- Standard installation workflow
- Clean import paths
- IDE/tooling support
- All existing imports break (major version bump required)

### ADR-0002: Compatibility Strategy (Clean Break)

**Status**: Accepted
**Date**: 2026-01-09

**Decision**: Clean break without shims

**Rationale**:
- Shims add complexity and testing burden
- Shims delay inevitable cleanup
- Major version bump (v2.0.0) is appropriate signal
- Users must update imports anyway

### ADR-0003: CLI Framework Choice (Click)

**Status**: Accepted
**Date**: 2026-01-09

**Decision**: Use Click for CLI

**Rationale**:
- Widely used, well-documented
- Explicit over implicit (unlike argparse magic)
- Better error messages than argparse
- Easy testing with CliRunner

---

## 13. Implementation Checklist

### Pre-Migration
- [ ] Backup current structure: `git stash` or create branch
- [ ] Run full test suite: `pytest tests/`
- [ ] Document current import patterns
- [ ] Run baseline measurements

### Phase 0: Security
- [ ] Run security checklist
- [ ] `echo "*.log" >> .gitignore`
- [ ] `git rm src/core/email_classifier.log`
- [ ] Scan for hardcoded secrets

### Phase 1: Critical Fixes
- [ ] Fix doc typo
- [ ] Move test runner
- [ ] Commit: `git commit -m "fix: critical governance violations"`

### Phase 2: Packaging
- [ ] Create `pyproject.toml`
- [ ] Create `src/gmail_fetcher/__init__.py`
- [ ] Create `src/gmail_fetcher/__main__.py`
- [ ] Run migration script
- [ ] Remove all `sys.path.insert` calls
- [ ] Update all imports
- [ ] `pip install -e .`
- [ ] Validate: `pytest tests/`
- [ ] Commit: `git commit -m "feat: convert to installable package"`

### Phase 3: CLI
- [ ] Create Click-based CLI
- [ ] Move handlers to cli/handlers/
- [ ] Validate: `gmail-fetcher --help`
- [ ] Commit: `git commit -m "refactor: consolidate CLI structure"`

### Phase 4: Config & Docs
- [ ] Implement config loader
- [ ] Create `docs/index.md`
- [ ] Update README
- [ ] Commit: `git commit -m "docs: restructure documentation"`

### Phase 5: Tests
- [ ] Create `tests/conftest.py`
- [ ] Organize test directories
- [ ] Validate: `pytest`
- [ ] Commit: `git commit -m "test: organize test structure"`

### Post-Migration
- [ ] Run full test suite
- [ ] Run release DoD checks
- [ ] Verify all commands work
- [ ] Update CI/CD configuration

---

## 14. Success Metrics

| Metric | Current | Target | How Verified |
|--------|---------|--------|--------------|
| Folder depth | 4 | <=3 | Baseline script |
| sys.path inserts | 15+ | 0 | `grep -r "sys\.path\.insert"` |
| Config locations | 3+ | 1 | Manual count |
| Onboarding time | 30-45 min | <15 min | New developer survey |
| Import errors | Common | Zero | `python -c "import gmail_fetcher"` |
| Test discovery | Manual | Automatic | `pytest --collect-only` |

---

## 15. Risk Mitigation

### 15.1 Common Refactor Risks

| Risk | Probability | Mitigation |
|------|-------------|------------|
| **Relative path assumptions** | High | Audit all `Path(__file__)` usages |
| **Runtime string imports** | Medium | Grep for `importlib.import_module` |
| **Plugin discovery breaks** | Medium | Test plugin registration after each phase |
| **Circular imports revealed** | High | Run `python -X importtime` after Phase 2 |
| **pytest sys.path pollution** | High | Run tests from outside repo root |
| **Editable install conflicts** | Medium | `pip uninstall gmail-fetcher` before re-installing |
| **Config path resolution** | High | Test from all 4 resolution levels |

### 15.2 Rollback Strategy

Each phase can be rolled back independently:

- **Phase 0-1**: `git checkout HEAD~1 -- .`
- **Phase 2**: Restore from git, reinstall requirements
- **Phase 3**: `git checkout HEAD~1 -- src/`
- **Phase 4**: `git checkout HEAD~1 -- config/ docs/`
- **Phase 5**: `git checkout HEAD~1 -- tests/`

---

## Change History (v1-v7 Evolution)

This document consolidates all fixes made across seven iterations:

| Version | Key Changes |
|---------|-------------|
| v1 | Initial assessment, current state analysis, proposed structure |
| v2 | Added measurement methodology, pyproject.toml spec, security checklist, test organization policy |
| v3 | Critical decisions locked, Click CLI choice, clean break strategy, executable scripts |
| v4 | Fixed PowerShell exclusion bugs, config loader security improvements, Hatchling config fixes |
| v5 | Fixed bash script metrics, relative import validation, CI build cleanup |
| v6 | Fixed is_relative_to ValueError, removed bash scripts (PowerShell only) |
| v7 | Updated paths for post-migration, fixed CI baseline invocation, config type validation |

---

**Document Status**: Complete
**Implementation Ready**: Yes
**Recommended Start**: Phase 0 (Security Audit) - Immediate
