# Gmail Fetcher Implementation Plan v4

**Document ID**: 0109-1800_implementation_plan_v4.md
**Release Version**: 2.0.0
**Status**: Executable (all bugs from v3 review fixed)

---

## Version Alignment

| Artifact | Version | Notes |
|----------|---------|-------|
| This document | v4 (internal revision) | |
| Release | **2.0.0** | Major bump for breaking changes |
| `pyproject.toml` | `version = "2.0.0"` | |
| `gmail_fetcher/__init__.py` | `__version__ = "2.0.0"` | |
| CHANGELOG.md | `## [2.0.0]` | |
| BREAKING_CHANGES.md | References v2.0.0 | |
| Classifier | `Development Status :: 4 - Beta` | Appropriate for major restructure |

---

## 1. Baseline Scripts (Bugs Fixed)

### `scripts/audit/baseline.ps1` (Fixed)

```powershell
#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Captures baseline measurements and writes JSON atomically.
    Fixed: exclusion logic uses segment-based matching.
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
$commitSha = & git rev-parse HEAD

# Excluded directory names (segment-based, not path-based)
$excludeNames = @('.git', '__pycache__', 'node_modules', 'backups', '.venv', 'venv', '.pytest_cache', '.mypy_cache', '.ruff_cache', 'htmlcov', 'dist', 'build', '*.egg-info')

function Test-ShouldExclude {
    param([string]$FullPath)

    # Get path segments
    $relativePath = $FullPath.Substring($repoRoot.Length).TrimStart('\', '/')
    $segments = $relativePath -split '[\\/]'

    foreach ($segment in $segments) {
        foreach ($exclude in $excludeNames) {
            if ($exclude.Contains('*')) {
                # Wildcard match
                if ($segment -like $exclude) { return $true }
            } else {
                # Exact match
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
            $segments = ($relativePath -split '[\\/]') | Where-Object { $_ -ne '' }
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

function Get-ConfigLocationCount {
    $locations = @(
        "config/app",
        "config/analysis",
        "src/analysis"
    )
    return ($locations | Where-Object { Test-Path (Join-Path $repoRoot $_) }).Count
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

function Get-EntryPointCount {
    $entryPoints = @("main.py", "src/cli/main.py")
    return ($entryPoints | Where-Object { Test-Path (Join-Path $repoRoot $_) }).Count
}

function Get-HiddenDocsCount {
    $claudeDocsPath = Join-Path $repoRoot "docs/claude-docs"
    if (-not (Test-Path $claudeDocsPath)) { return 0 }
    return (Get-ChildItem -Path $claudeDocsPath -Filter "*.md" -File).Count
}

# Collect measurements
Write-Host "Collecting measurements..." -ForegroundColor Cyan

$measurements = [ordered]@{
    max_folder_depth = Get-MaxFolderDepth
    sys_path_inserts = Get-SysPathInsertCount
    config_locations = Get-ConfigLocationCount
    python_source_files = Get-PythonFileCount
    test_files = Get-TestFileCount
    entry_points = Get-EntryPointCount
    hidden_docs = Get-HiddenDocsCount
}

# Build JSON object
$baseline = [ordered]@{
    schema_version = "1.0"
    timestamp = $timestamp
    commit_sha = $commitSha
    repo_root = $repoRoot
    measurements = $measurements
    targets = [ordered]@{
        max_folder_depth = 3
        sys_path_inserts = 0
        config_locations = 1
        entry_points = 1
        hidden_docs = 0
    }
}

# Write atomically (write to temp, then move)
$outputFile = Join-Path $OutputDir "${fileTimestamp}_baseline.json"
$tempFile = [System.IO.Path]::GetTempFileName()

try {
    $baseline | ConvertTo-Json -Depth 10 | Set-Content -Path $tempFile -Encoding UTF8 -NoNewline

    # Validate JSON before moving
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
$measurements.GetEnumerator() | ForEach-Object {
    $target = $baseline.targets[$_.Key]
    if ($null -ne $target) {
        $status = if ($_.Value -le $target) { "[PASS]" } else { "[FAIL]" }
        $color = if ($_.Value -le $target) { "Green" } else { "Red" }
        Write-Host "  $status $($_.Key): $($_.Value) (target: $target)" -ForegroundColor $color
    } else {
        Write-Host "  [INFO] $($_.Key): $($_.Value)" -ForegroundColor Gray
    }
}

exit 0
```

### `scripts/audit/baseline.sh` (Fixed)

```bash
#!/usr/bin/env bash
#
# Captures baseline measurements and writes JSON atomically.
# Fixed: uses find -prune for proper exclusion.
#
set -euo pipefail

OUTPUT_DIR="${1:-docs/audit}"

# Ensure we're in repo root
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
    echo "Error: Not in a git repository" >&2
    exit 1
}
cd "$REPO_ROOT"

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Timestamp and commit
TIMESTAMP="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
FILE_TIMESTAMP="$(date +"%Y%m%d-%H%M")"
COMMIT_SHA="$(git rev-parse HEAD)"

# Fixed: Use -prune for proper exclusion (doesn't traverse excluded dirs)
get_max_folder_depth() {
    find . \( \
        -name .git -o \
        -name __pycache__ -o \
        -name node_modules -o \
        -name backups -o \
        -name .venv -o \
        -name venv -o \
        -name .pytest_cache -o \
        -name .mypy_cache -o \
        -name .ruff_cache -o \
        -name htmlcov -o \
        -name dist -o \
        -name build -o \
        -name '*.egg-info' \
    \) -prune -o -type d -print 2>/dev/null | \
        awk -F/ '{print NF-1}' | \
        sort -rn | \
        head -1
}

get_sys_path_insert_count() {
    find . \( \
        -name .git -o \
        -name __pycache__ -o \
        -name .venv -o \
        -name venv \
    \) -prune -o -name "*.py" -print 2>/dev/null | \
        xargs grep -l 'sys\.path\.\(insert\|append\)' 2>/dev/null | \
        wc -l | \
        tr -d '[:space:]'
}

get_config_location_count() {
    local count=0
    for dir in "config/app" "config/analysis" "src/analysis"; do
        [[ -d "$dir" ]] && ((count++)) || true
    done
    echo "$count"
}

get_python_file_count() {
    [[ -d "src" ]] || { echo 0; return; }
    find src \( -name __pycache__ -o -name .venv \) -prune -o \
        -name "*.py" -print 2>/dev/null | wc -l | tr -d '[:space:]'
}

get_test_file_count() {
    [[ -d "tests" ]] || { echo 0; return; }
    find tests \( -name __pycache__ -o -name .pytest_cache \) -prune -o \
        -name "test_*.py" -print 2>/dev/null | wc -l | tr -d '[:space:]'
}

get_entry_point_count() {
    local count=0
    [[ -f "main.py" ]] && ((count++)) || true
    [[ -f "src/cli/main.py" ]] && ((count++)) || true
    echo "$count"
}

get_hidden_docs_count() {
    [[ -d "docs/claude-docs" ]] || { echo 0; return; }
    find docs/claude-docs -maxdepth 1 -name "*.md" -type f 2>/dev/null | wc -l | tr -d '[:space:]'
}

# Collect measurements
echo "Collecting measurements..."

MAX_DEPTH=$(get_max_folder_depth)
SYS_PATH_COUNT=$(get_sys_path_insert_count)
CONFIG_LOCS=$(get_config_location_count)
PY_FILES=$(get_python_file_count)
TEST_FILES=$(get_test_file_count)
ENTRY_POINTS=$(get_entry_point_count)
HIDDEN_DOCS=$(get_hidden_docs_count)

# Build JSON atomically
OUTPUT_FILE="$OUTPUT_DIR/${FILE_TIMESTAMP}_baseline.json"
TEMP_FILE="$(mktemp)"

trap 'rm -f "$TEMP_FILE"' EXIT

cat > "$TEMP_FILE" << EOF
{
  "schema_version": "1.0",
  "timestamp": "$TIMESTAMP",
  "commit_sha": "$COMMIT_SHA",
  "repo_root": "$REPO_ROOT",
  "measurements": {
    "max_folder_depth": $MAX_DEPTH,
    "sys_path_inserts": $SYS_PATH_COUNT,
    "config_locations": $CONFIG_LOCS,
    "python_source_files": $PY_FILES,
    "test_files": $TEST_FILES,
    "entry_points": $ENTRY_POINTS,
    "hidden_docs": $HIDDEN_DOCS
  },
  "targets": {
    "max_folder_depth": 3,
    "sys_path_inserts": 0,
    "config_locations": 1,
    "entry_points": 1,
    "hidden_docs": 0
  }
}
EOF

# Validate JSON before moving
python3 -c "import json; json.load(open('$TEMP_FILE'))" || {
    echo "Error: Generated invalid JSON" >&2
    exit 1
}

mv "$TEMP_FILE" "$OUTPUT_FILE"
trap - EXIT

echo "Baseline written to: $OUTPUT_FILE"
echo ""
echo "Measurements vs Targets:"

check_metric() {
    local name="$1" value="$2" target="$3"
    if [[ "$value" -le "$target" ]]; then
        echo "  [PASS] $name: $value (target: $target)"
    else
        echo "  [FAIL] $name: $value (target: $target)"
    fi
}

check_metric "max_folder_depth" "$MAX_DEPTH" 3
check_metric "sys_path_inserts" "$SYS_PATH_COUNT" 0
check_metric "config_locations" "$CONFIG_LOCS" 1
echo "  [INFO] python_source_files: $PY_FILES"
echo "  [INFO] test_files: $TEST_FILES"
check_metric "entry_points" "$ENTRY_POINTS" 1
check_metric "hidden_docs" "$HIDDEN_DOCS" 0

exit 0
```

---

## 2. Configuration Loader (All Bugs Fixed)

```python
# src/gmail_fetcher/core/config.py
"""
Configuration loader with secure defaults and strict validation.

Fixed in v4:
- Default output_dir is home-based, not CWD
- Repo-safety uses is_relative_to (Python 3.10+)
- Repo root determined from config file or project, not credential path
- Handles git-not-installed explicitly
"""
from __future__ import annotations

import json
import os
import subprocess
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Schema enforcement
_ALLOWED_KEYS = frozenset({
    "credentials_path",
    "token_path",
    "output_dir",
    "max_emails",
    "rate_limit_per_second",
    "log_level",
})

_LOG_LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})


class ConfigError(Exception):
    """Configuration validation error."""


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Validated, immutable application configuration."""

    credentials_path: Path
    token_path: Path
    output_dir: Path
    max_emails: int = 1000
    rate_limit_per_second: float = 8.0
    log_level: str = "INFO"

    def __post_init__(self) -> None:
        if not 1 <= self.max_emails <= 50000:
            raise ConfigError(f"max_emails must be 1-50000, got {self.max_emails}")
        if not 0.1 <= self.rate_limit_per_second <= 100:
            raise ConfigError(
                f"rate_limit_per_second must be 0.1-100, got {self.rate_limit_per_second}"
            )
        if self.log_level not in _LOG_LEVELS:
            raise ConfigError(f"log_level must be one of {_LOG_LEVELS}")

    @classmethod
    def default_dir(cls) -> Path:
        """Return the default config directory (~/.gmail-fetcher/)."""
        return Path.home() / ".gmail-fetcher"

    @classmethod
    def load(
        cls,
        cli_config: Path | None = None,
        *,
        allow_repo_credentials: bool = False,
    ) -> "AppConfig":
        """
        Load config following resolution order:
        1. --config CLI argument
        2. GMAIL_FETCHER_CONFIG env var
        3. ~/.gmail-fetcher/config.json (user home)
        4. Built-in defaults (all paths in ~/.gmail-fetcher/)
        """
        config_path = cls._resolve_config_path(cli_config)

        if config_path is not None:
            return cls._load_from_file(config_path, allow_repo_credentials)

        # No config file - use secure defaults (all in user home)
        default_dir = cls.default_dir()
        return cls(
            credentials_path=default_dir / "credentials.json",
            token_path=default_dir / "token.json",
            output_dir=default_dir / "backups",  # Fixed: home-based, not CWD
        )

    @classmethod
    def _resolve_config_path(cls, cli_config: Path | None) -> Path | None:
        # Priority 1: CLI argument
        if cli_config is not None:
            resolved = cli_config.resolve()
            if not resolved.exists():
                raise ConfigError(f"Config file not found: {resolved}")
            return resolved

        # Priority 2: Environment variable
        env_config = os.environ.get("GMAIL_FETCHER_CONFIG")
        if env_config:
            resolved = Path(env_config).resolve()
            if not resolved.exists():
                raise ConfigError(f"GMAIL_FETCHER_CONFIG not found: {resolved}")
            return resolved

        # Priority 3: User home config
        user_config = cls.default_dir() / "config.json"
        if user_config.exists():
            return user_config.resolve()

        return None

    @classmethod
    def _load_from_file(
        cls,
        config_path: Path,
        allow_repo_credentials: bool,
    ) -> "AppConfig":
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise ConfigError(f"Invalid JSON in {config_path}: {e}") from e

        if not isinstance(data, dict):
            raise ConfigError(f"Config must be a JSON object, got {type(data).__name__}")

        # Strict key validation (fail on unknown keys)
        unknown_keys = set(data.keys()) - _ALLOWED_KEYS
        if unknown_keys:
            raise ConfigError(f"Unknown config keys: {sorted(unknown_keys)}")

        # Resolve paths relative to config file location (not CWD)
        config_dir = config_path.parent

        def resolve_path(key: str, default: Path) -> Path:
            if key not in data:
                return default
            p = Path(data[key])
            if not p.is_absolute():
                p = (config_dir / p).resolve()
            return p

        default_dir = cls.default_dir()
        credentials_path = resolve_path("credentials_path", default_dir / "credentials.json")
        token_path = resolve_path("token_path", default_dir / "token.json")
        output_dir = resolve_path("output_dir", default_dir / "backups")

        # Security check: determine repo root from config file location (not credential path)
        repo_root = cls._find_repo_root(config_path.parent)

        if repo_root is not None:
            cls._check_path_safety(
                credentials_path, "credentials_path", repo_root, allow_repo_credentials
            )
            cls._check_path_safety(
                token_path, "token_path", repo_root, allow_repo_credentials
            )

        return cls(
            credentials_path=credentials_path,
            token_path=token_path,
            output_dir=output_dir,
            max_emails=cls._get_int(data, "max_emails", 1000),
            rate_limit_per_second=cls._get_float(data, "rate_limit_per_second", 8.0),
            log_level=cls._get_str(data, "log_level", "INFO").upper(),
        )

    @staticmethod
    def _find_repo_root(search_from: Path) -> Path | None:
        """Find git repo root, or None if not in a repo or git not installed."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                cwd=search_from,
                timeout=5,
            )
            if result.returncode == 0:
                return Path(result.stdout.strip()).resolve()
        except (FileNotFoundError, subprocess.TimeoutExpired):
            # git not installed or timed out
            pass
        return None

    @staticmethod
    def _check_path_safety(
        path: Path,
        name: str,
        repo_root: Path,
        allow: bool,
    ) -> None:
        """Check if path is inside repo (security risk)."""
        resolved = path.resolve()

        # Python 3.10+: use is_relative_to for robust check
        try:
            is_inside_repo = resolved.is_relative_to(repo_root)
        except ValueError:
            # Different drives on Windows
            is_inside_repo = False

        if is_inside_repo:
            if allow:
                warnings.warn(
                    f"{name} ({resolved}) is inside git repo. "
                    f"Ensure it's in .gitignore to prevent credential leakage.",
                    UserWarning,
                    stacklevel=5,
                )
            else:
                raise ConfigError(
                    f"{name} ({resolved}) is inside git repo ({repo_root}). "
                    f"Move to {AppConfig.default_dir()} or use --allow-repo-credentials."
                )

    @staticmethod
    def _get_int(data: dict[str, Any], key: str, default: int) -> int:
        if key not in data:
            return default
        val = data[key]
        if not isinstance(val, int) or isinstance(val, bool):
            raise ConfigError(f"{key} must be integer, got {type(val).__name__}")
        return val

    @staticmethod
    def _get_float(data: dict[str, Any], key: str, default: float) -> float:
        if key not in data:
            return default
        val = data[key]
        if isinstance(val, bool) or not isinstance(val, (int, float)):
            raise ConfigError(f"{key} must be number, got {type(val).__name__}")
        return float(val)

    @staticmethod
    def _get_str(data: dict[str, Any], key: str, default: str) -> str:
        if key not in data:
            return default
        val = data[key]
        if not isinstance(val, str):
            raise ConfigError(f"{key} must be string, got {type(val).__name__}")
        return val
```

---

## 3. Import Policy Checker (Fixed Scope)

```python
#!/usr/bin/env python3
# scripts/validation/check_import_policy.py
"""
Phase 1: Check import policy violations.

Fixed in v4:
- Only forbids OLD top-level package names that existed before migration
- Does not forbid legitimate third-party packages named 'core', etc.
- Properly checks relative imports
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

# OLD top-level package names that existed before migration
# These should NOT be imported directly anymore
OLD_PACKAGE_ROOTS = frozenset({
    "src",        # Never valid as import
    "analysis",   # Was src/analysis, now gmail_fetcher.analysis
    "deletion",   # Was src/deletion, now gmail_fetcher.deletion
    "handlers",   # Was src/handlers, now merged into gmail_fetcher.cli
    "parsers",    # Was src/parsers, now gmail_fetcher.parsers
    "plugins",    # Was src/plugins, now gmail_fetcher.plugins
    "tools",      # Was src/tools, now gmail_fetcher.tools
    "utils",      # Was src/utils, now gmail_fetcher.utils
    "cli",        # Was src/cli, now gmail_fetcher.cli
    "core",       # Was src/core, now gmail_fetcher.core
})


def get_import_root(module: str) -> str:
    """Get the root package name from an import."""
    return module.split(".")[0]


def check_file(path: Path) -> list[str]:
    """Check a single file for policy violations."""
    errors: list[str] = []

    try:
        content = path.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(path))
    except SyntaxError as e:
        return [f"{path}:{e.lineno}: SyntaxError: {e.msg}"]
    except UnicodeDecodeError as e:
        return [f"{path}: UnicodeDecodeError: {e}"]

    # Check for sys.path manipulation
    for i, line in enumerate(content.splitlines(), 1):
        if "sys.path.insert" in line or "sys.path.append" in line:
            # Skip if it's a comment
            stripped = line.lstrip()
            if not stripped.startswith("#"):
                errors.append(f"{path}:{i}: sys.path manipulation forbidden")

    # Check imports
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = get_import_root(alias.name)
                if root in OLD_PACKAGE_ROOTS:
                    errors.append(
                        f"{path}:{node.lineno}: Old import: 'import {alias.name}' "
                        f"- use 'from gmail_fetcher.{alias.name} import ...' instead"
                    )

        elif isinstance(node, ast.ImportFrom):
            if node.module is None:
                continue  # from . import x - relative import, check separately

            root = get_import_root(node.module)
            if root in OLD_PACKAGE_ROOTS:
                errors.append(
                    f"{path}:{node.lineno}: Old import: 'from {node.module}' "
                    f"- use 'from gmail_fetcher.{node.module} import ...' instead"
                )

            # Also catch 'from src.x import y'
            if node.module.startswith("src."):
                errors.append(
                    f"{path}:{node.lineno}: Invalid import: 'from {node.module}' "
                    f"- 'src' is not a package"
                )

    return errors


def main() -> int:
    # Check both src and tests directories
    check_dirs = []

    src_dir = Path("src/gmail_fetcher")
    if src_dir.exists():
        check_dirs.append(src_dir)
    else:
        # Pre-migration layout
        src_dir = Path("src")
        if src_dir.exists():
            check_dirs.append(src_dir)

    tests_dir = Path("tests")
    if tests_dir.exists():
        check_dirs.append(tests_dir)

    if not check_dirs:
        print("Warning: No src/ or tests/ directory found")
        return 0

    all_errors: list[str] = []

    for check_dir in check_dirs:
        for py_file in check_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            all_errors.extend(check_file(py_file))

    if all_errors:
        print(f"Import policy check FAILED ({len(all_errors)} violations):")
        for err in sorted(set(all_errors)):
            print(f"  {err}")
        return 1

    print(f"Import policy check PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

---

## 4. pyproject.toml (Fixed Hatchling Config)

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
    "Programming Language :: Python :: 3.13",
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

# Fixed: Correct hatchling src-layout configuration
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

# Ensure py.typed is included
[tool.hatch.build.targets.wheel.force-include]
"src/gmail_fetcher/py.typed" = "gmail_fetcher/py.typed"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "-v",
    "--tb=short",
    "--strict-markers",
]
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

# Fixed: Remove --ignore-missing-imports, add explicit per-module config
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

---

## 5. CLI Implementation (Fixed Exit Codes & Precedence)

```python
# src/gmail_fetcher/cli/main.py
"""
Gmail Fetcher CLI - Click-based implementation.

Fixed in v4:
- Proper exit code mapping via exception handler
- Config/CLI flag precedence: CLI overrides config
- Version from package metadata
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import NoReturn

import click

from gmail_fetcher.core.config import AppConfig, ConfigError

# Exit codes (documented in ADR-0003)
EXIT_SUCCESS = 0
EXIT_GENERAL_ERROR = 1
EXIT_USAGE_ERROR = 2  # Click handles this automatically
EXIT_AUTH_ERROR = 3
EXIT_NETWORK_ERROR = 4
EXIT_CONFIG_ERROR = 5


def get_version() -> str:
    """Get version from package metadata or fallback."""
    try:
        from importlib.metadata import version
        return version("gmail-fetcher")
    except Exception:
        # Fallback for editable installs or when metadata unavailable
        try:
            from gmail_fetcher import __version__
            return __version__
        except ImportError:
            return "2.0.0"


class GmailFetcherError(Exception):
    """Base exception for gmail-fetcher errors."""
    exit_code: int = EXIT_GENERAL_ERROR


class AuthenticationError(GmailFetcherError):
    """Authentication failed."""
    exit_code = EXIT_AUTH_ERROR


class NetworkError(GmailFetcherError):
    """Network/API error."""
    exit_code = EXIT_NETWORK_ERROR


def handle_errors(func):
    """Decorator to map exceptions to exit codes."""
    import functools

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ConfigError as e:
            click.echo(f"Configuration error: {e}", err=True)
            sys.exit(EXIT_CONFIG_ERROR)
        except AuthenticationError as e:
            click.echo(f"Authentication error: {e}", err=True)
            sys.exit(EXIT_AUTH_ERROR)
        except NetworkError as e:
            click.echo(f"Network error: {e}", err=True)
            sys.exit(EXIT_NETWORK_ERROR)
        except GmailFetcherError as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(e.exit_code)
        except KeyboardInterrupt:
            click.echo("\nInterrupted.", err=True)
            sys.exit(130)

    return wrapper


@click.group(invoke_without_command=True)
@click.version_option(get_version(), prog_name="gmail-fetcher")
@click.option(
    "--config", "config_path",
    type=click.Path(exists=True, path_type=Path),
    envvar="GMAIL_FETCHER_CONFIG",
    help="Path to config file",
)
@click.option(
    "--allow-repo-credentials",
    is_flag=True,
    default=False,
    help="Allow credentials inside git repo (unsafe)",
)
@click.pass_context
@handle_errors
def main(ctx: click.Context, config_path: Path | None, allow_repo_credentials: bool) -> None:
    """Gmail backup, analysis, and management suite."""
    ctx.ensure_object(dict)

    # Load config early so all commands have access
    try:
        config = AppConfig.load(config_path, allow_repo_credentials=allow_repo_credentials)
        ctx.obj["config"] = config
    except ConfigError:
        # Some commands (like 'config') may want to show errors differently
        ctx.obj["config"] = None
        ctx.obj["config_error"] = sys.exc_info()[1]

    ctx.obj["config_path"] = config_path
    ctx.obj["allow_repo_credentials"] = allow_repo_credentials

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@main.command()
@click.option("--query", "-q", required=True, help="Gmail search query")
@click.option(
    "--max-emails", "-m",
    type=click.IntRange(1, 50000),
    default=None,  # None = use config default
    help="Maximum emails to fetch (overrides config)",
)
@click.option(
    "--output-dir", "-o",
    type=click.Path(path_type=Path),
    default=None,  # None = use config default
    help="Output directory (overrides config)",
)
@click.option(
    "--format", "-f",
    type=click.Choice(["eml", "markdown", "both"]),
    default="both",
    help="Output format",
)
@click.option(
    "--organize-by",
    type=click.Choice(["date", "sender", "none"]),
    default="date",
    help="Organization strategy",
)
@click.pass_context
@handle_errors
def fetch(
    ctx: click.Context,
    query: str,
    max_emails: int | None,
    output_dir: Path | None,
    format: str,
    organize_by: str,
) -> None:
    """Fetch emails from Gmail."""
    config: AppConfig = ctx.obj["config"]
    if config is None:
        raise ctx.obj.get("config_error") or ConfigError("No configuration loaded")

    # CLI flags override config (explicit precedence)
    effective_max = max_emails if max_emails is not None else config.max_emails
    effective_output = output_dir if output_dir is not None else config.output_dir

    click.echo(f"Query: {query}")
    click.echo(f"Max emails: {effective_max}")
    click.echo(f"Output: {effective_output}")
    click.echo(f"Format: {format}, Organize: {organize_by}")

    # TODO: Actual implementation
    click.echo("Fetch not yet implemented")


@main.command()
@click.pass_context
@handle_errors
def auth(ctx: click.Context) -> None:
    """Authenticate with Gmail API."""
    config: AppConfig | None = ctx.obj["config"]

    if config is None:
        # Try to load with defaults for auth setup
        config = AppConfig.load(
            ctx.obj.get("config_path"),
            allow_repo_credentials=ctx.obj.get("allow_repo_credentials", False),
        )

    click.echo(f"Credentials: {config.credentials_path}")
    click.echo(f"Token: {config.token_path}")

    if not config.credentials_path.exists():
        click.echo(f"\nCredentials file not found: {config.credentials_path}", err=True)
        click.echo("Download from Google Cloud Console and place at the above path.")
        sys.exit(EXIT_CONFIG_ERROR)

    # TODO: Actual authentication implementation
    click.echo("\nAuthentication flow not yet implemented")


@main.command()
@click.option("--query", "-q", help="Gmail search query for deletion")
@click.option("--dry-run/--no-dry-run", default=True, help="Preview without deleting")
@click.pass_context
@handle_errors
def delete(ctx: click.Context, query: str | None, dry_run: bool) -> None:
    """Delete emails from Gmail."""
    config: AppConfig = ctx.obj["config"]
    if config is None:
        raise ctx.obj.get("config_error") or ConfigError("No configuration loaded")

    if dry_run:
        click.echo("DRY RUN - no emails will be deleted")

    if not query:
        click.echo("Error: --query is required", err=True)
        sys.exit(EXIT_USAGE_ERROR)

    # TODO: Implementation
    click.echo(f"Would delete emails matching: {query}")


@main.command()
@click.argument("input_path", type=click.Path(exists=True, path_type=Path))
@click.pass_context
@handle_errors
def analyze(ctx: click.Context, input_path: Path) -> None:
    """Analyze email data."""
    click.echo(f"Analyzing: {input_path}")
    # TODO: Implementation


@main.command("config")
@click.pass_context
@handle_errors
def show_config(ctx: click.Context) -> None:
    """Show current configuration."""
    config: AppConfig | None = ctx.obj["config"]

    if config is None:
        error = ctx.obj.get("config_error")
        if error:
            click.echo(f"Configuration error: {error}", err=True)
            sys.exit(EXIT_CONFIG_ERROR)
        click.echo("No configuration loaded (using defaults)")
        config = AppConfig.load()

    click.echo(f"credentials_path: {config.credentials_path}")
    click.echo(f"token_path: {config.token_path}")
    click.echo(f"output_dir: {config.output_dir}")
    click.echo(f"max_emails: {config.max_emails}")
    click.echo(f"rate_limit: {config.rate_limit_per_second}/s")
    click.echo(f"log_level: {config.log_level}")


if __name__ == "__main__":
    main()
```

---

## 6. Package `__init__.py` (Always Populated)

```python
# src/gmail_fetcher/__init__.py
"""Gmail Fetcher - Gmail backup, analysis, and management suite."""

__version__ = "2.0.0"
__all__ = ["__version__"]
```

---

## 7. CI Workflow (Fixed for Windows)

```yaml
# .github/workflows/ci.yml
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

      - name: Policy check (no sys.path, no old imports)
        run: python scripts/validation/check_import_policy.py

      - name: Compile check
        run: python -m compileall src/gmail_fetcher -q

      # Fixed: OS-conditional import resolution
      - name: Import resolution check (Linux/macOS)
        if: runner.os != 'Windows'
        run: |
          cd /tmp
          python -c "
          import gmail_fetcher
          from gmail_fetcher.cli.main import main
          from gmail_fetcher.core.config import AppConfig
          print('Version:', gmail_fetcher.__version__)
          print('Imports OK')
          "

      - name: Import resolution check (Windows)
        if: runner.os == 'Windows'
        shell: pwsh
        run: |
          Set-Location $env:TEMP
          python -c @"
          import gmail_fetcher
          from gmail_fetcher.cli.main import main
          from gmail_fetcher.core.config import AppConfig
          print('Version:', gmail_fetcher.__version__)
          print('Imports OK')
          "@

      - name: Run tests
        run: pytest -m "not integration and not api" --cov --cov-report=xml

      - name: Type check
        run: mypy src/gmail_fetcher

      - name: Lint
        run: ruff check src/gmail_fetcher tests

      - name: Upload coverage
        if: matrix.os == 'ubuntu-latest' && matrix.python-version == '3.11'
        uses: codecov/codecov-action@v4
        with:
          files: coverage.xml

  # Build and install validation
  build-validation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Build package
        run: |
          pip install build
          python -m build

      - name: Install wheel in clean venv
        run: |
          python -m venv /tmp/test-venv
          /tmp/test-venv/bin/pip install dist/*.whl

      - name: Verify installation
        run: |
          cd /tmp  # Ensure not in repo
          /tmp/test-venv/bin/python -c "
          import gmail_fetcher
          print('Version:', gmail_fetcher.__version__)
          assert gmail_fetcher.__version__ == '2.0.0', 'Version mismatch'

          from gmail_fetcher.cli.main import main
          from gmail_fetcher.core.config import AppConfig
          print('All imports OK')
          "

      - name: Verify CLI works
        run: |
          /tmp/test-venv/bin/gmail-fetcher --version
          /tmp/test-venv/bin/gmail-fetcher --help

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

  # Release DoD checks
  release-dod:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4

      - name: Check no forbidden files exist
        run: |
          errors=0

          # main.py should not exist (or should be documented legacy)
          if [ -f "main.py" ]; then
            echo "WARNING: main.py exists - ensure it's documented as legacy shim"
          fi

          # Old package roots should not exist
          for dir in src/analysis src/deletion src/handlers src/cli src/core src/parsers src/plugins src/tools src/utils; do
            if [ -d "$dir" ] && [ ! -d "src/gmail_fetcher" ]; then
              echo "ERROR: $dir exists but src/gmail_fetcher doesn't - migration incomplete"
              errors=1
            fi
          done

          # Credentials/tokens should not be tracked
          if git ls-files | grep -qE '(credentials|token)\.json$'; then
            echo "ERROR: Credentials or tokens tracked in git"
            errors=1
          fi

          # Log files should not be tracked
          if git ls-files | grep -qE '\.log$'; then
            echo "ERROR: Log files tracked in git"
            errors=1
          fi

          exit $errors
```

---

## 8. Move Script (Fixed)

```powershell
#!/usr/bin/env pwsh
# scripts/migration/move_to_package.ps1
<#
.SYNOPSIS
    Moves source files to package namespace structure.

Fixed in v4:
- Preflight checks (destination doesn't exist, clean working tree)
- Always writes __init__.py with version
- Post-move validation
#>
[CmdletBinding()]
param(
    [switch]$DryRun,
    [switch]$Force
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repoRoot = (git rev-parse --show-toplevel)
if (-not $repoRoot) { throw "Not in a git repository" }
$repoRoot = (Resolve-Path $repoRoot).Path
Set-Location $repoRoot

$targetDir = "src/gmail_fetcher"
$version = "2.0.0"

# Preflight checks
Write-Host "=== Preflight Checks ===" -ForegroundColor Cyan

# Check clean working tree (unless Force)
$gitStatus = git status --porcelain
if ($gitStatus -and -not $Force) {
    Write-Host "ERROR: Working tree is not clean. Commit or stash changes first." -ForegroundColor Red
    Write-Host "Use -Force to override (not recommended)." -ForegroundColor Yellow
    exit 1
}

# Check target doesn't exist (unless Force)
if ((Test-Path $targetDir) -and -not $Force) {
    Write-Host "ERROR: $targetDir already exists. Remove it first or use -Force." -ForegroundColor Red
    exit 1
}

Write-Host "[OK] Preflight checks passed" -ForegroundColor Green

# Source directories to move
$moves = @(
    @{From="src/analysis"; To="$targetDir/analysis"},
    @{From="src/cli"; To="$targetDir/cli"},
    @{From="src/core"; To="$targetDir/core"},
    @{From="src/deletion"; To="$targetDir/deletion"},
    @{From="src/handlers"; To="$targetDir/cli/handlers"},
    @{From="src/parsers"; To="$targetDir/parsers"},
    @{From="src/plugins"; To="$targetDir/plugins"},
    @{From="src/tools"; To="$targetDir/tools"},
    @{From="src/utils"; To="$targetDir/utils"},
)

if ($DryRun) {
    Write-Host ""
    Write-Host "=== DRY RUN ===" -ForegroundColor Yellow
}

# Create target directory
if ($DryRun) {
    Write-Host "[DRY-RUN] New-Item -ItemType Directory -Path $targetDir"
} else {
    New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    Write-Host "[CREATED] $targetDir" -ForegroundColor Green
}

# Move directories
Write-Host ""
Write-Host "=== Moving Directories ===" -ForegroundColor Cyan

foreach ($move in $moves) {
    $from = $move.From
    $to = $move.To

    if (-not (Test-Path $from)) {
        Write-Host "[SKIP] $from (does not exist)" -ForegroundColor Gray
        continue
    }

    if ($DryRun) {
        Write-Host "[DRY-RUN] git mv $from $to"
    } else {
        # Create parent directory if needed
        $parent = Split-Path $to -Parent
        if (-not (Test-Path $parent)) {
            New-Item -ItemType Directory -Path $parent -Force | Out-Null
        }

        git mv $from $to
        if ($LASTEXITCODE -ne 0) { throw "git mv failed: $from -> $to" }
        Write-Host "[MOVED] $from -> $to" -ForegroundColor Green
    }
}

# Create required files
Write-Host ""
Write-Host "=== Creating Package Files ===" -ForegroundColor Cyan

# __init__.py with version (always create, deterministic content)
$initContent = @"
"""Gmail Fetcher - Gmail backup, analysis, and management suite."""

__version__ = "$version"
__all__ = ["__version__"]
"@

$initPath = "$targetDir/__init__.py"
if ($DryRun) {
    Write-Host "[DRY-RUN] Write $initPath with __version__ = '$version'"
} else {
    Set-Content -Path $initPath -Value $initContent -Encoding UTF8
    Write-Host "[CREATED] $initPath (version $version)" -ForegroundColor Green
}

# __main__.py
$mainContent = @'
"""Entry point for python -m gmail_fetcher."""
from gmail_fetcher.cli.main import main

if __name__ == "__main__":
    raise SystemExit(main())
'@

$mainPath = "$targetDir/__main__.py"
if ($DryRun) {
    Write-Host "[DRY-RUN] Write $mainPath"
} else {
    Set-Content -Path $mainPath -Value $mainContent -Encoding UTF8
    Write-Host "[CREATED] $mainPath" -ForegroundColor Green
}

# py.typed marker
$pytypedPath = "$targetDir/py.typed"
if ($DryRun) {
    Write-Host "[DRY-RUN] Write $pytypedPath"
} else {
    Set-Content -Path $pytypedPath -Value "" -Encoding UTF8
    Write-Host "[CREATED] $pytypedPath" -ForegroundColor Green
}

# Cleanup old src/__init__.py if it exists
$oldInit = "src/__init__.py"
if (Test-Path $oldInit) {
    if ($DryRun) {
        Write-Host "[DRY-RUN] Remove $oldInit"
    } else {
        git rm $oldInit 2>$null
        Write-Host "[REMOVED] $oldInit" -ForegroundColor Yellow
    }
}

# Post-move validation
if (-not $DryRun) {
    Write-Host ""
    Write-Host "=== Post-Move Validation ===" -ForegroundColor Cyan

    # Check structure exists
    $required = @(
        "$targetDir/__init__.py",
        "$targetDir/__main__.py",
        "$targetDir/py.typed",
        "$targetDir/cli",
        "$targetDir/core"
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
        if ($foundVersion -eq $version) {
            Write-Host "[OK] __version__ = '$foundVersion'" -ForegroundColor Green
        } else {
            Write-Host "[FAIL] __version__ mismatch: $foundVersion != $version" -ForegroundColor Red
            $allOk = $false
        }
    } else {
        Write-Host "[FAIL] __version__ not found in __init__.py" -ForegroundColor Red
        $allOk = $false
    }

    if ($allOk) {
        Write-Host ""
        Write-Host "=== Move Complete ===" -ForegroundColor Green
        Write-Host "Next steps:"
        Write-Host "  1. Run: pip install -e ."
        Write-Host "  2. Run: python scripts/validation/check_import_policy.py"
        Write-Host "  3. Run: pytest"
        Write-Host "  4. Commit: git add -A && git commit -m 'refactor: migrate to package layout'"
    } else {
        Write-Host ""
        Write-Host "=== Validation Failed ===" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host ""
    Write-Host "DRY RUN complete. Run without -DryRun to execute." -ForegroundColor Cyan
}
```

---

## 9. Release DoD Checks (3 Must-Pass)

### `scripts/validation/release_checks.ps1`

```powershell
#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Must-pass release checks. Run before tagging a release.
#>
[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$exitCode = 0

Write-Host "=== Release DoD Checks ===" -ForegroundColor Cyan
Write-Host ""

# Check 1: Build and install wheel
Write-Host "Check 1: Build and install wheel" -ForegroundColor Yellow
Write-Host "---"

$venvPath = ".release-check-venv"
$tempDir = [System.IO.Path]::GetTempPath()

try {
    # Clean
    if (Test-Path $venvPath) { Remove-Item -Recurse -Force $venvPath }
    if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }

    # Build
    python -m pip install --quiet build
    python -m build --quiet
    if ($LASTEXITCODE -ne 0) { throw "Build failed" }
    Write-Host "[OK] Package built" -ForegroundColor Green

    # Create venv and install
    python -m venv $venvPath
    & "$venvPath/Scripts/pip" install --quiet (Get-ChildItem dist/*.whl | Select-Object -First 1)
    if ($LASTEXITCODE -ne 0) { throw "Wheel installation failed" }
    Write-Host "[OK] Wheel installed" -ForegroundColor Green

    # Import checks from outside repo
    Set-Location $tempDir
    $output = & "$([System.IO.Path]::GetFullPath("$PWD/../$venvPath"))/Scripts/python" -c @"
import gmail_fetcher
print(f'Version: {gmail_fetcher.__version__}')
from gmail_fetcher.cli.main import main
from gmail_fetcher.core.config import AppConfig
print('All imports OK')
"@
    if ($LASTEXITCODE -ne 0) { throw "Import check failed" }
    Write-Host $output
    Write-Host "[OK] Import resolution passed" -ForegroundColor Green

    # CLI check
    & "$([System.IO.Path]::GetFullPath("$PWD/../$venvPath"))/Scripts/gmail-fetcher" --version
    if ($LASTEXITCODE -ne 0) { throw "CLI --version failed" }
    Write-Host "[OK] CLI works" -ForegroundColor Green

} catch {
    Write-Host "[FAIL] Check 1 failed: $_" -ForegroundColor Red
    $exitCode = 1
} finally {
    Set-Location $PSScriptRoot/../..
    if (Test-Path $venvPath) { Remove-Item -Recurse -Force $venvPath }
}

Write-Host ""

# Check 2: Tests pass from outside repo
Write-Host "Check 2: Tests from outside repo" -ForegroundColor Yellow
Write-Host "---"

try {
    $venvPath2 = ".test-check-venv"
    if (Test-Path $venvPath2) { Remove-Item -Recurse -Force $venvPath2 }

    python -m venv $venvPath2
    & "$venvPath2/Scripts/pip" install --quiet -e ".[dev]"

    # Run from temp directory
    $repoRoot = $PWD
    Set-Location $tempDir

    & "$repoRoot/$venvPath2/Scripts/pytest" "$repoRoot/tests" -m "not integration and not api" -q
    if ($LASTEXITCODE -ne 0) { throw "Tests failed" }
    Write-Host "[OK] Tests passed" -ForegroundColor Green

} catch {
    Write-Host "[FAIL] Check 2 failed: $_" -ForegroundColor Red
    $exitCode = 1
} finally {
    Set-Location $repoRoot
    if (Test-Path $venvPath2) { Remove-Item -Recurse -Force $venvPath2 }
}

Write-Host ""

# Check 3: Security checks
Write-Host "Check 3: Security checks" -ForegroundColor Yellow
Write-Host "---"

try {
    # Check no credentials tracked
    $tracked = git ls-files | Select-String -Pattern "(credentials|token)\.json$"
    if ($tracked) {
        throw "Credentials tracked in git: $tracked"
    }
    Write-Host "[OK] No credentials tracked" -ForegroundColor Green

    # Check no log files tracked
    $logs = git ls-files | Select-String -Pattern "\.log$"
    if ($logs) {
        throw "Log files tracked in git: $logs"
    }
    Write-Host "[OK] No log files tracked" -ForegroundColor Green

    # Check gitignore includes critical patterns
    $gitignore = Get-Content .gitignore -ErrorAction SilentlyContinue
    $required = @("credentials.json", "token.json", "*.log")
    foreach ($pattern in $required) {
        if ($gitignore -notcontains $pattern -and $gitignore -notmatch [regex]::Escape($pattern)) {
            Write-Host "[WARN] .gitignore may not include: $pattern" -ForegroundColor Yellow
        }
    }
    Write-Host "[OK] .gitignore reviewed" -ForegroundColor Green

    # Gitleaks (if available)
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

---

## 10. Summary: All v3 Issues Fixed

| # | Issue | Fix |
|---|-------|-----|
| 1 | Versioning contradiction | Aligned to v2.0.0 everywhere, Beta classifier kept |
| 2 | PowerShell exclusion bug | Segment-based matching with `Test-ShouldExclude` |
| 3 | Bash depth measurement | Proper `find -prune` syntax |
| 4 | Config repo-safety unreliable | `is_relative_to`, repo root from config dir |
| 5 | Config output_dir CWD | Default is `~/.gmail-fetcher/backups/` |
| 6 | Import checker forbids legit | Only OLD_PACKAGE_ROOTS, not generic names |
| 7 | Import resolution weak | Runs from `/tmp` or `$env:TEMP`, CI enforced |
| 8 | CLI exit codes not mapped | `@handle_errors` decorator with exception mapping |
| 9 | Hatchling packaging wrong | Correct `[tool.hatch.build]` config |
| 10 | Package-data not configured | `force-include` for py.typed |
| 11 | CI bash on Windows | OS-conditional steps with pwsh |
| 12 | mypy --ignore-missing-imports | Per-module overrides in pyproject |
| 13 | Move script incomplete | Preflight checks, always writes __init__.py |
| 14 | Release DoD missing | 3 must-pass checks script |

---

**Document Version**: v4
**Release Version**: 2.0.0
**Status**: Executable - all known bugs fixed
