# Final Validation & Release Preparation

**Duration**: ~1 hour
**Risk**: Low
**Depends On**: All phases (0-5) complete

---

## Objective

Create validation scripts, run full verification pipeline, and prepare for release.

---

## Instructions

### Task 1: Create Unified Verification Pipeline

Create `scripts/verify_all.ps1` with the content from Implementation Plan Section 8.5.

This script runs all 9 verification steps:
1. Baseline measurements
2. Import policy check
3. Package build
4. Wheel installation test (isolated)
5. Import resolution check (isolated)
6. Test suite with coverage gate
7. Security checks
8. CLI smoke test
9. Release checks

### Task 2: Create Release Checks Script

Create `scripts/validation/release_checks.ps1` with the content from Implementation Plan Section 8.6.

This script performs must-pass release validation:
1. Build wheel and verify installation from outside repo
2. Run tests from outside repo
3. Security verification

### Task 3: Create Pre-Commit Configuration

Create `.pre-commit-config.yaml` with the content from Implementation Plan Section 8.7.

Then install pre-commit hooks:

```bash
pip install pre-commit
pre-commit install
```

### Task 4: Create CI Workflow

Create `.github/workflows/ci.yml` with the content from Implementation Plan Section 11.1.

This workflow runs on push/PR and includes:
- Test matrix (Python 3.10-3.13, Ubuntu + Windows)
- Linting (ruff)
- Type checking (mypy)
- Coverage gate (≥70%)
- Build validation
- Import policy check
- Exception taxonomy check
- Security check
- Schema validation

### Task 5: Update Documentation

**Update README.md** with:
- New installation instructions (`pip install -e .`)
- New CLI usage (`gmail-assistant --help`)
- Breaking changes notice
- Link to BREAKING_CHANGES.md

**Create BREAKING_CHANGES.md**:

```markdown
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

# New
gmail-assistant fetch --query "is:unread"
```

## Configuration

Configuration now defaults to `~/.gmail-assistant/` for security:

- Credentials: `~/.gmail-assistant/credentials.json`
- Token: `~/.gmail-assistant/token.json`
- Config: `~/.gmail-assistant/config.json`

## Entry Points

- Old: `python main.py`
- New: `gmail-assistant` or `python -m gmail_assistant`

## Migration Guide

1. Update all imports to use `gmail_assistant.*` prefix
2. Move credentials to `~/.gmail-assistant/`
3. Update any scripts using old CLI syntax
4. Run `pip install -e .` to install package
```

**Create/Update CHANGELOG.md**:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-01-09

### Added
- Click-based CLI with subcommands (fetch, delete, analyze, auth, config)
- Secure configuration system with `~/.gmail-assistant/` defaults
- Centralized exception hierarchy
- JSON Schema for configuration validation
- Comprehensive test suite with ≥70% coverage gate
- Pre-commit hooks for code quality
- CI/CD pipeline with GitHub Actions

### Changed
- **BREAKING**: Migrated to src-layout package structure
- **BREAKING**: All imports now use `gmail_assistant.*` prefix
- **BREAKING**: CLI completely redesigned
- **BREAKING**: Configuration paths changed

### Removed
- Legacy entry points (main.py, src/cli/main.py)
- sys.path manipulation
- Flat import structure

### Security
- Credentials now default to user home directory
- Added repo-safety checks for credential paths
- Added gitleaks integration

## [1.x.x] - Previous

See git history for previous versions.
```

### Task 6: Run Full Verification

```powershell
.\scripts\verify_all.ps1
```

All 9 checks should pass:
- [PASS] Baseline
- [PASS] Import Policy
- [PASS] Build
- [PASS] Install Test
- [PASS] Import Resolution
- [PASS] Tests
- [PASS] Security
- [PASS] CLI Smoke
- [PASS] Release Checks

### Task 7: Manual Verification Checklist

Run through these manually:

```bash
# 1. Clean venv test
python -m venv .test-venv
.\.test-venv\Scripts\activate
pip install dist/*.whl
cd $env:TEMP
gmail-assistant --version
gmail-assistant fetch --help
python -c "import gmail_assistant; print(gmail_assistant.__version__)"
deactivate
cd C:\_Lucx\Projects\gmail_assistant
Remove-Item -Recurse .test-venv

# 2. Version alignment check
grep -E "version.*2\.0\.0" pyproject.toml
grep -E "__version__.*2\.0\.0" src/gmail_assistant/__init__.py

# 3. Security check
git ls-files | Select-String "(credentials|token)\.json"
# Should be empty
```

---

## Definition of Done

- [ ] `scripts/verify_all.ps1` exists and runs
- [ ] `scripts/validation/release_checks.ps1` exists
- [ ] `.pre-commit-config.yaml` exists
- [ ] `.github/workflows/ci.yml` exists
- [ ] All 9 verification checks pass
- [ ] README.md updated with new instructions
- [ ] BREAKING_CHANGES.md created
- [ ] CHANGELOG.md updated for v2.0.0
- [ ] Version aligned: pyproject.toml = __init__.py = 2.0.0
- [ ] All phase tags exist (migration/phase-0-complete through phase-5-complete)

---

## Commit

After completing all tasks:

```bash
git add -A
git commit -m "chore: add validation scripts and release documentation

- Added unified verification pipeline (verify_all.ps1)
- Added release checks script
- Added pre-commit configuration
- Added GitHub Actions CI workflow
- Updated README with new installation/usage
- Created BREAKING_CHANGES.md migration guide
- Updated CHANGELOG.md for v2.0.0

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Release (when ready)

```bash
# Final verification
.\scripts\verify_all.ps1

# Build release
python -m build

# Tag release
git tag -a v2.0.0 -m "Release v2.0.0 - Packaging and restructuring release"
git push origin main --tags

# Create GitHub release with CHANGELOG content
```

---

## Post-Release

- [ ] Verify installation from PyPI (if published)
- [ ] Update documentation links
- [ ] Announce release (note: packaging-only, functional behavior in v2.1.0)
- [ ] Plan v2.1.0 functional implementation
