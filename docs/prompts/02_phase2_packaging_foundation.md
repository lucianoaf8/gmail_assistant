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
- Package name: `gmail-assistant`
- Version: `2.0.0`
- Python: `>=3.10`
- Console script: `gmail-assistant = "gmail_assistant.cli.main:main"`
- Dev dependencies for testing

### Task 2: Create Migration Script

Create `scripts/migration/move_to_package_layout.ps1` with the content from Implementation Plan Section 8.2.

The script will:
- Create `src/gmail_assistant/` directory
- Move: `src/cli` → `src/gmail_assistant/cli`
- Move: `src/core` → `src/gmail_assistant/core`
- Move: `src/analysis` → `src/gmail_assistant/analysis`
- Move: `src/deletion` → `src/gmail_assistant/deletion`
- Move: `src/handlers` → `src/gmail_assistant/cli/commands`
- Move: `src/parsers` → `src/gmail_assistant/parsers`
- Move: `src/utils` → `src/gmail_assistant/utils`
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

After migration, all imports need updating from old paths to new `gmail_assistant.*` paths.

**Use the code-refactoring-specialist agent:**

```
I need to update all Python imports in this codebase after a package restructuring.

OLD IMPORT PATTERNS (find and replace):
- `from core.` → `from gmail_assistant.core.`
- `from cli.` → `from gmail_assistant.cli.`
- `from analysis.` → `from gmail_assistant.analysis.`
- `from deletion.` → `from gmail_assistant.deletion.`
- `from handlers.` → `from gmail_assistant.cli.commands.`
- `from parsers.` → `from gmail_assistant.parsers.`
- `from utils.` → `from gmail_assistant.utils.`
- `import core` → `import gmail_assistant.core`
- `import cli` → `import gmail_assistant.cli`
- etc.

ALSO REMOVE all occurrences of:
- `sys.path.insert(...)`
- `sys.path.append(...)`

Search in:
- src/gmail_assistant/**/*.py
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
src/gmail_assistant/__init__.py          # With __version__ = "2.0.0"
src/gmail_assistant/cli/__init__.py
src/gmail_assistant/cli/commands/__init__.py
src/gmail_assistant/core/__init__.py
src/gmail_assistant/analysis/__init__.py
src/gmail_assistant/deletion/__init__.py
src/gmail_assistant/parsers/__init__.py
src/gmail_assistant/utils/__init__.py
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
grep -r "sys.path.insert\|sys.path.append" src/gmail_assistant/ --include="*.py"

# Should return nothing. If it finds matches, remove them.

# Test imports work
python -c "import gmail_assistant; print(gmail_assistant.__version__)"
python -c "from gmail_assistant.cli.main import main; print('CLI OK')"

# Test CLI
gmail-assistant --version
python -m gmail_assistant --version
```

---

## Definition of Done

- [ ] `pip install -e .` succeeds in clean venv
- [ ] `python -m gmail_assistant --version` works
- [ ] `gmail-assistant --version` works
- [ ] `python -m compileall src/gmail_assistant -q` succeeds
- [ ] `python scripts/validation/check_import_policy.py` passes
- [ ] No `sys.path.insert` or `sys.path.append` in codebase

---

## Commit

After completing all tasks:

```bash
git add -A
git commit -m "phase-2: packaging foundation and src-layout migration

Phase 2 of Gmail Assistant restructuring.
- Created pyproject.toml with Hatchling build
- Migrated to src/gmail_assistant/ package layout
- Updated all imports to gmail_assistant.* prefix
- Removed all sys.path manipulation
- Added import policy and resolution checkers
- Package now installable via pip

BREAKING CHANGE: All import paths changed from 'from core...' to 'from gmail_assistant.core...'

See: Implementation_Plan_Final_Release_Edition.md Section 6.3

Co-Authored-By: Claude <noreply@anthropic.com>"

git tag migration/phase-2-complete
```

---

## Rollback (if needed)

```powershell
git revert $(git rev-parse migration/phase-2-complete) --no-edit
git clean -fd src/gmail_assistant
pip uninstall gmail-assistant -y
```
