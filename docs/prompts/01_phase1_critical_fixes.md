# Phase 1: Critical Fixes

**Duration**: ~1 hour
**Risk**: Low
**Breaking Changes**: None
**Depends On**: Phase 0

---

## Objective

Fix documentation typos, reorganize misplaced files, and capture baseline measurements.

---

## Instructions

Execute the following tasks in order:

### Task 1: Fix Documentation Filename Typos

Check for and fix any filename typos in docs:

```bash
# Check if typo file exists
ls docs/fulll_project_documentation.md 2>$null
```

If it exists, rename it:

```bash
git mv docs/fulll_project_documentation.md docs/full_project_documentation.md
```

### Task 2: Move Test Runner to Tests Directory

Check if test runner is in wrong location:

```bash
ls tests/docs/run_comprehensive_tests.py 2>$null
```

If it exists, move it:

```bash
git mv tests/docs/run_comprehensive_tests.py tests/run_comprehensive_tests.py
```

### Task 3: Create Baseline Measurement Script

Create the file `scripts/audit/baseline.ps1` with the content from the implementation plan (Section 8.1).

The script should:
- Measure max folder depth
- Count sys.path.insert occurrences
- Count package modules (post-migration and legacy)
- Count Python source files and test files
- Count entry points (post-migration and legacy)
- Output JSON with measurements and targets

**Key metrics to track:**
| Metric | Target |
|--------|--------|
| max_folder_depth | ≤3 |
| sys_path_inserts | 0 |
| post_migration_package_modules | 3 |
| legacy_package_modules | 0 |
| post_migration_entry_points | 2 |
| legacy_entry_points | 0 |

### Task 4: Create Audit Output Directory

```bash
mkdir -p docs/audit
```

### Task 5: Run Baseline Measurement

```powershell
.\scripts\audit\baseline.ps1 -OutputDir docs/audit
```

Review the output. At this point, you should see:
- `legacy_package_modules` > 0 (pre-migration state)
- `post_migration_package_modules` = 0 (not migrated yet)
- `legacy_entry_points` > 0 (old structure)

---

## Definition of Done

- [ ] No typos in filenames (check `docs/` directory)
- [ ] Test runner in `tests/` not `tests/docs/`
- [ ] `scripts/audit/baseline.ps1` exists and runs
- [ ] Baseline JSON saved to `docs/audit/`

---

## Commit

After completing all tasks:

```bash
git add -A
git commit -m "phase-1: critical fixes and baseline capture

Phase 1 of Gmail Assistant restructuring.
- Fixed documentation filename typos
- Moved test runner to correct location
- Added baseline measurement script
- Captured pre-migration baseline

See: Implementation_Plan_Final_Release_Edition.md Section 6.2

Co-Authored-By: Claude <noreply@anthropic.com>"

git tag migration/phase-1-complete
```

---

## Rollback (if needed)

```powershell
git revert $(git rev-parse migration/phase-1-complete) --no-edit
```
