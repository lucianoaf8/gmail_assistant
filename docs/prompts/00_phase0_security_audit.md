# Phase 0: Security Audit

**Duration**: ~1 hour
**Risk**: Low
**Breaking Changes**: None
**Depends On**: None

---

## Objective

Harden security by updating .gitignore, removing tracked sensitive files, and scanning for secrets.

---

## Instructions

Execute the following tasks in order:

### Task 1: Update .gitignore with Security Patterns

Add the following patterns to `.gitignore` (create if doesn't exist). Ensure these patterns are present:

```gitignore
# Credentials and tokens (NEVER commit)
credentials.json
token.json
*.credentials
*.token

# Log files
*.log
logs/

# Backup and data directories
backups/
data/

# Python artifacts
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
.venv/
venv/
ENV/

# IDE
.idea/
.vscode/
*.swp
*.swo

# Testing and coverage
.pytest_cache/
.coverage
htmlcov/
.tox/
.nox/

# Type checking
.mypy_cache/
.dmypy.json
dmypy.json

# Ruff
.ruff_cache/

# Build artifacts
*.whl
*.tar.gz
```

### Task 2: Remove Tracked Log Files

Check for and remove any tracked log files:

```bash
git ls-files '*.log'
```

If any are found (like `src/core/email_classifier.log`), remove them:

```bash
git rm --cached src/core/email_classifier.log
```

Or if they should be fully deleted:

```bash
git rm src/core/email_classifier.log
```

### Task 3: Check for Tracked Credentials

Verify no credentials are tracked:

```bash
git ls-files | Select-String -Pattern "(credentials|token)\.json$"
```

This should return empty. If not, remove them immediately with `git rm`.

### Task 4: Create Baseline Script Directory

```bash
mkdir -p scripts/audit
```

### Task 5: Run Security Scan (Optional)

If gitleaks is installed:

```bash
gitleaks detect --no-banner
```

---

## Definition of Done

- [ ] `.gitignore` includes: `credentials.json`, `token.json`, `*.log`, `backups/`, `data/`
- [ ] `git ls-files '*.log'` returns empty
- [ ] `git ls-files | Select-String "(credentials|token)\.json"` returns empty
- [ ] `scripts/audit/` directory exists

---

## Commit

After completing all tasks:

```bash
git add -A
git commit -m "phase-0: security audit and gitignore hardening

Phase 0 of Gmail Assistant restructuring.
See: Implementation_Plan_Final_Release_Edition.md Section 6.1

Co-Authored-By: Claude <noreply@anthropic.com>"

git tag migration/phase-0-complete
```

---

## Notes

- This phase is additive only - no rollback needed
- If gitleaks finds secrets in git history, that's a separate remediation task
