# Phase 2: Packaging Foundation

**Duration**: ~4 hours
**Risk**: Medium
**Breaking Changes**: Import paths
**Depends On**: Phase 1

---

## Objective

Transform the project into a proper Python package with src-layout, remove sys.path manipulation, and establish clean imports.

---

## Instructions

This is the most complex phase. Execute carefully in order.

### Task 1: Create pyproject.toml

Create `pyproject.toml` in the repo root with the complete configuration from Implementation Plan Section 10.1.

Key elements:
- Build system: Hatchling
- Package name: `gman`
- Version: `2.0.0`
- Python: `>=3.10`
- Console script: `gman = "gman.cli.main:main"`
- Dev dependencies for testing

### Task 2: Create Migration Script

Create `scripts/migration/move_to_package_layout.ps1` with the content from Implementation Plan Section 8.2.

The script will:
- Create `src/gman/` directory
- Move: `src/cli` → `src/gman/cli`
- Move: `src/core` → `src/gman/core`
- Move: `src/analysis` → `src/gman/analysis`
- Move: `src/deletion` → `src/gman/deletion`
- Move: `src/handlers` → `src/gman/cli/commands`
- Move: `src/parsers` → `src/gman/parsers`
- Move: `src/utils` → `src/gman/utils`
- Create `__init__.py`, `__main__.py`, `py.typed`
- Skip `src/tools` and `src/plugins` (deferred)

### Task 3: Run Migration Script (Dry Run First)

```powershell
.\scripts\migration\move_to_package_layout.ps1 -DryRun
```

Review the output. Then execute:

```powershell
.\scripts\migration\move_to_package_layout.ps1
```

### Task 4: Fix All Imports (AGENT RECOMMENDED)

After migration, all imports need updating from old paths to new `gman.*` paths.

**Use the code-refactoring-specialist agent:**

```
I need to update all Python imports in this codebase after a package restructuring.

OLD IMPORT PATTERNS (find and replace):
- `from core.` → `from gman.core.`
- `from cli.` → `from gman.cli.`
- `from analysis.` → `from gman.analysis.`
- `from deletion.` → `from gman.deletion.`
- `from handlers.` → `from gman.cli.commands.`
- `from parsers.` → `from gman.parsers.`
- `from utils.` → `from gman.utils.`
- `import core` → `import gman.core`
- `import cli` → `import gman.cli`
- etc.

ALSO REMOVE all occurrences of:
- `sys.path.insert(...)`
- `sys.path.append(...)`

Search in:
- src/gman/**/*.py
- tests/**/*.py

Do NOT modify:
- scripts/ (these run standalone)
- Any comments explaining old paths
```

### Task 5: Create Import Policy Checker

Create `scripts/validation/check_import_policy.py` with the content from Implementation Plan Section 8.3.

### Task 6: Create Import Resolution Checker

Create `scripts/validation/check_import_resolution.py` with the content from Implementation Plan Section 8.4.

### Task 7: Ensure All __init__.py Files Exist

Verify these files exist (create empty ones if missing):

```
src/gman/__init__.py          # With __version__ = "2.0.0"
src/gman/cli/__init__.py
src/gman/cli/commands/__init__.py
src/gman/core/__init__.py
src/gman/analysis/__init__.py
src/gman/deletion/__init__.py
src/gman/parsers/__init__.py
src/gman/utils/__init__.py
```

### Task 8: Install Package in Editable Mode

```bash
pip install -e .
```

### Task 9: Validate

```bash
# Check import policy
python scripts/validation/check_import_policy.py

# Check no sys.path manipulation
grep -r "sys.path.insert\|sys.path.append" src/gman/ --include="*.py"

# Should return nothing. If it finds matches, remove them.

# Test imports work
python -c "import gman; print(gman.__version__)"
python -c "from gman.cli.main import main; print('CLI OK')"

# Test CLI
gman --version
python -m gman --version
```

---

## Definition of Done

- [ ] `pip install -e .` succeeds in clean venv
- [ ] `python -m gman --version` works
- [ ] `gman --version` works
- [ ] `python -m compileall src/gman -q` succeeds
- [ ] `python scripts/validation/check_import_policy.py` passes
- [ ] No `sys.path.insert` or `sys.path.append` in codebase

---

## Commit

After completing all tasks:

```bash
git add -A
git commit -m "phase-2: packaging foundation and src-layout migration

Phase 2 of Gman restructuring.
- Created pyproject.toml with Hatchling build
- Migrated to src/gman/ package layout
- Updated all imports to gman.* prefix
- Removed all sys.path manipulation
- Added import policy and resolution checkers
- Package now installable via pip

BREAKING CHANGE: All import paths changed from 'from core...' to 'from gman.core...'

See: Implementation_Plan_Final_Release_Edition.md Section 6.3

Co-Authored-By: Claude <noreply@anthropic.com>"

git tag migration/phase-2-complete
```

---

## Rollback (if needed)

```powershell
git revert $(git rev-parse migration/phase-2-complete) --no-edit
git clean -fd src/gman
pip uninstall gman -y
```
