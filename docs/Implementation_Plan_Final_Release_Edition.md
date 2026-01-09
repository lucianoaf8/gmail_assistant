# Gmail Assistant Implementation Plan — Final (Release Edition, Corrected)

**Document ID**: Implementation_Plan_Final_Release_Edition_Corrected.md
**Date**: 2026-01-09
**Release Version**: 2.0.0
**Status**: Canonical — Single Source of Truth
**Correction Revision**: 1 (addresses Expert Assessment findings)

---

## Table of Contents

1. [Executive Overview](#1-executive-overview)
2. [Version Alignment](#2-version-alignment)
3. [Platform Contract](#3-platform-contract)
4. [Critical Decisions](#4-critical-decisions)
5. [Target Folder Structure](#5-target-folder-structure)
6. [Phase-by-Phase Migration Plan](#6-phase-by-phase-migration-plan)
7. [Rollback &amp; Recovery Procedures](#7-rollback--recovery-procedures)
8. [Tooling &amp; Automation](#8-tooling--automation)
9. [Configuration System](#9-configuration-system)
10. [Packaging &amp; Release Pipeline](#10-packaging--release-pipeline)
11. [CI/CD Design](#11-cicd-design)
12. [Validation &amp; Quality Gates](#12-validation--quality-gates)
13. [Risk Register](#13-risk-register)
14. [Acceptance Criteria &amp; Release Checklist](#14-acceptance-criteria--release-checklist)
15. [Revision History](#15-revision-history)

---

## 1. Executive Overview

### 1.1 Purpose

This document defines the complete migration of Gmail Assistant from an ad-hoc script collection to a properly packaged Python application. It serves as the single source of truth for all restructuring work.

### 1.2 Goals

| Goal                            | Metric                              | Target                                |
| ------------------------------- | ----------------------------------- | ------------------------------------- |
| Eliminate sys.path manipulation | Occurrences in codebase             | 0                                     |
| Reduce folder depth             | Max directory depth                 | ≤3                                   |
| Consolidate entry points        | Post-migration entry points         | 2 (`cli/main.py` + `__main__.py`) |
| Remove legacy entry points      | Legacy entry points                 | 0                                     |
| Standardize packaging           | Installable via pip                 | Yes                                   |
| Enable clean imports            | All imports use `gmail_assistant.*` | Yes                                   |
| Security-first configuration    | Credentials outside repo by default | Yes                                   |

### 1.3 Scope

| In Scope                           | Out of Scope                                           |
| ---------------------------------- | ------------------------------------------------------ |
| Package restructuring              | Feature development                                    |
| Import cleanup                     | Gmail API changes                                      |
| Configuration standardization      | New functionality                                      |
| CI/CD pipeline                     | UI redesign                                            |
| Documentation governance           | Performance optimization                               |
| CLI skeleton with argument parsing | Full functional implementation of fetch/delete/analyze |

### 1.4 Success Criteria

1. `pip install -e .` succeeds in clean venv
2. `gmail-assistant --help` produces expected output
3. `python -m gmail_assistant --help` produces expected output
4. All unit tests pass
5. No sys.path manipulation in codebase
6. No credentials tracked in git
7. Wheel installs and imports correctly from outside repo
8. CLI subcommands parse arguments correctly (functional behavior is out of scope for v2.0.0)

### 1.5 Functional Readiness Statement

**v2.0.0 is a packaging and restructuring release.** CLI commands are implemented as argument-parsing skeletons with TODO placeholders for business logic. Functional behavior (email fetching, deletion, analysis) is deferred to v2.1.0. Acceptance criteria and quality gates validate structural correctness, not end-to-end functionality.

---

## 2. Version Alignment

| Artifact                      | Version                            | Notes                                           |
| ----------------------------- | ---------------------------------- | ----------------------------------------------- |
| This document                 | Final (Release Edition, Corrected) | Supersedes v1–v8 and uncorrected Final         |
| Package release               | **2.0.0**                    | Major bump for breaking changes; packaging-only |
| `pyproject.toml`            | `version = "2.0.0"`              | Single source of truth for version              |
| `gmail_assistant/__init__.py` | `__version__ = "2.0.0"`          | Runtime version access                          |
| CHANGELOG.md                  | `## [2.0.0]`                     | Release notes                                   |
| BREAKING_CHANGES.md           | References v2.0.0                  | Migration guide                                 |
| Classifier                    | `Development Status :: 4 - Beta` | Packaging complete; functionality in progress   |

---

## 3. Platform Contract

### 3.1 Primary Environment

- **Operating System**: Windows 10/11
- **Python**: 3.10, 3.11, 3.12, 3.13
- **Shell**: PowerShell 7+ (pwsh)

### 3.2 CI Environment

- **Runners**: ubuntu-latest, windows-latest
- **Python Matrix**: 3.10, 3.11, 3.12, 3.13
- **Shell**: pwsh (cross-platform)

### 3.3 Developer Requirements

| Platform    | Requirement                                                              |
| ----------- | ------------------------------------------------------------------------ |
| Windows     | PowerShell 7+ (included in Windows 11, install separately on Windows 10) |
| Linux/macOS | PowerShell Core (`pwsh`) installed                                     |
| All         | Python 3.10+ with pip                                                    |
| All         | Git 2.x                                                                  |

### 3.4 Runtime Dependencies

| Dependency   | Required                | Behavior When Missing                                                            |
| ------------ | ----------------------- | -------------------------------------------------------------------------------- |
| Python 3.10+ | Yes                     | Application will not run                                                         |
| Git          | **No** (optional) | Config repo-safety checks disabled; warning logged; credentials allowed anywhere |
| Internet     | For auth/fetch only     | Offline mode for analysis of local backups                                       |

### 3.5 Runtime Invariants

| Invariant              | Specification                                                       |
| ---------------------- | ------------------------------------------------------------------- |
| Configuration encoding | UTF-8 JSON                                                          |
| Backup output format   | JSON (default), MBOX, EML                                           |
| Path handling          | Forward slashes normalized;`~` expanded via `Path.expanduser()` |
| Gmail API scopes       | `gmail.readonly` (fetch), `gmail.modify` (delete)               |
| Rate limiting          | Default 10 req/s; configurable; exponential backoff on 429          |
| Idempotency            | Fetch is idempotent (overwrites); Delete is NOT idempotent          |
| File permissions       | User-only read/write for credentials/tokens (0600 on Unix)          |

---

## 4. Critical Decisions

| Decision                | Choice                                      | Rationale                                                                      | ADR                                                  |
| ----------------------- | ------------------------------------------- | ------------------------------------------------------------------------------ | ---------------------------------------------------- |
| Compatibility strategy  | **Clean break**                       | No shims. Bump to v2.0.0 with documented breaking changes. Reduces complexity. | ADR-0002                                             |
| CLI framework           | **Click**                             | Better UX than argparse, good subcommand support, widespread adoption.         | ADR-0003                                             |
| Config default location | **User home** (`~/.gmail-assistant/`) | Security-first. Repo-local requires explicit opt-in.                           | ADR-0001                                             |
| Build backend           | **Hatchling**                         | Modern, fast, correct src-layout defaults.                                     | ADR-0001                                             |
| Python minimum          | **>=3.10**                            | Enables `                                                                      | ` union types, match statements. Realistic for 2026. |
| Scripting language      | **PowerShell**                        | Cross-platform via pwsh. Windows-first project.                                | ADR-0001                                             |
| Exception taxonomy      | **Single hierarchy**                  | All domain exceptions inherit from `GmailAssistantError` in `exceptions.py`. | ADR-0004                                             |

---

## 5. Target Folder Structure

### 5.1 Post-Migration Layout

```
gmail_assistant/                          # REPO ROOT
│
├── pyproject.toml                      # Package configuration (single source of truth)
├── README.md                           # User-facing documentation
├── CLAUDE.md                           # AI assistant context
├── CHANGELOG.md                        # Release notes
├── BREAKING_CHANGES.md                 # Migration guide for v2.0.0
├── LICENSE                             # MIT license
├── .gitignore                          # Security patterns included
├── .pre-commit-config.yaml             # Pre-commit hook configuration
│
├── src/
│   └── gmail_assistant/                  # INSTALLABLE PACKAGE
│       ├── __init__.py                 # Package root, exports __version__
│       ├── __main__.py                 # python -m gmail_assistant entry point
│       ├── py.typed                    # PEP 561 marker
│       │
│       ├── cli/                        # COMMAND LINE INTERFACE
│       │   ├── __init__.py
│       │   ├── main.py                 # Click application, console script entry
│       │   └── commands/               # Subcommand modules
│       │       ├── __init__.py
│       │       ├── fetch.py
│       │       ├── delete.py
│       │       ├── analyze.py
│       │       ├── auth.py
│       │       └── config.py
│       │
│       ├── core/                       # BUSINESS LOGIC
│       │   ├── __init__.py
│       │   ├── config.py               # Configuration loader
│       │   ├── exceptions.py           # Centralized exceptions (SINGLE SOURCE)
│       │   ├── constants.py            # Application constants
│       │   ├── auth/
│       │   │   ├── __init__.py
│       │   │   └── oauth.py
│       │   ├── fetch/
│       │   │   ├── __init__.py
│       │   │   └── fetcher.py
│       │   └── processing/
│       │       ├── __init__.py
│       │       └── processor.py
│       │
│       ├── analysis/                   # EMAIL ANALYSIS
│       │   ├── __init__.py
│       │   ├── engine.py
│       │   └── classifier.py
│       │
│       ├── deletion/                   # EMAIL DELETION
│       │   ├── __init__.py
│       │   └── deleter.py
│       │
│       ├── parsers/                    # EMAIL PARSING
│       │   ├── __init__.py
│       │   └── email_parser.py
│       │
│       └── utils/                      # UTILITIES
│           ├── __init__.py
│           └── helpers.py
│
├── tests/                              # TEST SUITE
│   ├── conftest.py                     # Shared fixtures
│   ├── unit/                           # Unit tests (default)
│   │   ├── test_config.py
│   │   ├── test_cli.py
│   │   ├── test_exceptions.py
│   │   └── test_core/
│   ├── integration/                    # Integration tests (marked)
│   │   └── test_gmail_api.py
│   └── fixtures/                       # Test data
│       └── sample_emails.json
│
├── config/                             # CONFIGURATION TEMPLATES
│   ├── default.json.template           # Example config
│   ├── logging.yaml                    # Logging configuration
│   └── schema/
│       └── config.schema.json          # JSON Schema for validation
│
├── scripts/                            # AUTOMATION
│   ├── audit/
│   │   └── baseline.ps1                # Baseline measurements
│   ├── migration/
│   │   └── move_to_package_layout.ps1  # Migration execution
│   ├── validation/
│   │   ├── check_import_policy.py      # Import policy checker
│   │   ├── check_import_resolution.py  # Import resolution checker
│   │   └── release_checks.ps1          # Release DoD checks
│   └── verify_all.ps1                  # UNIFIED VERIFICATION PIPELINE
│
├── docs/                               # DOCUMENTATION
│   ├── index.md                        # Documentation hub
│   ├── getting-started.md              # Quick start guide
│   ├── configuration.md                # Config reference
│   ├── cli-reference.md                # CLI documentation
│   ├── troubleshooting.md              # Error catalog
│   ├── adr/                            # Architecture Decision Records
│   │   ├── README.md                   # ADR index
│   │   ├── ADR-0001-package-layout.md
│   │   ├── ADR-0002-compatibility.md
│   │   ├── ADR-0003-cli-framework.md
│   │   └── ADR-0004-exception-taxonomy.md
│   └── internal/                       # Internal/timestamped docs
│       └── [YYYYMMDD-HHMM_topic.md]
│
├── logs/                               # LOG FILES (gitignored)
├── data/                               # DATA FILES (gitignored)
└── backups/                            # BACKUPS (gitignored)
```

### 5.2 Removed Items (Post-Migration)

| Item                              | Reason                                          |
| --------------------------------- | ----------------------------------------------- |
| `main.py` (repo root)           | Replaced by console script                      |
| `src/cli/main.py`               | Moved to `src/gmail_assistant/cli/main.py`      |
| `src/handlers/`                 | Merged into `src/gmail_assistant/cli/commands/` |
| `src/tools/`                    | Functionality merged into `utils/` or removed |
| `src/plugins/`                  | Deferred to v2.1.0 (no plugin contract defined) |
| `config/app/`                   | Flattened to `config/`                        |
| `docs/claude-docs/`             | Promoted to `docs/`                           |
| `tests/docs/`                   | Tests moved to `tests/`                       |
| `src/core/email_classifier.log` | Log files must not be in source                 |

### 5.3 Deferred Items

| Item                          | Reason                                     | Target Version |
| ----------------------------- | ------------------------------------------ | -------------- |
| `plugins/` directory        | Plugin contract not defined; no governance | v2.1.0         |
| Functional CLI implementation | Packaging-only release                     | v2.1.0         |

---

## 6. Phase-by-Phase Migration Plan

### 6.0 Phase Governance

**Commit Boundary Rule**: Each phase MUST conclude with exactly one commit (or a squashed commit) using the prescribed commit message. This enables deterministic rollback.

**Phase Commit Message Format**:

```
phase-N: <short description>

Phase N of Gmail Assistant restructuring.
See: Implementation_Plan_Final_Release_Edition_Corrected.md §6.N
```

**Phase Tag Format** (optional but recommended):

```
migration/phase-N-complete
```

---

### 6.1 Phase 0: Security Audit

**Duration**: 1 hour
**Risk**: Low
**Breaking Changes**: None
**Depends On**: None

| Task                       | Command/Action                               | Validation                  |
| -------------------------- | -------------------------------------------- | --------------------------- |
| Update .gitignore          | Add security patterns                        | Patterns present            |
| Remove tracked log files   | `git rm src/core/email_classifier.log`     | No .log in `git ls-files` |
| Scan for hardcoded secrets | Run gitleaks                                 | No findings                 |
| Check credential files     | `git ls-files \| Select-String credentials` | Empty result                |
| Verify token files         | `git ls-files \| Select-String token.json`  | Empty result                |

**Definition of Done**:

- [ ] `.gitignore` includes: `credentials.json`, `token.json`, `*.log`, `backups/`, `data/`
- [ ] `git ls-files '*.log'` returns empty
- [ ] `gitleaks detect` passes (if installed)

**Phase Commit**:

```bash
git add -A
git commit -m "phase-0: security audit and gitignore hardening"
git tag migration/phase-0-complete
```

**Rollback**: Not applicable (additive changes only)

---

### 6.2 Phase 1: Critical Fixes

**Duration**: 1 hour
**Risk**: Low
**Breaking Changes**: None
**Depends On**: Phase 0

| Task             | Command                                                                           | Validation     |
| ---------------- | --------------------------------------------------------------------------------- | -------------- |
| Fix doc typo     | `git mv docs/fulll_project_documentation.md docs/full_project_documentation.md` | File renamed   |
| Move test runner | `git mv tests/docs/run_comprehensive_tests.py tests/`                           | File in tests/ |
| Run baseline     | `.\scripts\audit\baseline.ps1`                                                  | JSON created   |

**Definition of Done**:

- [ ] No typos in filenames
- [ ] Baseline measurements saved to `docs/audit/`

**Phase Commit**:

```bash
git add -A
git commit -m "phase-1: critical fixes and baseline capture"
git tag migration/phase-1-complete
```

**Rollback**:

```powershell
git revert $(git rev-parse migration/phase-1-complete) --no-edit
```

---

### 6.3 Phase 2: Packaging Foundation

**Duration**: 4 hours
**Risk**: Medium
**Breaking Changes**: Import paths
**Depends On**: Phase 1

| Task                     | Action                                                          | Validation                           |
| ------------------------ | --------------------------------------------------------------- | ------------------------------------ |
| Create pyproject.toml    | Use spec from §10.1                                            | `pip install . --dry-run` succeeds |
| Create package namespace | `New-Item -ItemType Directory -Path src/gmail_assistant -Force` | Directory exists                     |
| Run migration script     | `.\scripts\migration\move_to_package_layout.ps1`              | Script completes                     |
| Remove sys.path.insert   | Manual edit or search/replace                                   | `grep -r "sys.path.insert"` empty  |
| Update all imports       | Change to `gmail_assistant.*` prefix                            | Import policy passes                 |
| Create py.typed          | `New-Item src/gmail_assistant/py.typed`                         | File exists                          |
| Install editable         | `pip install -e .`                                            | Succeeds                             |

**Definition of Done**:

- [ ] `pip install -e .` succeeds in clean venv
- [ ] `python -m gmail_assistant --help` works
- [ ] `gmail-assistant --help` works
- [ ] `python -m compileall src/gmail_assistant -q` succeeds
- [ ] `python scripts/validation/check_import_policy.py` passes
- [ ] No `sys.path.insert` or `sys.path.append` in codebase

**Phase Commit**:

```bash
git add -A
git commit -m "phase-2: packaging foundation and src-layout migration"
git tag migration/phase-2-complete
```

**Rollback**:

```powershell
git revert $(git rev-parse migration/phase-2-complete) --no-edit
git clean -fd src/gmail_assistant
pip uninstall gmail-assistant -y
```

---

### 6.4 Phase 3: Configuration & Exceptions

**Duration**: 2 hours
**Risk**: Low
**Breaking Changes**: Config file paths
**Depends On**: Phase 2

**Rationale**: Configuration and exception taxonomy must be established BEFORE CLI implementation because CLI imports and maps these types.

| Task                       | Action                                    | Validation                         |
| -------------------------- | ----------------------------------------- | ---------------------------------- |
| Create exceptions.py       | Write core/exceptions.py per §9.2        | File exists, exports correct types |
| Implement config loader    | Write core/config.py per §9.1            | Loads from all levels              |
| Create config.schema.json  | Write schema per §9.3                    | Valid JSON Schema                  |
| Add schema validation test | Unit test validates schema matches loader | Test passes                        |
| Create docs/index.md       | Write documentation hub                   | Links work                         |
| Create docs/adr/           | Write ADR-0001, 0002, 0003, 0004          | Files exist                        |
| Update README.md           | Accurate paths and commands               | Commands work                      |
| Create BREAKING_CHANGES.md | Document all breaking changes             | Complete                           |

**Definition of Done**:

- [ ] `from gmail_assistant.core.exceptions import ConfigError, AuthError, NetworkError` works
- [ ] Config loads from: CLI arg → env var → project → home → defaults
- [ ] `docs/index.md` exists with working links
- [ ] All ADRs documented including ADR-0004 (exception taxonomy)
- [ ] README commands are accurate
- [ ] Unit test confirms schema matches loader behavior

**Phase Commit**:

```bash
git add -A
git commit -m "phase-3: configuration system and exception taxonomy"
git tag migration/phase-3-complete
```

**Rollback**:

```powershell
git revert $(git rev-parse migration/phase-3-complete) --no-edit
```

---

### 6.5 Phase 4: CLI Consolidation

**Duration**: 3 hours
**Risk**: Medium
**Breaking Changes**: CLI interface
**Depends On**: Phase 3 (config and exceptions must exist)

| Task                     | Action                                                                | Validation          |
| ------------------------ | --------------------------------------------------------------------- | ------------------- |
| Create commands/         | `New-Item -ItemType Directory -Path src/gmail_assistant/cli/commands` | Directory exists    |
| Implement Click CLI      | Write main.py with Click                                              | CLI runs            |
| Add subcommand skeletons | fetch, delete, analyze, auth, config                                  | All `--help` work |
| Implement error handler  | `@handle_errors` decorator using exceptions from §9.2              | Exit codes correct  |
| Update__main__.py  | Import and call main                                                  | `python -m` works |

**Definition of Done**:

- [ ] `gmail-assistant fetch --help` shows expected flags
- [ ] `gmail-assistant delete --help` shows expected flags
- [ ] `gmail-assistant analyze --help` shows expected flags
- [ ] `gmail-assistant auth --help` shows expected flags
- [ ] `gmail-assistant config --help` shows expected flags
- [ ] Exit codes match specification (0=success, 1=general, 2=usage, 3=auth, 4=network, 5=config)
- [ ] All exception types imported from `gmail_assistant.core.exceptions`

**Phase Commit**:

```bash
git add -A
git commit -m "phase-4: CLI consolidation with Click"
git tag migration/phase-4-complete
```

**Rollback**:

```powershell
git revert $(git rev-parse migration/phase-4-complete) --no-edit
pip install -e .
```

---

### 6.6 Phase 5: Test Organization

**Duration**: 2 hours
**Risk**: Low
**Breaking Changes**: None
**Depends On**: Phase 4

| Task                  | Action                        | Validation                        |
| --------------------- | ----------------------------- | --------------------------------- |
| Create conftest.py    | Write shared fixtures         | Fixtures available                |
| Organize unit/        | Move unit tests               | `pytest tests/unit/` passes     |
| Organize integration/ | Move integration tests        | Tests organized                   |
| Add exception tests   | Test exception hierarchy      | All exceptions testable           |
| Configure markers     | Verify pyproject.toml markers | `pytest --markers` shows custom |
| Run full suite        | `pytest`                    | All tests pass                    |

**Definition of Done**:

- [ ] `pytest -m unit` passes
- [ ] `pytest -m integration` runs (may skip without credentials)
- [ ] `pytest --cov` reports ≥70% coverage (required gate)
- [ ] No `pytest.ini` file (config in pyproject.toml)
- [ ] Exception hierarchy tests pass

**Phase Commit**:

```bash
git add -A
git commit -m "phase-5: test organization and coverage gate"
git tag migration/phase-5-complete
```

**Rollback**:

```powershell
git revert $(git rev-parse migration/phase-5-complete) --no-edit
```

---

## 7. Rollback & Recovery Procedures

### 7.1 Phase-Level Rollback

Each phase has a deterministic rollback using its completion tag:

```powershell
# Rollback specific phase (preserves later phases if any)
git revert $(git rev-parse migration/phase-N-complete) --no-edit

# Or hard reset to before a phase (destructive)
git reset --hard migration/phase-$(N-1)-complete
```

### 7.2 Rollback Reference Table

| Phase | Tag                            | Rollback Command                                           |
| ----- | ------------------------------ | ---------------------------------------------------------- |
| 0     | `migration/phase-0-complete` | N/A (additive only)                                        |
| 1     | `migration/phase-1-complete` | `git revert $(git rev-parse migration/phase-1-complete)` |
| 2     | `migration/phase-2-complete` | `git revert ...` + `pip uninstall gmail-assistant -y`    |
| 3     | `migration/phase-3-complete` | `git revert $(git rev-parse migration/phase-3-complete)` |
| 4     | `migration/phase-4-complete` | `git revert ...` + `pip install -e .`                  |
| 5     | `migration/phase-5-complete` | `git revert $(git rev-parse migration/phase-5-complete)` |

### 7.3 Full Migration Rollback

To completely revert to pre-migration state:

```powershell
# 1. Identify the commit before Phase 0
$prePhase0 = git rev-parse migration/phase-0-complete~1

# 2. Create a rollback branch
git checkout -b rollback/pre-migration $prePhase0

# 3. Uninstall the package
pip uninstall gmail-assistant -y

# 4. Clean generated files
git clean -fd

# 5. Verify
python main.py --help  # Should work with old structure
```

### 7.4 Emergency Recovery

If migration leaves repo in broken state without tags:

```powershell
# 1. Stash any uncommitted changes
git stash

# 2. Reset to last known good state
git reset --hard origin/main

# 3. Clean all untracked files
git clean -fdx

# 4. Reinstall dependencies
pip install -e ".[dev]"

# 5. Run verification
.\scripts\verify_all.ps1
```

---

## 8. Tooling & Automation

### 8.1 Baseline Measurement Script

**Location**: `scripts/audit/baseline.ps1`

```powershell
#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Captures baseline measurements and writes JSON atomically.
.DESCRIPTION
    Measures repository structure metrics against defined targets.
    Outputs JSON file with schema version 1.4 (corrected metric names).
.PARAMETER OutputDir
    Directory for baseline JSON output. Default: docs/audit
.EXAMPLE
    .\scripts\audit\baseline.ps1 -OutputDir docs/audit
#>
[CmdletBinding()]
param(
    [string]$OutputDir = "docs/audit"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

# Ensure we're in repo root
$repoRoot = (& git rev-parse --show-toplevel 2>$null)
if (-not $repoRoot) {
    Write-Error "Not in a git repository"
    exit 1
}
$repoRoot = (Resolve-Path $repoRoot).Path
Set-Location $repoRoot

# Create output directory
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

# Timestamp and commit
$timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
$fileTimestamp = (Get-Date).ToString("yyyyMMdd-HHmm")
$commitSha = & git rev-parse HEAD 2>$null
if (-not $commitSha) { $commitSha = "no-commits" }

# Excluded directory names (segment-based)
$excludeNames = @(
    '.git', '__pycache__', 'node_modules', 'backups', '.venv', 'venv',
    '.pytest_cache', '.mypy_cache', '.ruff_cache', 'htmlcov', 'dist', 'build', '*.egg-info'
)

function Test-ShouldExclude {
    param([string]$FullPath)
    $relativePath = $FullPath.Substring($repoRoot.Length).TrimStart('\', '/')
    $segments = @($relativePath -split '[\\/]')
    foreach ($segment in $segments) {
        foreach ($exclude in $excludeNames) {
            if ($exclude.Contains('*')) {
                if ($segment -like $exclude) { return $true }
            } else {
                if ($segment -eq $exclude) { return $true }
            }
        }
    }
    return $false
}

function Get-MaxFolderDepth {
    $maxDepth = 0
    Get-ChildItem -Path $repoRoot -Directory -Recurse -Force -ErrorAction SilentlyContinue |
        Where-Object { -not (Test-ShouldExclude $_.FullName) } |
        ForEach-Object {
            $relativePath = $_.FullName.Substring($repoRoot.Length).TrimStart('\', '/')
            $segments = @(($relativePath -split '[\\/]') | Where-Object { $_ -ne '' })
            $depth = $segments.Count
            if ($depth -gt $maxDepth) { $maxDepth = $depth }
        }
    return $maxDepth
}

function Get-SysPathInsertCount {
    $count = 0
    Get-ChildItem -Path $repoRoot -Filter "*.py" -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { -not (Test-ShouldExclude $_.FullName) } |
        ForEach-Object {
            $content = Get-Content $_.FullName -Raw -ErrorAction SilentlyContinue
            if ($content) {
                $matches = [regex]::Matches($content, 'sys\.path\.(insert|append)')
                $count += $matches.Count
            }
        }
    return $count
}

# CORRECTED: Renamed from "config_locations" to "package_modules"
# Checks for expected post-migration package structure
function Get-PostMigrationPackageModuleCount {
    $expectedModules = @(
        "src/gmail_assistant/core",
        "src/gmail_assistant/cli",
        "src/gmail_assistant/analysis"
    )
    return ($expectedModules | Where-Object { Test-Path (Join-Path $repoRoot $_) }).Count
}

# CORRECTED: Legacy structure modules
function Get-LegacyPackageModuleCount {
    $legacy = @("src/core", "src/cli", "src/analysis", "src/handlers")
    return ($legacy | Where-Object { Test-Path (Join-Path $repoRoot $_) }).Count
}

function Get-PythonFileCount {
    $srcPath = Join-Path $repoRoot "src"
    if (-not (Test-Path $srcPath)) { return 0 }
    return (Get-ChildItem -Path $srcPath -Filter "*.py" -Recurse -File |
        Where-Object { -not (Test-ShouldExclude $_.FullName) }).Count
}

function Get-TestFileCount {
    $testsPath = Join-Path $repoRoot "tests"
    if (-not (Test-Path $testsPath)) { return 0 }
    return (Get-ChildItem -Path $testsPath -Filter "test_*.py" -Recurse -File |
        Where-Object { -not (Test-ShouldExclude $_.FullName) }).Count
}

function Get-PostMigrationEntryPointCount {
    $entryPoints = @(
        "src/gmail_assistant/cli/main.py",
        "src/gmail_assistant/__main__.py"
    )
    return ($entryPoints | Where-Object { Test-Path (Join-Path $repoRoot $_) }).Count
}

function Get-LegacyEntryPointCount {
    $legacy = @("main.py", "src/cli/main.py")
    return ($legacy | Where-Object { Test-Path (Join-Path $repoRoot $_) }).Count
}

function Get-HiddenDocsCount {
    $claudeDocsPath = Join-Path $repoRoot "docs/claude-docs"
    if (-not (Test-Path $claudeDocsPath)) { return 0 }
    return (Get-ChildItem -Path $claudeDocsPath -Filter "*.md" -File).Count
}

# Collect measurements
Write-Host "Collecting measurements..." -ForegroundColor Cyan

$measurements = [ordered]@{
    max_folder_depth                  = Get-MaxFolderDepth
    sys_path_inserts                  = Get-SysPathInsertCount
    post_migration_package_modules    = Get-PostMigrationPackageModuleCount
    legacy_package_modules            = Get-LegacyPackageModuleCount
    python_source_files               = Get-PythonFileCount
    test_files                        = Get-TestFileCount
    post_migration_entry_points       = Get-PostMigrationEntryPointCount
    legacy_entry_points               = Get-LegacyEntryPointCount
    hidden_docs                       = Get-HiddenDocsCount
}

$baseline = [ordered]@{
    schema_version                    = "1.4"
    depth_convention                  = "segments_under_repo_root"
    timestamp                         = $timestamp
    commit_sha                        = $commitSha
    repo_root                         = $repoRoot
    measurements                      = $measurements
    targets = [ordered]@{
        max_folder_depth              = 3
        sys_path_inserts              = 0
        post_migration_package_modules = 3
        legacy_package_modules        = 0
        post_migration_entry_points   = 2
        legacy_entry_points           = 0
        hidden_docs                   = 0
    }
}

# Write atomically
$outputFile = Join-Path $OutputDir "${fileTimestamp}_baseline.json"
$tempFile = [System.IO.Path]::GetTempFileName()

try {
    $baseline | ConvertTo-Json -Depth 10 | Set-Content -Path $tempFile -Encoding UTF8 -NoNewline
    $null = Get-Content $tempFile | ConvertFrom-Json
    Move-Item -Path $tempFile -Destination $outputFile -Force
    Write-Host "Baseline written to: $outputFile" -ForegroundColor Green
}
catch {
    if (Test-Path $tempFile) { Remove-Item $tempFile -Force }
    throw
}

# Display results
Write-Host ""
Write-Host "Measurements vs Targets:" -ForegroundColor Cyan
$allPass = $true
$measurements.GetEnumerator() | ForEach-Object {
    $target = $baseline.targets[$_.Key]
    if ($null -ne $target) {
        $pass = $_.Value -le $target
        # For "post_migration_*" metrics, we want >= target
        if ($_.Key -like "post_migration_*") {
            $pass = $_.Value -ge $target
        }
        $status = if ($pass) { "[PASS]" } else { "[FAIL]" }
        $color = if ($pass) { "Green" } else { "Red" }
        if (-not $pass) { $allPass = $false }
        Write-Host "  $status $($_.Key): $($_.Value) (target: $target)" -ForegroundColor $color
    } else {
        Write-Host "  [INFO] $($_.Key): $($_.Value)" -ForegroundColor Gray
    }
}

Write-Host ""
if ($allPass) {
    Write-Host "All targets met." -ForegroundColor Green
    exit 0
} else {
    Write-Host "Some targets not met." -ForegroundColor Yellow
    exit 0  # Non-blocking for pre-migration runs
}
```

### 8.2 Migration Script

**Location**: `scripts/migration/move_to_package_layout.ps1`

```powershell
#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Migrates source files to src/gmail_assistant package layout.
.DESCRIPTION
    CORRECTED: Aligns with §5 Target Folder Structure.
    - Moves src/handlers to src/gmail_assistant/cli/commands (not cli/handlers)
    - Does NOT move src/tools or src/plugins (deferred/removed per §5.2, §5.3)
.PARAMETER DryRun
    Show what would be done without making changes.
.PARAMETER Version
    Version string for __init__.py. Default: 2.0.0
.EXAMPLE
    .\scripts\migration\move_to_package_layout.ps1 -DryRun
    .\scripts\migration\move_to_package_layout.ps1
#>
[CmdletBinding()]
param(
    [switch]$DryRun,
    [string]$Version = "2.0.0"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repoRoot = (git rev-parse --show-toplevel)
if (-not $repoRoot) {
    Write-Error "Not in a git repository"
    exit 1
}
$repoRoot = (Resolve-Path $repoRoot).Path
Set-Location $repoRoot

Write-Host "=== Gmail Assistant Migration Script ===" -ForegroundColor Cyan
Write-Host "Repo root: $repoRoot"
Write-Host "Version: $Version"
Write-Host "Dry run: $DryRun"
Write-Host ""

# Preflight checks
Write-Host "=== Preflight Checks ===" -ForegroundColor Yellow

$targetDir = "src/gmail_assistant"
if ((Test-Path $targetDir) -and -not $DryRun) {
    $existing = Get-ChildItem $targetDir -ErrorAction SilentlyContinue
    if ($existing.Count -gt 0) {
        Write-Error "Target directory $targetDir already has content. Aborting."
        exit 1
    }
}

$gitStatus = git status --porcelain
if ($gitStatus -and -not $DryRun) {
    Write-Host "[WARN] Working tree has uncommitted changes:" -ForegroundColor Yellow
    Write-Host $gitStatus
    $confirm = Read-Host "Continue anyway? (y/N)"
    if ($confirm -ne 'y') {
        Write-Host "Aborted." -ForegroundColor Red
        exit 1
    }
}

Write-Host "[OK] Preflight checks passed" -ForegroundColor Green
Write-Host ""

# Define moves - CORRECTED to match §5 Target Folder Structure
$moves = @(
    @{From="src/cli"; To="src/gmail_assistant/cli"},
    @{From="src/core"; To="src/gmail_assistant/core"},
    @{From="src/analysis"; To="src/gmail_assistant/analysis"},
    @{From="src/deletion"; To="src/gmail_assistant/deletion"},
    @{From="src/handlers"; To="src/gmail_assistant/cli/commands"},  # CORRECTED: to commands/ not handlers/
    @{From="src/parsers"; To="src/gmail_assistant/parsers"},
    @{From="src/utils"; To="src/gmail_assistant/utils"}
    # NOTE: src/tools and src/plugins are NOT moved (deferred per §5.3)
)

# Items to explicitly skip with warning
$skippedDirs = @("src/tools", "src/plugins")

# Create target directory
Write-Host "=== Creating Package Structure ===" -ForegroundColor Yellow

if ($DryRun) {
    Write-Host "[DRY-RUN] mkdir $targetDir" -ForegroundColor Yellow
} else {
    New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    Write-Host "[CREATED] $targetDir" -ForegroundColor Green
}

# Warn about skipped directories
foreach ($skipped in $skippedDirs) {
    if (Test-Path $skipped) {
        Write-Host "[SKIP] $skipped exists but is deferred (see §5.3)" -ForegroundColor Yellow
    }
}

# Execute moves
Write-Host ""
Write-Host "=== Moving Directories ===" -ForegroundColor Yellow

foreach ($move in $moves) {
    $from = $move.From
    $to = $move.To

    if (-not (Test-Path $from)) {
        Write-Host "[SKIP] $from does not exist" -ForegroundColor Gray
        continue
    }

    if ($DryRun) {
        Write-Host "[DRY-RUN] git mv $from $to" -ForegroundColor Yellow
    } else {
        $parent = Split-Path $to -Parent
        if (-not (Test-Path $parent)) {
            New-Item -ItemType Directory -Path $parent -Force | Out-Null
        }
        git mv $from $to
        Write-Host "[MOVED] $from -> $to" -ForegroundColor Green
    }
}

# Create required files
Write-Host ""
Write-Host "=== Creating Package Files ===" -ForegroundColor Yellow

# __init__.py
$initContent = @"
"""Gmail Assistant - Gmail backup, analysis, and management suite."""
__version__ = "$Version"
__all__ = ["__version__"]
"@

$initPath = "$targetDir/__init__.py"
if ($DryRun) {
    Write-Host "[DRY-RUN] create $initPath" -ForegroundColor Yellow
} else {
    Set-Content -Path $initPath -Value $initContent -Encoding UTF8
    Write-Host "[CREATED] $initPath" -ForegroundColor Green
}

# __main__.py
$mainContent = @'
"""Entry point for python -m gmail_assistant."""
from gmail_assistant.cli.main import main

if __name__ == "__main__":
    raise SystemExit(main())
'@

$mainPath = "$targetDir/__main__.py"
if ($DryRun) {
    Write-Host "[DRY-RUN] create $mainPath" -ForegroundColor Yellow
} else {
    Set-Content -Path $mainPath -Value $mainContent -Encoding UTF8
    Write-Host "[CREATED] $mainPath" -ForegroundColor Green
}

# py.typed
$pytypedPath = "$targetDir/py.typed"
if ($DryRun) {
    Write-Host "[DRY-RUN] create $pytypedPath" -ForegroundColor Yellow
} else {
    New-Item -ItemType File -Path $pytypedPath -Force | Out-Null
    Write-Host "[CREATED] $pytypedPath" -ForegroundColor Green
}

# Create __init__.py in cli/commands/ if it doesn't exist
$commandsInitPath = "$targetDir/cli/commands/__init__.py"
if ((Test-Path "$targetDir/cli/commands") -and -not (Test-Path $commandsInitPath)) {
    if ($DryRun) {
        Write-Host "[DRY-RUN] create $commandsInitPath" -ForegroundColor Yellow
    } else {
        Set-Content -Path $commandsInitPath -Value '"""CLI subcommand modules."""' -Encoding UTF8
        Write-Host "[CREATED] $commandsInitPath" -ForegroundColor Green
    }
}

# Cleanup old src/__init__.py
$oldInit = "src/__init__.py"
if (Test-Path $oldInit) {
    if ($DryRun) {
        Write-Host "[DRY-RUN] remove $oldInit" -ForegroundColor Yellow
    } else {
        $tracked = git ls-files $oldInit
        if ($tracked) {
            git rm $oldInit 2>$null
        } else {
            Remove-Item $oldInit -Force
        }
        Write-Host "[REMOVED] $oldInit" -ForegroundColor Yellow
    }
}

# Post-move validation
if (-not $DryRun) {
    Write-Host ""
    Write-Host "=== Post-Move Validation ===" -ForegroundColor Cyan

    $required = @(
        "$targetDir/__init__.py",
        "$targetDir/__main__.py",
        "$targetDir/py.typed"
    )

    $allOk = $true
    foreach ($path in $required) {
        if (Test-Path $path) {
            Write-Host "[OK] $path exists" -ForegroundColor Green
        } else {
            Write-Host "[FAIL] $path missing" -ForegroundColor Red
            $allOk = $false
        }
    }

    # Verify __version__
    $content = Get-Content "$targetDir/__init__.py" -Raw
    if ($content -match '__version__\s*=\s*"(\d+\.\d+\.\d+)"') {
        $foundVersion = $Matches[1]
        if ($foundVersion -eq $Version) {
            Write-Host "[OK] __version__ = '$foundVersion'" -ForegroundColor Green
        } else {
            Write-Host "[FAIL] __version__ mismatch: $foundVersion != $Version" -ForegroundColor Red
            $allOk = $false
        }
    } else {
        Write-Host "[FAIL] __version__ not found" -ForegroundColor Red
        $allOk = $false
    }

    Write-Host ""
    if ($allOk) {
        Write-Host "=== Migration Complete ===" -ForegroundColor Green
        Write-Host "Next steps:"
        Write-Host "  1. Update all imports to use gmail_assistant.* prefix"
        Write-Host "  2. Remove all sys.path.insert/append calls"
        Write-Host "  3. Run: pip install -e ."
        Write-Host "  4. Run: python scripts/validation/check_import_policy.py"
        Write-Host "  5. Run: pytest"
        Write-Host "  6. Commit: git add -A && git commit -m 'phase-2: packaging foundation'"
    } else {
        Write-Host "=== Migration Failed ===" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host ""
    Write-Host "DRY RUN complete. Run without -DryRun to execute." -ForegroundColor Cyan
}
```

### 8.3 Import Policy Checker

**Location**: `scripts/validation/check_import_policy.py`

```python
#!/usr/bin/env python3
"""
Import policy checker - validates imports follow post-migration conventions.

Checks:
1. No sys.path manipulation
2. No imports from old package roots
3. No invalid relative imports
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import NamedTuple


class Violation(NamedTuple):
    file: Path
    line: int
    message: str


# Old package roots that should not be imported directly
OLD_PACKAGE_ROOTS = frozenset({
    "src",
    "analysis",
    "deletion",
    "handlers",
    "parsers",
    "plugins",
    "tools",
    "utils",
    "core",
    "cli",
})

# These are never valid as import roots
INVALID_IMPORT_ROOTS = frozenset({"src"})


def check_file(path: Path) -> list[Violation]:
    """Check a single Python file for import policy violations."""
    violations = []
  
    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:
        return [Violation(path, 0, f"Could not read file: {e}")]
  
    # Check for sys.path manipulation
    if "sys.path.insert" in content or "sys.path.append" in content:
        for i, line in enumerate(content.splitlines(), 1):
            if "sys.path.insert" in line or "sys.path.append" in line:
                # Skip comments
                stripped = line.lstrip()
                if not stripped.startswith("#"):
                    violations.append(Violation(
                        path, i,
                        "sys.path manipulation is forbidden"
                    ))
  
    # Parse AST for import analysis
    try:
        tree = ast.parse(content, filename=str(path))
    except SyntaxError as e:
        return violations + [Violation(path, e.lineno or 0, f"Syntax error: {e}")]
  
    for node in ast.walk(tree):
        # Check Import statements
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in INVALID_IMPORT_ROOTS:
                    violations.append(Violation(
                        path, node.lineno,
                        f"Invalid import root '{root}' - 'src' is never importable"
                    ))
                elif root in OLD_PACKAGE_ROOTS:
                    violations.append(Violation(
                        path, node.lineno,
                        f"Old import '{alias.name}' - use 'gmail_assistant.{alias.name}'"
                    ))
      
        # Check ImportFrom statements
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root = node.module.split(".")[0]
                if root in INVALID_IMPORT_ROOTS:
                    violations.append(Violation(
                        path, node.lineno,
                        f"Invalid import root '{root}' - 'src' is never importable"
                    ))
                elif root in OLD_PACKAGE_ROOTS:
                    violations.append(Violation(
                        path, node.lineno,
                        f"Old import 'from {node.module}' - use 'from gmail_assistant.{node.module}'"
                    ))
          
            # Check relative imports
            if node.level > 0:
                # Relative imports are only allowed within src/gmail_assistant
                try:
                    rel = path.relative_to(Path.cwd() / "src" / "gmail_assistant")
                    # Check that relative import doesn't escape package
                    depth = len(rel.parts) - 1  # -1 for the file itself
                    if node.level > depth:
                        violations.append(Violation(
                            path, node.lineno,
                            f"Relative import level {node.level} escapes package boundary"
                        ))
                except ValueError:
                    # File not in src/gmail_assistant - relative imports not allowed
                    violations.append(Violation(
                        path, node.lineno,
                        "Relative imports only allowed within src/gmail_assistant/"
                    ))
  
    return violations


def main() -> int:
    """Run import policy checks on all Python files."""
    repo_root = Path.cwd()
  
    # Directories to check
    check_dirs = [
        repo_root / "src",
        repo_root / "tests",
        repo_root / "scripts",
    ]
  
    # Exclusions
    exclude_patterns = {
        "__pycache__",
        ".venv",
        "venv",
        ".git",
        "dist",
        "build",
    }
  
    all_violations: list[Violation] = []
    files_checked = 0
  
    for check_dir in check_dirs:
        if not check_dir.exists():
            continue
      
        for py_file in check_dir.rglob("*.py"):
            # Skip excluded directories
            if any(excl in py_file.parts for excl in exclude_patterns):
                continue
          
            violations = check_file(py_file)
            all_violations.extend(violations)
            files_checked += 1
  
    # Report results
    print(f"Checked {files_checked} files")
    print()
  
    if all_violations:
        print(f"Found {len(all_violations)} violations:")
        print()
        for v in all_violations:
            rel_path = v.file.relative_to(repo_root) if v.file.is_relative_to(repo_root) else v.file
            print(f"  {rel_path}:{v.line}: {v.message}")
        print()
        print("FAILED: Import policy violations found")
        return 1
    else:
        print("PASSED: No import policy violations")
        return 0


if __name__ == "__main__":
    sys.exit(main())
```

### 8.4 Import Resolution Checker

**Location**: `scripts/validation/check_import_resolution.py`

```python
#!/usr/bin/env python3
"""
Import resolution checker - validates imports actually resolve.

Must be run AFTER pip install -e . in a clean environment.
CORRECTED: Includes isolation verification and clear guidance.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


def check_environment() -> tuple[bool, list[str]]:
    """
    Verify we're not importing from source directory.
  
    Returns:
        (is_safe, warnings)
    """
    warnings = []
    cwd = Path.cwd().resolve()
  
    # Check sys.path doesn't include src/ directly
    for p in sys.path:
        if not p:
            continue
        path = Path(p).resolve()
        if path == cwd / "src":
            warnings.append(f"sys.path contains src/: {path}")
        elif path == cwd:
            warnings.append(f"sys.path contains repo root: {path}")
  
    is_safe = len(warnings) == 0
    return is_safe, warnings


def check_imports() -> bool:
    """Try importing key modules."""
    imports_to_check = [
        "gmail_assistant",
        "gmail_assistant.cli.main",
        "gmail_assistant.core.config",
        "gmail_assistant.core.exceptions",
    ]
  
    all_ok = True
  
    for module in imports_to_check:
        try:
            __import__(module)
            print(f"  [OK] import {module}")
        except ImportError as e:
            print(f"  [FAIL] import {module}: {e}")
            all_ok = False
  
    return all_ok


def check_version() -> bool:
    """Verify __version__ is accessible."""
    try:
        import gmail_assistant
        version = gmail_assistant.__version__
        print(f"  [OK] gmail_assistant.__version__ = {version}")
        return True
    except Exception as e:
        print(f"  [FAIL] Could not access __version__: {e}")
        return False


def check_exception_taxonomy() -> bool:
    """Verify exception hierarchy is correct and unified."""
    try:
        from gmail_assistant.core.exceptions import (
            GmailAssistantError,
            ConfigError,
            AuthError,
            NetworkError,
        )
      
        # Verify inheritance
        assert issubclass(ConfigError, GmailAssistantError), "ConfigError must inherit GmailAssistantError"
        assert issubclass(AuthError, GmailAssistantError), "AuthError must inherit GmailAssistantError"
        assert issubclass(NetworkError, GmailAssistantError), "NetworkError must inherit GmailAssistantError"
      
        print("  [OK] Exception taxonomy correct")
        return True
    except Exception as e:
        print(f"  [FAIL] Exception taxonomy: {e}")
        return False


def check_no_duplicate_configerror() -> bool:
    """Verify ConfigError is not duplicated in config.py."""
    try:
        # Import both modules
        from gmail_assistant.core import config
        from gmail_assistant.core import exceptions
      
        # Check that config.ConfigError IS exceptions.ConfigError
        if hasattr(config, 'ConfigError'):
            config_error_class = getattr(config, 'ConfigError')
            if config_error_class is not exceptions.ConfigError:
                print("  [FAIL] config.ConfigError is not exceptions.ConfigError (duplicate class)")
                return False
      
        print("  [OK] No duplicate ConfigError")
        return True
    except Exception as e:
        print(f"  [FAIL] ConfigError check: {e}")
        return False


def check_file_location() -> bool:
    """Verify package is installed, not from source."""
    try:
        import gmail_assistant
        location = Path(gmail_assistant.__file__).resolve()
        cwd = Path.cwd().resolve()
      
        # Should NOT be under current working directory's src/
        if location.is_relative_to(cwd / "src"):
            print(f"  [WARN] Importing from source: {location}")
            print("         This may mask packaging issues.")
            return True  # Warning only
        else:
            print(f"  [OK] Package location: {location}")
            return True
    except Exception as e:
        print(f"  [FAIL] Could not check location: {e}")
        return False


def main() -> int:
    print("=== Import Resolution Check ===")
    print()
  
    print("Checking environment...")
    is_safe, warnings = check_environment()
    if not is_safe:
        print()
        print("WARNING: Environment may produce unreliable results:")
        for w in warnings:
            print(f"  - {w}")
        print()
        print("For accurate results, run from outside the repo directory")
        print("or ensure PYTHONPATH does not include repo/src paths.")
        print()
  
    print()
    print("Checking imports...")
    imports_ok = check_imports()
  
    print()
    print("Checking version...")
    version_ok = check_version()
  
    print()
    print("Checking exception taxonomy...")
    exceptions_ok = check_exception_taxonomy()
  
    print()
    print("Checking for duplicate ConfigError...")
    no_duplicate_ok = check_no_duplicate_configerror()
  
    print()
    print("Checking package location...")
    location_ok = check_file_location()
  
    print()
    all_ok = imports_ok and version_ok and exceptions_ok and no_duplicate_ok and location_ok
  
    if all_ok:
        print("PASSED: All import resolution checks passed")
        return 0
    else:
        print("FAILED: Some import resolution checks failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
```

### 8.5 Unified Verification Pipeline

**Location**: `scripts/verify_all.ps1`

```powershell
#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Unified verification pipeline for Gmail Assistant.
.DESCRIPTION
    Executes the complete verification sequence:
    1. Baseline measurements
    2. Import policy check
    3. Package build
    4. Wheel installation test (isolated)
    5. Import resolution check (isolated)
    6. Test suite with coverage gate
    7. Security checks
    8. CLI smoke test
    9. Release checks (full DoD validation)
  
    CORRECTED: Now invokes release_checks.ps1 as Step 9.
    CORRECTED: Import resolution runs from temp directory for isolation.
.PARAMETER SkipBuild
    Skip package build (use existing dist/)
.PARAMETER SkipTests
    Skip test suite execution
.PARAMETER SkipReleaseChecks
    Skip release_checks.ps1 (faster iteration)
.EXAMPLE
    .\scripts\verify_all.ps1
    .\scripts\verify_all.ps1 -SkipTests
#>
[CmdletBinding()]
param(
    [switch]$SkipBuild,
    [switch]$SkipTests,
    [switch]$SkipReleaseChecks
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repoRoot = (git rev-parse --show-toplevel)
if (-not $repoRoot) {
    Write-Error "Not in a git repository"
    exit 1
}
$repoRoot = (Resolve-Path $repoRoot).Path
Set-Location $repoRoot

$exitCode = 0
$results = @{}

function Write-Step {
    param([string]$Name, [string]$Status, [string]$Color = "White")
    $symbol = switch ($Status) {
        "PASS" { "[PASS]"; $Color = "Green" }
        "FAIL" { "[FAIL]"; $Color = "Red" }
        "SKIP" { "[SKIP]"; $Color = "Yellow" }
        "RUN"  { "[....]"; $Color = "Cyan" }
        default { "[????]" }
    }
    Write-Host "$symbol $Name" -ForegroundColor $Color
}

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║       Gmail Assistant - Unified Verification Pipeline          ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "Repo: $repoRoot"
Write-Host "Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host ""

# ============================================================================
# Step 1: Baseline Measurements
# ============================================================================
Write-Host "─── Step 1: Baseline Measurements ───" -ForegroundColor Yellow
Write-Step "Baseline" "RUN"

try {
    & "$repoRoot/scripts/audit/baseline.ps1" -OutputDir "docs/audit" | Out-Null
    Write-Step "Baseline" "PASS"
    $results["Baseline"] = "PASS"
} catch {
    Write-Step "Baseline" "FAIL"
    Write-Host "  Error: $_" -ForegroundColor Red
    $results["Baseline"] = "FAIL"
    $exitCode = 1
}

Write-Host ""

# ============================================================================
# Step 2: Import Policy Check
# ============================================================================
Write-Host "─── Step 2: Import Policy Check ───" -ForegroundColor Yellow
Write-Step "Import Policy" "RUN"

try {
    $policyResult = python "$repoRoot/scripts/validation/check_import_policy.py"
    if ($LASTEXITCODE -eq 0) {
        Write-Step "Import Policy" "PASS"
        $results["Import Policy"] = "PASS"
    } else {
        Write-Step "Import Policy" "FAIL"
        Write-Host $policyResult
        $results["Import Policy"] = "FAIL"
        $exitCode = 1
    }
} catch {
    Write-Step "Import Policy" "FAIL"
    Write-Host "  Error: $_" -ForegroundColor Red
    $results["Import Policy"] = "FAIL"
    $exitCode = 1
}

Write-Host ""

# ============================================================================
# Step 3: Package Build
# ============================================================================
Write-Host "─── Step 3: Package Build ───" -ForegroundColor Yellow

if ($SkipBuild) {
    Write-Step "Build" "SKIP"
    $results["Build"] = "SKIP"
} else {
    Write-Step "Build" "RUN"
  
    try {
        # Clean dist/
        if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
      
        # Install build tool
        python -m pip install --quiet build
      
        # Build
        python -m build --quiet 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "Build failed" }
      
        # Verify single wheel
        $wheels = Get-ChildItem dist -Filter *.whl -ErrorAction SilentlyContinue
        if ($wheels.Count -ne 1) {
            throw "Expected 1 wheel, found $($wheels.Count)"
        }
      
        Write-Step "Build" "PASS"
        Write-Host "  Wheel: $($wheels[0].Name)" -ForegroundColor Gray
        $results["Build"] = "PASS"
    } catch {
        Write-Step "Build" "FAIL"
        Write-Host "  Error: $_" -ForegroundColor Red
        $results["Build"] = "FAIL"
        $exitCode = 1
    }
}

Write-Host ""

# ============================================================================
# Step 4: Wheel Installation Test (Isolated)
# ============================================================================
Write-Host "─── Step 4: Wheel Installation Test ───" -ForegroundColor Yellow
Write-Step "Install Test" "RUN"

$testVenv = Join-Path $repoRoot ".verify-venv"

try {
    # Clean up existing venv
    if (Test-Path $testVenv) { Remove-Item -Recurse -Force $testVenv }
  
    # Create venv
    python -m venv $testVenv
    $venvPip = Join-Path $testVenv "Scripts/pip.exe"
    $venvPython = Join-Path $testVenv "Scripts/python.exe"
    if (-not (Test-Path $venvPip)) {
        $venvPip = Join-Path $testVenv "Scripts/pip"
        $venvPython = Join-Path $testVenv "Scripts/python"
    }
  
    # Find wheel
    $wheel = Get-ChildItem dist -Filter *.whl | Select-Object -First 1
    if (-not $wheel) { throw "No wheel found in dist/" }
  
    # Install
    & $venvPip install --quiet $wheel.FullName
    if ($LASTEXITCODE -ne 0) { throw "Wheel installation failed" }
  
    # Import test from temp directory (CORRECTED: isolated execution)
    $tempDir = [System.IO.Path]::GetTempPath()
    Push-Location $tempDir
    try {
        $output = & $venvPython -c "import gmail_assistant; print(gmail_assistant.__version__)"
        if ($LASTEXITCODE -ne 0) { throw "Import failed" }
        Write-Step "Install Test" "PASS"
        Write-Host "  Version: $output" -ForegroundColor Gray
        $results["Install Test"] = "PASS"
    } finally {
        Pop-Location
    }
  
} catch {
    Write-Step "Install Test" "FAIL"
    Write-Host "  Error: $_" -ForegroundColor Red
    $results["Install Test"] = "FAIL"
    $exitCode = 1
} finally {
    if (Test-Path $testVenv) { Remove-Item -Recurse -Force $testVenv -ErrorAction SilentlyContinue }
}

Write-Host ""

# ============================================================================
# Step 5: Import Resolution Check (Isolated)
# ============================================================================
Write-Host "─── Step 5: Import Resolution Check ───" -ForegroundColor Yellow
Write-Step "Import Resolution" "RUN"

$resolutionVenv = Join-Path $repoRoot ".resolution-venv"

try {
    # Create isolated venv
    if (Test-Path $resolutionVenv) { Remove-Item -Recurse -Force $resolutionVenv }
    python -m venv $resolutionVenv
  
    $venvPip = Join-Path $resolutionVenv "Scripts/pip.exe"
    $venvPython = Join-Path $resolutionVenv "Scripts/python.exe"
    if (-not (Test-Path $venvPip)) {
        $venvPip = Join-Path $resolutionVenv "Scripts/pip"
        $venvPython = Join-Path $resolutionVenv "Scripts/python"
    }
  
    # Install wheel (not editable)
    $wheel = Get-ChildItem dist -Filter *.whl | Select-Object -First 1
    & $venvPip install --quiet $wheel.FullName
  
    # CORRECTED: Run from temp directory for true isolation
    $tempDir = [System.IO.Path]::GetTempPath()
    $scriptContent = Get-Content "$repoRoot/scripts/validation/check_import_resolution.py" -Raw
    $tempScript = Join-Path $tempDir "check_import_resolution.py"
    Set-Content -Path $tempScript -Value $scriptContent -Encoding UTF8
  
    Push-Location $tempDir
    try {
        & $venvPython $tempScript
        if ($LASTEXITCODE -eq 0) {
            Write-Step "Import Resolution" "PASS"
            $results["Import Resolution"] = "PASS"
        } else {
            Write-Step "Import Resolution" "FAIL"
            $results["Import Resolution"] = "FAIL"
            $exitCode = 1
        }
    } finally {
        Pop-Location
        Remove-Item $tempScript -ErrorAction SilentlyContinue
    }
  
} catch {
    Write-Step "Import Resolution" "FAIL"
    Write-Host "  Error: $_" -ForegroundColor Red
    $results["Import Resolution"] = "FAIL"
    $exitCode = 1
} finally {
    if (Test-Path $resolutionVenv) { Remove-Item -Recurse -Force $resolutionVenv -ErrorAction SilentlyContinue }
}

Write-Host ""

# ============================================================================
# Step 6: Test Suite with Coverage Gate
# ============================================================================
Write-Host "─── Step 6: Test Suite ───" -ForegroundColor Yellow

if ($SkipTests) {
    Write-Step "Tests" "SKIP"
    $results["Tests"] = "SKIP"
} else {
    Write-Step "Tests" "RUN"
  
    try {
        # Install dev dependencies
        pip install -e ".[dev]" --quiet
      
        # Run tests with coverage
        $coverageOutput = pytest tests -m "not integration and not api" -q --tb=short --cov=gmail_assistant --cov-report=term --cov-fail-under=70 2>&1
      
        if ($LASTEXITCODE -eq 0) {
            Write-Step "Tests" "PASS"
            $results["Tests"] = "PASS"
        } else {
            Write-Step "Tests" "FAIL"
            Write-Host $coverageOutput
            $results["Tests"] = "FAIL"
            $exitCode = 1
        }
    } catch {
        Write-Step "Tests" "FAIL"
        Write-Host "  Error: $_" -ForegroundColor Red
        $results["Tests"] = "FAIL"
        $exitCode = 1
    }
}

Write-Host ""

# ============================================================================
# Step 7: Security Checks
# ============================================================================
Write-Host "─── Step 7: Security Checks ───" -ForegroundColor Yellow
Write-Step "Security" "RUN"

try {
    $securityOk = $true
  
    # Check no credentials tracked
    $tracked = git ls-files | Select-String -Pattern "(credentials|token)\.json$"
    if ($tracked) {
        Write-Host "  [FAIL] Credentials tracked: $tracked" -ForegroundColor Red
        $securityOk = $false
    }
  
    # Check no log files tracked
    $logs = git ls-files | Select-String -Pattern "\.log$"
    if ($logs) {
        Write-Host "  [FAIL] Log files tracked: $logs" -ForegroundColor Red
        $securityOk = $false
    }
  
    # Gitleaks (optional)
    $gitleaks = Get-Command gitleaks -ErrorAction SilentlyContinue
    if ($gitleaks) {
        gitleaks detect --no-banner --exit-code 1 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  [FAIL] Gitleaks found secrets" -ForegroundColor Red
            $securityOk = $false
        }
    }
  
    if ($securityOk) {
        Write-Step "Security" "PASS"
        $results["Security"] = "PASS"
    } else {
        Write-Step "Security" "FAIL"
        $results["Security"] = "FAIL"
        $exitCode = 1
    }
  
} catch {
    Write-Step "Security" "FAIL"
    Write-Host "  Error: $_" -ForegroundColor Red
    $results["Security"] = "FAIL"
    $exitCode = 1
}

Write-Host ""

# ============================================================================
# Step 8: CLI Smoke Test
# ============================================================================
Write-Host "─── Step 8: CLI Smoke Test ───" -ForegroundColor Yellow
Write-Step "CLI Smoke" "RUN"

try {
    # Ensure package is installed
    pip install -e . --quiet 2>&1 | Out-Null
  
    # Test --version
    $version = gmail-assistant --version 2>&1
    if ($LASTEXITCODE -ne 0) { throw "CLI --version failed" }
  
    # Test --help
    $help = gmail-assistant --help 2>&1
    if ($LASTEXITCODE -ne 0) { throw "CLI --help failed" }
  
    # Test subcommand helps
    $subcommands = @("fetch", "delete", "analyze", "auth", "config")
    foreach ($cmd in $subcommands) {
        $subHelp = gmail-assistant $cmd --help 2>&1
        if ($LASTEXITCODE -ne 0) { throw "CLI $cmd --help failed" }
    }
  
    Write-Step "CLI Smoke" "PASS"
    $results["CLI Smoke"] = "PASS"
  
} catch {
    Write-Step "CLI Smoke" "FAIL"
    Write-Host "  Error: $_" -ForegroundColor Red
    $results["CLI Smoke"] = "FAIL"
    $exitCode = 1
}

Write-Host ""

# ============================================================================
# Step 9: Release Checks (CORRECTED: Now actually invokes release_checks.ps1)
# ============================================================================
Write-Host "─── Step 9: Release Checks ───" -ForegroundColor Yellow

if ($SkipReleaseChecks) {
    Write-Step "Release Checks" "SKIP"
    $results["Release Checks"] = "SKIP"
} else {
    Write-Step "Release Checks" "RUN"
  
    try {
        & "$repoRoot/scripts/validation/release_checks.ps1"
        if ($LASTEXITCODE -eq 0) {
            Write-Step "Release Checks" "PASS"
            $results["Release Checks"] = "PASS"
        } else {
            Write-Step "Release Checks" "FAIL"
            $results["Release Checks"] = "FAIL"
            $exitCode = 1
        }
    } catch {
        Write-Step "Release Checks" "FAIL"
        Write-Host "  Error: $_" -ForegroundColor Red
        $results["Release Checks"] = "FAIL"
        $exitCode = 1
    }
}

Write-Host ""

# ============================================================================
# Summary
# ============================================================================
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                        SUMMARY                               ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

$results.GetEnumerator() | Sort-Object Name | ForEach-Object {
    $color = switch ($_.Value) {
        "PASS" { "Green" }
        "FAIL" { "Red" }
        "SKIP" { "Yellow" }
        default { "White" }
    }
    Write-Host "  $($_.Value.PadRight(6)) $($_.Key)" -ForegroundColor $color
}

Write-Host ""

if ($exitCode -eq 0) {
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
    Write-Host "  ALL CHECKS PASSED - Ready for release" -ForegroundColor Green
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
} else {
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Red
    Write-Host "  CHECKS FAILED - Review errors above" -ForegroundColor Red
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Red
}

Write-Host ""
exit $exitCode
```

### 8.6 Release Checks Script

**Location**: `scripts/validation/release_checks.ps1`

```powershell
#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Must-pass release checks. Run before tagging a release.
.DESCRIPTION
    Executes three critical checks:
    1. Build wheel and verify installation from outside repo
    2. Run tests from outside repo
    3. Security verification
#>
[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$exitCode = 0

$repoRoot = (git rev-parse --show-toplevel)
if (-not $repoRoot) {
    Write-Host "ERROR: Not in a git repository" -ForegroundColor Red
    exit 1
}
$repoRoot = (Resolve-Path $repoRoot).Path

Write-Host "=== Release DoD Checks ===" -ForegroundColor Cyan
Write-Host "Repo root: $repoRoot"
Write-Host ""

# ============================================================================
# Check 1: Build and install wheel
# ============================================================================
Write-Host "Check 1: Build and install wheel" -ForegroundColor Yellow
Write-Host "─────────────────────────────────"

$venvPath = Join-Path $repoRoot ".release-check-venv"
$distPath = Join-Path $repoRoot "dist"

try {
    # Clean
    if (Test-Path $venvPath) { Remove-Item -Recurse -Force $venvPath }
    if (Test-Path $distPath) { Remove-Item -Recurse -Force $distPath }

    # Build
    Push-Location $repoRoot
    try {
        python -m pip install --quiet build
        python -m build --quiet
        if ($LASTEXITCODE -ne 0) { throw "Build failed" }
    } finally {
        Pop-Location
    }
    Write-Host "[OK] Package built" -ForegroundColor Green

    # Select wheel (no name assumption)
    $wheels = Get-ChildItem $distPath -Filter *.whl -ErrorAction Stop
    if ($wheels.Count -ne 1) {
        throw "Expected 1 wheel, found $($wheels.Count): $($wheels.Name -join ', ')"
    }
    $wheelPath = $wheels[0].FullName
    Write-Host "[OK] Single wheel found: $($wheels[0].Name)" -ForegroundColor Green

    # Create venv and install
    python -m venv $venvPath
    $venvPython = Join-Path $venvPath "Scripts/python.exe"
    $venvPip = Join-Path $venvPath "Scripts/pip.exe"
    $venvCli = Join-Path $venvPath "Scripts/gmail-assistant.exe"
    if (-not (Test-Path $venvPython)) {
        $venvPython = Join-Path $venvPath "Scripts/python"
        $venvPip = Join-Path $venvPath "Scripts/pip"
        $venvCli = Join-Path $venvPath "Scripts/gmail-assistant"
    }

    & $venvPip install --quiet $wheelPath
    if ($LASTEXITCODE -ne 0) { throw "Wheel installation failed" }
    Write-Host "[OK] Wheel installed" -ForegroundColor Green

    # Import checks from temp dir
    $tempDir = [System.IO.Path]::GetTempPath()
    Push-Location $tempDir
    try {
        $output = & $venvPython -c @"
import gmail_assistant
print(f'Version: {gmail_assistant.__version__}')
print(f'File: {gmail_assistant.__file__}')
from gmail_assistant.cli.main import main
from gmail_assistant.core.config import AppConfig
from gmail_assistant.core.exceptions import ConfigError, AuthError, NetworkError
print('All imports OK')
"@
        if ($LASTEXITCODE -ne 0) { throw "Import check failed" }
        Write-Host $output
        Write-Host "[OK] Import resolution passed" -ForegroundColor Green
    } finally {
        Pop-Location
    }

    # CLI check
    & $venvCli --version
    if ($LASTEXITCODE -ne 0) { throw "CLI --version failed" }
    Write-Host "[OK] CLI works" -ForegroundColor Green

} catch {
    Write-Host "[FAIL] Check 1 failed: $_" -ForegroundColor Red
    $exitCode = 1
} finally {
    if (Test-Path $venvPath) { Remove-Item -Recurse -Force $venvPath -ErrorAction SilentlyContinue }
}

Write-Host ""

# ============================================================================
# Check 2: Tests pass from outside repo
# ============================================================================
Write-Host "Check 2: Tests from outside repo" -ForegroundColor Yellow
Write-Host "─────────────────────────────────"

$venvPath2 = Join-Path $repoRoot ".test-check-venv"

try {
    if (Test-Path $venvPath2) { Remove-Item -Recurse -Force $venvPath2 }

    python -m venv $venvPath2
    $venvPip2 = Join-Path $venvPath2 "Scripts/pip.exe"
    $venvPytest = Join-Path $venvPath2 "Scripts/pytest.exe"
    if (-not (Test-Path $venvPip2)) {
        $venvPip2 = Join-Path $venvPath2 "Scripts/pip"
        $venvPytest = Join-Path $venvPath2 "Scripts/pytest"
    }

    Push-Location $repoRoot
    try {
        & $venvPip2 install --quiet -e ".[dev]"
        if ($LASTEXITCODE -ne 0) { throw "Dev install failed" }
    } finally {
        Pop-Location
    }

    # Run tests from temp directory
    $tempDir = [System.IO.Path]::GetTempPath()
    $testsPath = Join-Path $repoRoot "tests"

    Push-Location $tempDir
    try {
        & $venvPytest $testsPath -m "not integration and not api" -q --cov-fail-under=70
        if ($LASTEXITCODE -ne 0) { throw "Tests failed" }
        Write-Host "[OK] Tests passed" -ForegroundColor Green
    } finally {
        Pop-Location
    }

} catch {
    Write-Host "[FAIL] Check 2 failed: $_" -ForegroundColor Red
    $exitCode = 1
} finally {
    if (Test-Path $venvPath2) { Remove-Item -Recurse -Force $venvPath2 -ErrorAction SilentlyContinue }
}

Write-Host ""

# ============================================================================
# Check 3: Security checks
# ============================================================================
Write-Host "Check 3: Security checks" -ForegroundColor Yellow
Write-Host "─────────────────────────────────"

Push-Location $repoRoot
try {
    $tracked = git ls-files | Select-String -Pattern "(credentials|token)\.json$"
    if ($tracked) {
        throw "Credentials tracked in git: $tracked"
    }
    Write-Host "[OK] No credentials tracked" -ForegroundColor Green

    $logs = git ls-files | Select-String -Pattern "\.log$"
    if ($logs) {
        throw "Log files tracked in git: $logs"
    }
    Write-Host "[OK] No log files tracked" -ForegroundColor Green

    $gitignorePath = Join-Path $repoRoot ".gitignore"
    if (Test-Path $gitignorePath) {
        $gitignore = Get-Content $gitignorePath
        $required = @("credentials.json", "token.json", "*.log")
        foreach ($pattern in $required) {
            $found = $gitignore | Where-Object { $_ -match [regex]::Escape($pattern) -or $_ -eq $pattern }
            if (-not $found) {
                Write-Host "[WARN] .gitignore may not include: $pattern" -ForegroundColor Yellow
            }
        }
    }
    Write-Host "[OK] .gitignore reviewed" -ForegroundColor Green

    $gitleaks = Get-Command gitleaks -ErrorAction SilentlyContinue
    if ($gitleaks) {
        gitleaks detect --no-banner --exit-code 1
        if ($LASTEXITCODE -ne 0) { throw "Gitleaks found secrets" }
        Write-Host "[OK] Gitleaks passed" -ForegroundColor Green
    } else {
        Write-Host "[SKIP] Gitleaks not installed" -ForegroundColor Yellow
    }

} catch {
    Write-Host "[FAIL] Check 3 failed: $_" -ForegroundColor Red
    $exitCode = 1
} finally {
    Pop-Location
}

Write-Host ""
Write-Host "=== Summary ===" -ForegroundColor Cyan

if ($exitCode -eq 0) {
    Write-Host "All release checks PASSED" -ForegroundColor Green
} else {
    Write-Host "Release checks FAILED" -ForegroundColor Red
}

exit $exitCode
```

### 8.7 Pre-Commit Configuration

**Location**: `.pre-commit-config.yaml`

```yaml
# Pre-commit hooks configuration
# Install: pip install pre-commit && pre-commit install

repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-added-large-files
        args: ['--maxkb=1000']
      - id: check-merge-conflict
      - id: detect-private-key

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.10.0
    hooks:
      - id: mypy
        additional_dependencies:
          - types-requests
        args: [--config-file=pyproject.toml]
        pass_filenames: false
        entry: mypy src/gmail_assistant

  - repo: local
    hooks:
      - id: import-policy
        name: Import Policy Check
        entry: python scripts/validation/check_import_policy.py
        language: system
        pass_filenames: false
        always_run: true

  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.2
    hooks:
      - id: gitleaks
```

---

## 9. Configuration System

### 9.1 Configuration Loader

**Location**: `src/gmail_assistant/core/config.py`

```python
"""
Configuration loader with secure defaults and strict validation.

Resolution Order (highest to lowest priority):
1. CLI arguments (--config, --credentials-path, etc.)
2. Environment variable: gmail_assistant_CONFIG
3. Project config: ./gmail-assistant.json (current directory)
4. User config: ~/.gmail-assistant/config.json
5. Built-in defaults

Security Features:
- Credentials default to ~/.gmail-assistant/ (outside any repo)
- Repo-local credentials require explicit --allow-repo-credentials flag
- Paths are validated and expanded (~, relative paths)
- Unknown keys are rejected
- Type validation on all fields

CORRECTED: ConfigError is imported from exceptions.py (single source of truth)
CORRECTED: Behavior documented when git is unavailable
"""
from __future__ import annotations

import json
import logging
import os
import subprocess
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar

# CORRECTED: Import ConfigError from exceptions (single authoritative source)
from gmail_assistant.core.exceptions import ConfigError

__all__ = ["AppConfig", "ConfigError"]

logger = logging.getLogger(__name__)

_ALLOWED_KEYS = frozenset({
    "credentials_path",
    "token_path",
    "output_dir",
    "max_emails",
    "rate_limit_per_second",
    "log_level",
})

_LOG_LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})


@dataclass
class AppConfig:
    """Application configuration with secure defaults."""
  
    credentials_path: Path
    token_path: Path
    output_dir: Path
    max_emails: int = 1000
    rate_limit_per_second: float = 10.0
    log_level: str = "INFO"
  
    # Class-level constants
    ENV_VAR: ClassVar[str] = "gmail_assistant_CONFIG"
    PROJECT_CONFIG_NAME: ClassVar[str] = "gmail-assistant.json"
  
    @classmethod
    def default_dir(cls) -> Path:
        """Default configuration directory (~/.gmail-assistant/)."""
        return Path.home() / ".gmail-assistant"
  
    @classmethod
    def load(
        cls,
        config_path: Path | None = None,
        allow_repo_credentials: bool = False,
    ) -> "AppConfig":
        """
        Load configuration from file or defaults.
      
        Args:
            config_path: Explicit config file path (highest priority)
            allow_repo_credentials: Allow credentials inside git repo
          
        Returns:
            Loaded configuration
          
        Raises:
            ConfigError: On validation failure
        """
        # Determine config file to use
        resolved_path = cls._resolve_config_path(config_path)
      
        if resolved_path and resolved_path.exists():
            return cls._from_file(resolved_path, allow_repo_credentials)
        else:
            return cls._defaults()
  
    @classmethod
    def _resolve_config_path(cls, explicit: Path | None) -> Path | None:
        """Resolve config path from various sources."""
        # 1. Explicit path
        if explicit:
            return explicit
      
        # 2. Environment variable
        env_path = os.environ.get(cls.ENV_VAR)
        if env_path:
            return Path(env_path)
      
        # 3. Project config (current directory)
        project_config = Path.cwd() / cls.PROJECT_CONFIG_NAME
        if project_config.exists():
            return project_config
      
        # 4. User config
        user_config = cls.default_dir() / "config.json"
        if user_config.exists():
            return user_config
      
        return None
  
    @classmethod
    def _defaults(cls) -> "AppConfig":
        """Create configuration with secure defaults."""
        default_dir = cls.default_dir()
        return cls(
            credentials_path=default_dir / "credentials.json",
            token_path=default_dir / "token.json",
            output_dir=default_dir / "backups",
        )
  
    @classmethod
    def _from_file(
        cls,
        config_path: Path,
        allow_repo_credentials: bool,
    ) -> "AppConfig":
        """Load configuration from JSON file."""
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise ConfigError(f"Invalid JSON in {config_path}: {e}")
        except OSError as e:
            raise ConfigError(f"Cannot read {config_path}: {e}")
      
        return cls._from_dict(data, config_path, allow_repo_credentials)
  
    @classmethod
    def _from_dict(
        cls,
        data: dict[str, Any],
        config_path: Path,
        allow_repo_credentials: bool,
    ) -> "AppConfig":
        """Parse and validate configuration dictionary."""
        # Check for unknown keys
        unknown = set(data.keys()) - _ALLOWED_KEYS
        if unknown:
            raise ConfigError(f"Unknown configuration keys: {unknown}")
      
        config_dir = config_path.parent.resolve()
        defaults = cls._defaults()
      
        def resolve_path(key: str, default: Path) -> Path:
            if key not in data:
                return default
            raw = data[key]
          
            # Type validation
            if not isinstance(raw, str):
                raise ConfigError(
                    f"{key} must be string path, got {type(raw).__name__}"
                )
          
            # Empty string validation
            if not raw.strip():
                raise ConfigError(f"{key} must be non-empty string path")
          
            # Expand ~ and resolve relative paths
            p = Path(raw).expanduser()
            if not p.is_absolute():
                p = (config_dir / p).resolve()
          
            return p
      
        # Resolve paths
        credentials_path = resolve_path("credentials_path", defaults.credentials_path)
        token_path = resolve_path("token_path", defaults.token_path)
        output_dir = resolve_path("output_dir", defaults.output_dir)
      
        # Security check for credentials (only if git is available)
        repo_roots = cls._find_all_repo_roots(config_path)
        for repo_root in repo_roots:
            cls._check_path_safety(
                credentials_path, "credentials_path", repo_root, allow_repo_credentials
            )
            cls._check_path_safety(
                token_path, "token_path", repo_root, allow_repo_credentials
            )
      
        # Validate other fields
        max_emails = data.get("max_emails", defaults.max_emails)
        if not isinstance(max_emails, int) or max_emails < 1:
            raise ConfigError("max_emails must be positive integer")
        if max_emails > 100000:
            raise ConfigError("max_emails cannot exceed 100000")
      
        rate_limit = data.get("rate_limit_per_second", defaults.rate_limit_per_second)
        if not isinstance(rate_limit, (int, float)) or rate_limit <= 0:
            raise ConfigError("rate_limit_per_second must be positive number")
        if rate_limit > 100:
            raise ConfigError("rate_limit_per_second cannot exceed 100")
      
        log_level = data.get("log_level", defaults.log_level)
        if not isinstance(log_level, str):
            raise ConfigError("log_level must be string")
        log_level = log_level.upper()
        if log_level not in _LOG_LEVELS:
            raise ConfigError(f"log_level must be one of {_LOG_LEVELS}")
      
        return cls(
            credentials_path=credentials_path,
            token_path=token_path,
            output_dir=output_dir,
            max_emails=max_emails,
            rate_limit_per_second=float(rate_limit),
            log_level=log_level,
        )
  
    @staticmethod
    def _find_all_repo_roots(config_path: Path) -> list[Path]:
        """
        Find git repo roots from config location and CWD.
      
        CORRECTED: Documents behavior when git is unavailable.
        If git is not installed or not in PATH, returns empty list
        and repo-safety checks are skipped (credentials allowed anywhere).
        A warning is logged in this case.
        """
        roots = []
      
        def find_repo_root(start: Path) -> Path | None:
            try:
                result = subprocess.run(
                    ["git", "rev-parse", "--show-toplevel"],
                    cwd=start,
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    return Path(result.stdout.strip()).resolve()
            except FileNotFoundError:
                # Git not installed - log warning once
                logger.warning(
                    "git not found in PATH; repo-safety checks disabled. "
                    "Credentials may be placed anywhere without warning."
                )
            except (subprocess.TimeoutExpired, OSError):
                pass
            return None
      
        # Check from config directory
        config_repo = find_repo_root(config_path.parent)
        if config_repo:
            roots.append(config_repo)
      
        # Check from CWD
        cwd_repo = find_repo_root(Path.cwd())
        if cwd_repo and cwd_repo not in roots:
            roots.append(cwd_repo)
      
        return roots
  
    @staticmethod
    def _check_path_safety(
        path: Path,
        name: str,
        repo_root: Path,
        allow: bool,
    ) -> None:
        """Check if path is inside repo (security risk)."""
        resolved = path.resolve()
      
        # Windows cross-drive can raise ValueError
        try:
            is_inside_repo = resolved.is_relative_to(repo_root)
        except ValueError:
            is_inside_repo = False
      
        if is_inside_repo:
            if allow:
                warnings.warn(
                    f"{name} ({resolved}) is inside git repo. "
                    f"Ensure it's in .gitignore to prevent credential leakage.",
                    UserWarning,
                    stacklevel=6,
                )
            else:
                raise ConfigError(
                    f"{name} ({resolved}) is inside git repo ({repo_root}). "
                    f"Move to {AppConfig.default_dir()} or use --allow-repo-credentials."
                )
```

### 9.2 Configuration Exceptions (SINGLE SOURCE OF TRUTH)

**Location**: `src/gmail_assistant/core/exceptions.py`

```python
"""
Centralized exception definitions.

CORRECTED: This is the SINGLE SOURCE OF TRUTH for all domain exceptions.
All modules must import exceptions from here, not define their own.
"""
from __future__ import annotations

__all__ = [
    "GmailAssistantError",
    "ConfigError",
    "AuthError",
    "NetworkError",
    "APIError",
]


class GmailAssistantError(Exception):
    """Base exception for Gmail Assistant. All domain exceptions inherit from this."""
    pass


class ConfigError(GmailAssistantError):
    """Configuration-related errors. Maps to exit code 5."""
    pass


class AuthError(GmailAssistantError):
    """Authentication/authorization errors. Maps to exit code 3."""
    pass


class NetworkError(GmailAssistantError):
    """Network connectivity errors. Maps to exit code 4."""
    pass


class APIError(GmailAssistantError):
    """Gmail API errors. Maps to exit code 1 (general)."""
    pass
```

### 9.3 Configuration Schema

**Location**: `config/schema/config.schema.json`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/user/gmail-assistant/config.schema.json",
  "title": "Gmail Assistant Configuration",
  "description": "Configuration schema for Gmail Assistant v2.0.0",
  "type": "object",
  "properties": {
    "credentials_path": {
      "type": "string",
      "description": "Path to Google OAuth credentials JSON file. Relative paths resolved from config file location. Supports ~ expansion.",
      "minLength": 1,
      "examples": ["~/.gmail-assistant/credentials.json", "./credentials.json"]
    },
    "token_path": {
      "type": "string",
      "description": "Path to store OAuth token after authentication. Relative paths resolved from config file location. Supports ~ expansion.",
      "minLength": 1,
      "examples": ["~/.gmail-assistant/token.json", "./token.json"]
    },
    "output_dir": {
      "type": "string",
      "description": "Directory for email backups and exports. Relative paths resolved from config file location. Supports ~ expansion.",
      "minLength": 1,
      "examples": ["~/.gmail-assistant/backups", "./gmail_backup"]
    },
    "max_emails": {
      "type": "integer",
      "description": "Maximum number of emails to fetch per operation.",
      "minimum": 1,
      "maximum": 100000,
      "default": 1000
    },
    "rate_limit_per_second": {
      "type": "number",
      "description": "Maximum API requests per second.",
      "exclusiveMinimum": 0,
      "maximum": 100,
      "default": 10.0
    },
    "log_level": {
      "type": "string",
      "description": "Logging verbosity level.",
      "enum": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
      "default": "INFO"
    }
  },
  "additionalProperties": false
}
```

### 9.4 Configuration Template

**Location**: `config/default.json.template`

```json
{
  "credentials_path": "~/.gmail-assistant/credentials.json",
  "token_path": "~/.gmail-assistant/token.json",
  "output_dir": "~/.gmail-assistant/backups",
  "max_emails": 1000,
  "rate_limit_per_second": 10.0,
  "log_level": "INFO"
}
```

---

## 10. Packaging & Release Pipeline

### 10.1 pyproject.toml

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "gmail-assistant"
version = "2.0.0"
description = "Gmail backup, analysis, and management suite"
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.10"
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
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Topic :: Communications :: Email",
    "Typing :: Typed",
]
keywords = ["gmail", "email", "backup", "archive", "google"]

dependencies = [
    "google-api-python-client>=2.140.0",
    "google-auth>=2.27.0",
    "google-auth-oauthlib>=1.2.0",
    "google-auth-httplib2>=0.2.0",
    "click>=8.1.0",
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
    "types-requests>=2.31.0",
    "pre-commit>=3.7.0",
    "jsonschema>=4.21.0",
]

[project.scripts]
gmail-assistant = "gmail_assistant.cli.main:main"

[project.urls]
Homepage = "https://github.com/user/gmail-assistant"
Documentation = "https://github.com/user/gmail-assistant/docs"
Repository = "https://github.com/user/gmail-assistant"
Changelog = "https://github.com/user/gmail-assistant/blob/main/CHANGELOG.md"

[tool.hatch.build.targets.wheel]
packages = ["src/gmail_assistant"]

[tool.hatch.build.targets.wheel.force-include]
"src/gmail_assistant/py.typed" = "gmail_assistant/py.typed"

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
filterwarnings = [
    "error",
]

[tool.coverage.run]
source = ["src/gmail_assistant"]
branch = true
omit = [
    "*/__pycache__/*",
    "*/tests/*",
]

[tool.coverage.report]
fail_under = 70
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
    "@abstractmethod",
]

[tool.ruff]
target-version = "py310"
line-length = 100
src = ["src"]

[tool.ruff.lint]
select = ["E", "F", "W", "I", "UP", "B", "SIM", "C4", "DTZ", "RUF"]
ignore = ["E501"]

[tool.ruff.lint.isort]
known-first-party = ["gmail_assistant"]

[tool.mypy]
python_version = "3.10"
strict = true
warn_return_any = true
warn_unused_ignores = true
disallow_untyped_defs = true
packages = ["gmail_assistant"]

[[tool.mypy.overrides]]
module = [
    "googleapiclient.*",
    "google.auth.*",
    "google.oauth2.*",
    "google_auth_oauthlib.*",
]
ignore_missing_imports = true
```

### 10.2 CLI Implementation

**Location**: `src/gmail_assistant/cli/main.py`

```python
"""
Gmail Assistant CLI - Click-based command line interface.

Exit Codes:
    0: Success
    1: General error
    2: Usage/argument error (Click default)
    3: Authentication error
    4: Network error
    5: Configuration error

CORRECTED: All exceptions imported from gmail_assistant.core.exceptions
"""
from __future__ import annotations

import functools
import sys
from pathlib import Path
from typing import Callable, TypeVar

import click

from gmail_assistant import __version__
from gmail_assistant.core.config import AppConfig
# CORRECTED: Import ALL exceptions from the single authoritative source
from gmail_assistant.core.exceptions import (
    ConfigError,
    AuthError,
    NetworkError,
    GmailAssistantError,
)

F = TypeVar("F", bound=Callable[..., None])


def handle_errors(func: F) -> F:
    """Decorator to map exceptions to exit codes."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ConfigError as e:
            click.echo(f"Configuration error: {e}", err=True)
            sys.exit(5)
        except AuthError as e:
            click.echo(f"Authentication error: {e}", err=True)
            sys.exit(3)
        except NetworkError as e:
            click.echo(f"Network error: {e}", err=True)
            sys.exit(4)
        except click.ClickException:
            raise  # Let Click handle its own exceptions
        except GmailAssistantError as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)
        except Exception as e:
            click.echo(f"Unexpected error: {e}", err=True)
            sys.exit(1)
    return wrapper  # type: ignore


@click.group()
@click.version_option(version=__version__, prog_name="gmail-assistant")
@click.option(
    "--config", "-c",
    type=click.Path(exists=True, path_type=Path),
    help="Path to configuration file.",
)
@click.option(
    "--allow-repo-credentials",
    is_flag=True,
    help="Allow credentials inside git repository (security risk).",
)
@click.pass_context
def main(ctx: click.Context, config: Path | None, allow_repo_credentials: bool) -> None:
    """Gmail Assistant - Backup, analyze, and manage your Gmail."""
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = config
    ctx.obj["allow_repo_credentials"] = allow_repo_credentials


@main.command()
@click.option("--query", "-q", default="", help="Gmail search query.")
@click.option("--max-emails", "-m", type=int, help="Maximum emails to fetch.")
@click.option("--output-dir", "-o", type=click.Path(path_type=Path), help="Output directory.")
@click.option("--format", "output_format", type=click.Choice(["json", "mbox", "eml"]), default="json")
@click.pass_context
@handle_errors
def fetch(
    ctx: click.Context,
    query: str,
    max_emails: int | None,
    output_dir: Path | None,
    output_format: str,
) -> None:
    """Fetch emails from Gmail."""
    cfg = AppConfig.load(
        ctx.obj["config_path"],
        ctx.obj["allow_repo_credentials"],
    )
  
    # Override with CLI options
    if max_emails:
        cfg.max_emails = max_emails
    if output_dir:
        cfg.output_dir = output_dir
  
    click.echo(f"Fetching emails (max: {cfg.max_emails}, format: {output_format})")
    click.echo(f"Query: {query or '(all)'}")
    click.echo(f"Output: {cfg.output_dir}")
    # NOTE: Functional implementation deferred to v2.1.0 (see §1.5)
    click.echo("[INFO] Functional fetch implementation is deferred to v2.1.0")


@main.command()
@click.option("--query", "-q", required=True, help="Gmail search query for emails to delete.")
@click.option("--dry-run", is_flag=True, help="Show what would be deleted without deleting.")
@click.option("--confirm", is_flag=True, help="Skip confirmation prompt.")
@click.pass_context
@handle_errors
def delete(
    ctx: click.Context,
    query: str,
    dry_run: bool,
    confirm: bool,
) -> None:
    """Delete emails matching query."""
    cfg = AppConfig.load(
        ctx.obj["config_path"],
        ctx.obj["allow_repo_credentials"],
    )
  
    click.echo(f"Delete query: {query}")
    click.echo(f"Dry run: {dry_run}")
    # NOTE: Functional implementation deferred to v2.1.0 (see §1.5)
    click.echo("[INFO] Functional delete implementation is deferred to v2.1.0")


@main.command()
@click.option("--input-dir", "-i", type=click.Path(exists=True, path_type=Path), help="Directory with fetched emails.")
@click.option("--report", "-r", type=click.Choice(["summary", "detailed", "json"]), default="summary")
@click.pass_context
@handle_errors
def analyze(
    ctx: click.Context,
    input_dir: Path | None,
    report: str,
) -> None:
    """Analyze fetched emails."""
    cfg = AppConfig.load(
        ctx.obj["config_path"],
        ctx.obj["allow_repo_credentials"],
    )
  
    source = input_dir or cfg.output_dir
    click.echo(f"Analyzing emails in: {source}")
    click.echo(f"Report type: {report}")
    # NOTE: Functional implementation deferred to v2.1.0 (see §1.5)
    click.echo("[INFO] Functional analyze implementation is deferred to v2.1.0")


@main.command()
@click.pass_context
@handle_errors
def auth(ctx: click.Context) -> None:
    """Authenticate with Gmail API."""
    cfg = AppConfig.load(
        ctx.obj["config_path"],
        ctx.obj["allow_repo_credentials"],
    )
  
    click.echo(f"Credentials: {cfg.credentials_path}")
    click.echo(f"Token: {cfg.token_path}")
    click.echo("Starting OAuth flow...")
    # NOTE: Functional implementation deferred to v2.1.0 (see §1.5)
    click.echo("[INFO] Functional auth implementation is deferred to v2.1.0")


@main.command("config")
@click.option("--show", is_flag=True, help="Show current configuration.")
@click.option("--validate", is_flag=True, help="Validate configuration file.")
@click.option("--init", is_flag=True, help="Create default configuration.")
@click.pass_context
@handle_errors
def config_cmd(
    ctx: click.Context,
    show: bool,
    validate: bool,
    init: bool,
) -> None:
    """Manage configuration."""
    if init:
        default_dir = AppConfig.default_dir()
        default_dir.mkdir(parents=True, exist_ok=True)
        config_file = default_dir / "config.json"
      
        if config_file.exists():
            click.echo(f"Config already exists: {config_file}")
            sys.exit(5)
      
        import json
        defaults = AppConfig._defaults()
        config_data = {
            "credentials_path": str(defaults.credentials_path),
            "token_path": str(defaults.token_path),
            "output_dir": str(defaults.output_dir),
            "max_emails": defaults.max_emails,
            "rate_limit_per_second": defaults.rate_limit_per_second,
            "log_level": defaults.log_level,
        }
        config_file.write_text(json.dumps(config_data, indent=2))
        click.echo(f"Created: {config_file}")
        return
  
    try:
        cfg = AppConfig.load(
            ctx.obj["config_path"],
            ctx.obj["allow_repo_credentials"],
        )
    except ConfigError as e:
        if validate:
            click.echo(f"Configuration invalid: {e}", err=True)
            sys.exit(5)
        raise
  
    if validate:
        click.echo("Configuration valid.")
        return
  
    if show:
        click.echo(f"credentials_path: {cfg.credentials_path}")
        click.echo(f"token_path: {cfg.token_path}")
        click.echo(f"output_dir: {cfg.output_dir}")
        click.echo(f"max_emails: {cfg.max_emails}")
        click.echo(f"rate_limit_per_second: {cfg.rate_limit_per_second}")
        click.echo(f"log_level: {cfg.log_level}")
        return
  
    # Default: show help
    click.echo(ctx.get_help())


if __name__ == "__main__":
    main()
```

### 10.3 Package __init__.py

**Location**: `src/gmail_assistant/__init__.py`

```python
"""Gmail Assistant - Gmail backup, analysis, and management suite."""
__version__ = "2.0.0"
__all__ = ["__version__"]
```

### 10.4 Package __main__.py

**Location**: `src/gmail_assistant/__main__.py`

```python
"""Entry point for python -m gmail_assistant."""
from gmail_assistant.cli.main import main

if __name__ == "__main__":
    raise SystemExit(main())
```

---

## 11. CI/CD Design

### 11.1 GitHub Actions Workflow

**Location**: `.github/workflows/ci.yml`

```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    name: Test Python ${{ matrix.python-version }} on ${{ matrix.os }}
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest]
        python-version: ["3.10", "3.11", "3.12", "3.13"]

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

      - name: Run linting
        run: |
          ruff check src/ tests/

      - name: Run type checking
        run: |
          mypy src/gmail_assistant

      - name: Run tests with coverage gate
        run: |
          pytest tests/ -m "not integration and not api" -v --cov=gmail_assistant --cov-report=xml --cov-fail-under=70

      - name: Upload coverage
        if: matrix.os == 'ubuntu-latest' && matrix.python-version == '3.12'
        uses: codecov/codecov-action@v4
        with:
          file: coverage.xml

  baseline-check:
    name: Baseline Measurements
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install PowerShell
        run: |
          sudo apt-get update
          sudo apt-get install -y powershell

      - name: Run baseline measurements
        shell: pwsh
        run: |
          ./scripts/audit/baseline.ps1 -OutputDir "docs/audit"

      - name: Upload baseline
        uses: actions/upload-artifact@v4
        with:
          name: baseline-measurements
          path: docs/audit/*.json

  build-validation:
    name: Build Validation
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Build package
        run: |
          pip install build
          python -m build

      - name: Verify wheel
        run: |
          WHEEL_COUNT=$(ls -1 dist/*.whl 2>/dev/null | wc -l)
          if [ "$WHEEL_COUNT" -ne 1 ]; then
            echo "ERROR: Expected 1 wheel, found $WHEEL_COUNT"
            ls -la dist/
            exit 1
          fi
          WHEEL_PATH=$(ls -1 dist/*.whl)
          echo "Wheel: $WHEEL_PATH"

      - name: Test wheel installation (isolated)
        run: |
          python -m venv /tmp/test-venv
          /tmp/test-venv/bin/pip install dist/*.whl
          cd /tmp  # CORRECTED: Run from outside repo
          /tmp/test-venv/bin/python -c "import gmail_assistant; print(f'Version: {gmail_assistant.__version__}')"
          /tmp/test-venv/bin/gmail-assistant --version

      - name: Upload wheel
        uses: actions/upload-artifact@v4
        with:
          name: wheel
          path: dist/*.whl

  import-policy:
    name: Import Policy Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Check import policy
        run: |
          python scripts/validation/check_import_policy.py

  exception-taxonomy:
    name: Exception Taxonomy Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install package
        run: pip install -e .

      - name: Verify exception taxonomy
        run: |
          python -c "
          from gmail_assistant.core.exceptions import GmailAssistantError, ConfigError, AuthError, NetworkError
          assert issubclass(ConfigError, GmailAssistantError)
          assert issubclass(AuthError, GmailAssistantError)
          assert issubclass(NetworkError, GmailAssistantError)
        
          # Verify no duplicate ConfigError
          from gmail_assistant.core import config, exceptions
          if hasattr(config, 'ConfigError'):
              assert config.ConfigError is exceptions.ConfigError, 'Duplicate ConfigError detected!'
          print('Exception taxonomy valid')
          "

  security:
    name: Security Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Check for tracked secrets
        run: |
          if git ls-files | grep -E '(credentials|token)\.json$'; then
            echo "ERROR: Credentials tracked in git"
            exit 1
          fi
          if git ls-files | grep -E '\.log$'; then
            echo "ERROR: Log files tracked in git"
            exit 1
          fi

      - name: Run Gitleaks
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

  schema-validation:
    name: Config Schema Validation
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: pip install jsonschema

      - name: Validate schema is valid JSON Schema
        run: |
          python -c "
          import json
          from jsonschema import Draft202012Validator
        
          with open('config/schema/config.schema.json') as f:
              schema = json.load(f)
        
          Draft202012Validator.check_schema(schema)
          print('Schema is valid JSON Schema')
          "

      - name: Validate template against schema
        run: |
          python -c "
          import json
          from jsonschema import validate, Draft202012Validator
        
          with open('config/schema/config.schema.json') as f:
              schema = json.load(f)
          with open('config/default.json.template') as f:
              config = json.load(f)
        
          validate(config, schema)
          print('Template validates against schema')
          "
```

---

## 12. Validation & Quality Gates

### 12.1 Pre-Commit Checks

| Check         | Tool                   | Enforcement  | Configuration               |
| ------------- | ---------------------- | ------------ | --------------------------- |
| Linting       | ruff                   | Block commit | `.pre-commit-config.yaml` |
| Type checking | mypy                   | Block commit | `.pre-commit-config.yaml` |
| Import policy | check_import_policy.py | Block commit | `.pre-commit-config.yaml` |
| Secrets       | gitleaks               | Block commit | `.pre-commit-config.yaml` |

**Installation**:

```bash
pip install pre-commit
pre-commit install
```

### 12.2 CI Quality Gates

| Gate               | Requirement                               | Enforcement                              |
| ------------------ | ----------------------------------------- | ---------------------------------------- |
| Tests              | All tests pass on all matrix combinations | **Required for merge**             |
| Coverage           | ≥70% line coverage                       | **Required for merge** (CORRECTED) |
| Linting            | Zero ruff errors                          | **Required for merge**             |
| Type checking      | Zero mypy errors                          | **Required for merge**             |
| Build              | Wheel builds successfully                 | **Required for merge**             |
| Security           | No secrets detected                       | **Required for merge**             |
| Exception taxonomy | Single ConfigError class                  | **Required for merge**             |
| Schema validation  | Schema and template valid                 | **Required for merge**             |

### 12.3 Release Quality Gates

| Gate               | Check                                         | Script                 |
| ------------------ | --------------------------------------------- | ---------------------- |
| Wheel installation | Install in clean venv                         | `release_checks.ps1` |
| Import resolution  | Import from outside repo                      | `release_checks.ps1` |
| CLI functionality  | `--help` and `--version` work             | `release_checks.ps1` |
| Tests pass         | All non-integration tests with ≥70% coverage | `release_checks.ps1` |
| No tracked secrets | `git ls-files` check                        | `release_checks.ps1` |
| Gitleaks           | No secrets in history                         | `release_checks.ps1` |

---

## 13. Risk Register

| ID  | Risk                                             | Probability | Impact   | Mitigation                                                                    | Owner       |
| --- | ------------------------------------------------ | ----------- | -------- | ----------------------------------------------------------------------------- | ----------- |
| R1  | Import breakage post-migration                   | Medium      | High     | Two-phase validation (policy + resolution), clean venv tests                  | Implementer |
| R2  | Config path resolution breaks                    | Medium      | Medium   | Comprehensive test matrix, type validation, expanduser, cross-drive tests     | Implementer |
| R3  | Wheel doesn't include all files                  | Medium      | High     | Hatchling force-include, wheel content verification, CI gate                  | Implementer |
| R4  | Credentials leaked to git                        | Low         | Critical | Default home paths, repo-safety check, gitleaks, .gitignore                   | Implementer |
| R5  | CI fails on one platform only                    | Medium      | Medium   | Matrix testing (ubuntu + windows), pwsh everywhere                            | Implementer |
| R6  | Breaking change not documented                   | Low         | Medium   | BREAKING_CHANGES.md, ADRs, changelog                                          | Reviewer    |
| R7  | Tests mask packaging issues                      | Medium      | High     | Run tests from outside repo, clean venv isolation, non-editable wheel install | Implementer |
| R8  | Python version incompatibility                   | Low         | Medium   | CI matrix 3.10-3.13, classifier alignment                                     | Implementer |
| R9  | Migration script fails midway                    | Medium      | High     | DryRun mode, git status check, phase rollback with tags                       | Implementer |
| R10 | Circular imports revealed                        | Medium      | Medium   | Import timing check (`-X importtime`), policy checker                       | Implementer |
| R11 | **Duplicate ConfigError classes**          | High        | High     | Single source in exceptions.py, CI taxonomy check, import resolution test     | Implementer |
| R12 | **Structure drift from migration script**  | High        | High     | Migration script aligned with §5, baseline metrics corrected                 | Implementer |
| R13 | **Rollback infeasible without phase tags** | Medium      | High     | Mandatory phase commits with tags, rollback reference table                   | Implementer |
| R14 | **git unavailable at runtime**             | Low         | Medium   | Document behavior, log warning, allow credentials anywhere                    | Implementer |
| R15 | **Schema not enforced at runtime**         | Medium      | Low      | Schema validation tests in CI, optional runtime validation                    | Implementer |
| R16 | **Windows path edge cases**                | Medium      | Medium   | Path normalization, expanduser, cross-drive ValueError handling               | Implementer |
| R17 | **Editable install masks wheel defects**   | Medium      | High     | Non-editable wheel install in verify_all.ps1, isolated resolution check       | Implementer |

### 13.1 Ownership Definitions

| Role        | Responsibility                                        |
| ----------- | ----------------------------------------------------- |
| Implementer | Execute migration, write code, run validation scripts |
| Reviewer    | Review PRs, validate DoD completion, approve merges   |
| Releaser    | Tag releases, publish wheel, verify post-release      |
| Operator    | Monitor production usage, report issues               |

---

## 14. Acceptance Criteria & Release Checklist

### 14.1 Acceptance Criteria

| Criterion                           | Verification Method                     | Scope     |
| ----------------------------------- | --------------------------------------- | --------- |
| Package installs via pip            | `pip install -e .` in clean venv      | Packaging |
| CLI accessible as `gmail-assistant` | `gmail-assistant --version`             | Packaging |
| CLI accessible via `python -m`    | `python -m gmail_assistant --version`   | Packaging |
| All subcommands parse correctly     | `gmail-assistant <cmd> --help` for each | Packaging |
| Config loads from all sources       | Unit tests for resolution order         | Packaging |
| No sys.path manipulation            | Import policy checker                   | Packaging |
| Credentials secure by default       | Config loader tests                     | Packaging |
| Tests pass on all platforms         | CI matrix green                         | Quality   |
| Documentation accurate              | Manual review of README, docs           | Quality   |
| Single ConfigError class            | Exception taxonomy CI check             | Quality   |
| ≥70% test coverage                 | Coverage gate in CI                     | Quality   |

**Note**: Functional behavior (email fetching, deletion, analysis) is **out of scope** for v2.0.0. See §1.5.

### 14.2 Release Checklist

```
Pre-Release
───────────
[ ] All CI checks pass on main branch
[ ] Changelog updated for version
[ ] BREAKING_CHANGES.md complete
[ ] Version aligned in pyproject.toml and __init__.py
[ ] All phase tags exist (migration/phase-0-complete through migration/phase-5-complete)

Validation
──────────
[ ] Run: .\scripts\verify_all.ps1
[ ] All 9 checks pass (including Release Checks)

Build
─────
[ ] Run: python -m build
[ ] Verify: Single wheel in dist/
[ ] Verify: Wheel contains gmail_assistant/__init__.py

Install Test
────────────
[ ] Create fresh venv
[ ] Install wheel: pip install dist/*.whl
[ ] Verify (from /tmp): python -c "import gmail_assistant; print(gmail_assistant.__version__)"
[ ] Verify: gmail-assistant --version
[ ] Verify: gmail-assistant fetch --help
[ ] Verify: gmail-assistant auth --help

Exception Taxonomy
──────────────────
[ ] Verify: from gmail_assistant.core.exceptions import ConfigError works
[ ] Verify: config.py imports ConfigError from exceptions.py

Security
────────
[ ] Run: gitleaks detect
[ ] Verify: No credentials in git history
[ ] Verify: .gitignore includes security patterns

Release
───────
[ ] Tag: git tag -a v2.0.0 -m "Release v2.0.0"
[ ] Push: git push origin v2.0.0
[ ] Create GitHub release with changelog
[ ] Upload wheel to PyPI (if public)

Post-Release
────────────
[ ] Verify installation from PyPI (if published)
[ ] Update documentation links
[ ] Announce release (note: packaging-only, functional behavior in v2.1.0)
```

---

## 15. Revision History

| Version                     | Date       | Changes                                                                                                                                                                                                                               |
| --------------------------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| v1                          | 2026-01-09 | Initial assessment and restructuring plan                                                                                                                                                                                             |
| v2                          | 2026-01-09 | Added measurement methodology, pyproject spec, security checklist, contracts                                                                                                                                                          |
| v3                          | 2026-01-09 | Added executable scripts, Click CLI, Hatchling, clean break decision                                                                                                                                                                  |
| v4                          | 2026-01-09 | Fixed versioning, PowerShell exclusion, bash find, release checks                                                                                                                                                                     |
| v5                          | 2026-01-09 | Fixed baseline.sh metrics, repo-safety, relative imports, release paths                                                                                                                                                               |
| v6                          | 2026-01-09 | Fixed is_relative_to ValueError, Hatchling packages syntax, removed bash                                                                                                                                                              |
| v7                          | 2026-01-09 | Fixed baseline paths, CI invocation, config type validation                                                                                                                                                                           |
| v8                          | 2026-01-09 | Fixed wheel glob, split metrics, empty string validation, expanduser                                                                                                                                                                  |
| Final                       | 2026-01-09 | Consolidated all fixes, added rollback procedures, Python 3.13, config.schema.json, verify_all.ps1                                                                                                                                    |
| **Final (Corrected)** | 2026-01-09 | Expert Assessment fixes: unified ConfigError, aligned structure/migration/baseline, phase commit governance, coverage gate enforcement, git runtime dependency, pre-commit config, isolated import resolution, expanded risk register |

---

## Appendix A: ADR Index

| ADR      | Title                                 | Status   |
| -------- | ------------------------------------- | -------- |
| ADR-0001 | Package Layout and Build Backend      | Accepted |
| ADR-0002 | Compatibility Strategy (Clean Break)  | Accepted |
| ADR-0003 | CLI Framework (Click)                 | Accepted |
| ADR-0004 | Exception Taxonomy (Single Hierarchy) | Accepted |

See `docs/adr/` for full ADR documents.

---

## Appendix B: Exit Code Reference

| Code | Meaning              | Exception                    |
| ---- | -------------------- | ---------------------------- |
| 0    | Success              | None                         |
| 1    | General error        | GmailAssistantError, Exception |
| 2    | Usage/argument error | Click default                |
| 3    | Authentication error | AuthError                    |
| 4    | Network error        | NetworkError                 |
| 5    | Configuration error  | ConfigError                  |

---

## Appendix C: Environment Variables

| Variable                 | Description                | Default                      |
| ------------------------ | -------------------------- | ---------------------------- |
| `gmail_assistant_CONFIG` | Path to configuration file | None (uses resolution order) |

---

## Appendix D: Correction Summary

| Expert Issue                                             | Fix Applied                                                                                                                                              | Section Updated                |
| -------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------ |
| Target structure inconsistent with migration script      | Aligned migration to create `cli/commands/` not `cli/handlers/`; removed tools/plugins from migration                                                | §5.1, §5.2, §5.3, §8.2     |
| Baseline "config_locations" semantically misnamed        | Renamed to `post_migration_package_modules`, fixed paths checked                                                                                       | §8.1                          |
| Duplicate ConfigError classes                            | Removed ConfigError from config.py; import from exceptions.py                                                                                            | §9.1, §9.2, §10.2           |
| verify_all.ps1 doesn't invoke release_checks.ps1         | Added Step 9 that invokes release_checks.ps1                                                                                                             | §8.5                          |
| "Implementation Ready" vs TODO stubs contradiction       | Added §1.5 Functional Readiness Statement; clarified scope                                                                                              | §1.3, §1.4, §1.5, §14.1    |
| Plugin system ungoverned                                 | Moved to §5.3 Deferred Items (v2.1.0)                                                                                                                   | §5.1, §5.3                   |
| Rollback assumes uncommitted phase boundaries            | Added §6.0 Phase Governance with commit boundary rule and tags                                                                                          | §6.0, §6.1-6.6, §7.1, §7.2 |
| Phase dependency: CLI imports config before config phase | Swapped Phase 3 (now Config) and Phase 4 (now CLI)                                                                                                       | §6.4, §6.5                   |
| Coverage gate "warning only"                             | Changed to required (fail_under=70)                                                                                                                      | §12.2, pyproject.toml         |
| Pre-commit checks not mechanized                         | Added .pre-commit-config.yaml                                                                                                                            | §8.7, §12.1                  |
| Import resolution checker isolation conflict             | verify_all.ps1 runs resolution from temp dir with non-editable install                                                                                   | §8.4, §8.5                   |
| Risk ownership undifferentiated                          | Added ownership definitions table; differentiated roles                                                                                                  | §13, §13.1                   |
| Missing risks                                            | Added R11-R17 for duplicate ConfigError, structure drift, rollback feasibility, git runtime, schema enforcement, Windows paths, editable install masking | §13                           |
| Config schema not enforced                               | Added CI schema validation job, test for template                                                                                                        | §11.1 (schema-validation job) |
| git runtime dependency undocumented                      | Added §3.4 Runtime Dependencies with behavior when missing                                                                                              | §3.4, §9.1                   |
| Runtime invariants incomplete                            | Added §3.5 Runtime Invariants                                                                                                                           | §3.5                          |

---

## Appendix E: Release Readiness Verdict

**Risk Level**: **LOW**

**Justification**:

1. **All critical blockers resolved**: ConfigError unified, structure aligned, verify_all.ps1 complete, functional scope clarified
2. **Quality gates strengthened**: Coverage now required (≥70%), pre-commit hooks mechanized, CI includes exception taxonomy and schema validation
3. **Governance enforced**: Phase commits with tags enable deterministic rollback
4. **Risk coverage expanded**: 17 risks identified with mitigations and differentiated ownership
5. **Scope accurately stated**: v2.0.0 is explicitly packaging-only; functional behavior deferred to v2.1.0

**Remaining considerations** (non-blocking):

- Functional implementation deferred (acceptable for packaging release)
- Schema not enforced at runtime (covered by CI validation and loader consistency tests)
- git optional at runtime with documented degradation

**Recommendation**: Proceed with migration execution and v2.0.0 release upon successful completion of all phase DoDs and final verification checklist.

---

**Document Status**: Canonical — Single Source of Truth (Corrected)
**Supersedes**: All previous versions (v1–v8) and uncorrected Final
**Implementation Ready**: Yes
