# Gmail Fetcher Implementation Plan v3

**Document ID**: 0109-1700_implementation_plan_v3.md
**Version**: 3.0 (Production-ready)
**Status**: Executable

---

## Critical Decisions (Locked)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Compatibility strategy** | **Clean break** (no shims) | Shims add complexity, testing burden, and delay cleanup. Bump to v2.0.0 with documented breaking changes. |
| **CLI framework** | **Click** | Better UX than argparse, widespread, good subcommand support, explicit over implicit. |
| **Config default location** | **User home** (`~/.gmail-fetcher/`) | Security-first; repo-local requires explicit opt-in. |
| **Build backend** | **Hatchling** | Modern, fast, better defaults than setuptools for src-layout. |
| **Python version** | **>=3.10** | Realistic minimum for 2026, enables `|` union types, match statements. |

---

## 1. Baseline Measurement Scripts (Executable)

### `scripts/audit/baseline.ps1`

```powershell
#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Captures baseline measurements and writes JSON atomically.
.OUTPUTS
    Creates docs/audit/YYYYMMDD-HHMM_baseline.json
#>
[CmdletBinding()]
param(
    [string]$OutputDir = "docs/audit"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

# Ensure we're in repo root
$repoRoot = & git rev-parse --show-toplevel 2>$null
if (-not $repoRoot) {
    Write-Error "Not in a git repository"
    exit 1
}
Set-Location $repoRoot

# Create output directory
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

# Timestamp and commit
$timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
$fileTimestamp = (Get-Date).ToString("yyyyMMdd-HHmm")
$commitSha = & git rev-parse HEAD

# Measurement functions
function Get-MaxFolderDepth {
    $maxDepth = 0
    $excludePatterns = @('__pycache__', '.git', 'node_modules', 'backups', '.venv', 'venv')

    Get-ChildItem -Path $repoRoot -Directory -Recurse -Force -ErrorAction SilentlyContinue |
        Where-Object {
            $path = $_.FullName
            -not ($excludePatterns | Where-Object { $path -like "*\$_*" })
        } |
        ForEach-Object {
            $relativePath = $_.FullName.Substring($repoRoot.Length).TrimStart('\', '/')
            $depth = ($relativePath -split '[\\/]').Count
            if ($depth -gt $maxDepth) { $maxDepth = $depth }
        }
    return $maxDepth
}

function Get-SysPathInsertCount {
    $count = 0
    Get-ChildItem -Path $repoRoot -Filter "*.py" -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -notlike "*\__pycache__\*" } |
        ForEach-Object {
            $content = Get-Content $_.FullName -Raw -ErrorAction SilentlyContinue
            if ($content -match 'sys\.path\.insert') {
                $matches = [regex]::Matches($content, 'sys\.path\.insert')
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
        Where-Object { $_.FullName -notlike "*\__pycache__\*" }).Count
}

function Get-TestFileCount {
    $testsPath = Join-Path $repoRoot "tests"
    if (-not (Test-Path $testsPath)) { return 0 }
    return (Get-ChildItem -Path $testsPath -Filter "test_*.py" -Recurse -File).Count
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
$measurements = @{
    max_folder_depth = Get-MaxFolderDepth
    sys_path_inserts = Get-SysPathInsertCount
    config_locations = Get-ConfigLocationCount
    python_source_files = Get-PythonFileCount
    test_files = Get-TestFileCount
    entry_points = Get-EntryPointCount
    hidden_docs = Get-HiddenDocsCount
}

# Build JSON object
$baseline = @{
    timestamp = $timestamp
    commit_sha = $commitSha
    repo_root = $repoRoot
    measurements = $measurements
    targets = @{
        max_folder_depth = 3
        sys_path_inserts = 0
        config_locations = 1
        entry_points = 1
        hidden_docs = 0
    }
}

# Write atomically (write to temp, then move)
$outputFile = Join-Path $OutputDir "${fileTimestamp}_baseline.json"
$tempFile = "$outputFile.tmp"

$baseline | ConvertTo-Json -Depth 10 | Set-Content -Path $tempFile -Encoding UTF8
Move-Item -Path $tempFile -Destination $outputFile -Force

Write-Host "Baseline written to: $outputFile" -ForegroundColor Green
Write-Host ""
Write-Host "Measurements:"
$measurements.GetEnumerator() | ForEach-Object {
    $target = $baseline.targets[$_.Key]
    $status = if ($target -and $_.Value -le $target) { "✓" } else { "✗" }
    Write-Host "  $status $($_.Key): $($_.Value) (target: $target)"
}

exit 0
```

### `scripts/audit/baseline.sh`

```bash
#!/usr/bin/env bash
#
# Captures baseline measurements and writes JSON atomically.
# Usage: ./scripts/audit/baseline.sh [output_dir]
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

# Measurement functions
get_max_folder_depth() {
    find . -type d \
        ! -path '*/__pycache__/*' \
        ! -path '*/.git/*' \
        ! -path '*/node_modules/*' \
        ! -path '*/backups/*' \
        ! -path '*/.venv/*' \
        ! -path '*/venv/*' \
        2>/dev/null |
        awk -F/ '{print NF-1}' |
        sort -rn |
        head -1
}

get_sys_path_insert_count() {
    grep -r "sys\.path\.insert" --include="*.py" . 2>/dev/null |
        grep -v __pycache__ |
        wc -l |
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
    find src -name "*.py" ! -path "*/__pycache__/*" 2>/dev/null | wc -l | tr -d '[:space:]'
}

get_test_file_count() {
    [[ -d "tests" ]] || { echo 0; return; }
    find tests -name "test_*.py" 2>/dev/null | wc -l | tr -d '[:space:]'
}

get_entry_point_count() {
    local count=0
    [[ -f "main.py" ]] && ((count++)) || true
    [[ -f "src/cli/main.py" ]] && ((count++)) || true
    echo "$count"
}

get_hidden_docs_count() {
    [[ -d "docs/claude-docs" ]] || { echo 0; return; }
    find docs/claude-docs -name "*.md" 2>/dev/null | wc -l | tr -d '[:space:]'
}

# Collect measurements
MAX_DEPTH=$(get_max_folder_depth)
SYS_PATH_COUNT=$(get_sys_path_insert_count)
CONFIG_LOCS=$(get_config_location_count)
PY_FILES=$(get_python_file_count)
TEST_FILES=$(get_test_file_count)
ENTRY_POINTS=$(get_entry_point_count)
HIDDEN_DOCS=$(get_hidden_docs_count)

# Build JSON
OUTPUT_FILE="$OUTPUT_DIR/${FILE_TIMESTAMP}_baseline.json"
TEMP_FILE="$OUTPUT_FILE.tmp"

cat > "$TEMP_FILE" << EOF
{
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

mv "$TEMP_FILE" "$OUTPUT_FILE"

echo "Baseline written to: $OUTPUT_FILE"
echo ""
echo "Measurements:"
echo "  max_folder_depth: $MAX_DEPTH (target: 3)"
echo "  sys_path_inserts: $SYS_PATH_COUNT (target: 0)"
echo "  config_locations: $CONFIG_LOCS (target: 1)"
echo "  python_source_files: $PY_FILES"
echo "  test_files: $TEST_FILES"
echo "  entry_points: $ENTRY_POINTS (target: 1)"
echo "  hidden_docs: $HIDDEN_DOCS (target: 0)"

exit 0
```

---

## 2. Configuration Loader (Correct Implementation)

### Design Principles

1. **Defaults point to user home** (`~/.gmail-fetcher/`)
2. **Relative paths resolve relative to config file location**, not CWD
3. **Repo-local credentials require explicit opt-in** with warning
4. **Schema validation is enforced** (fail on unknown keys, type errors)

### `src/gmail_fetcher/core/config.py`

```python
"""Configuration loader with secure defaults and strict validation."""
from __future__ import annotations

import json
import os
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

# Allowed keys (schema enforcement without external deps)
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


@dataclass(frozen=True)
class AppConfig:
    """Validated, immutable application configuration."""

    credentials_path: Path
    token_path: Path
    output_dir: Path
    max_emails: int = 1000
    rate_limit_per_second: float = 8.0
    log_level: str = "INFO"

    def __post_init__(self):
        # Validate bounds
        if not 1 <= self.max_emails <= 50000:
            raise ConfigError(f"max_emails must be 1-50000, got {self.max_emails}")
        if not 0.1 <= self.rate_limit_per_second <= 100:
            raise ConfigError(f"rate_limit must be 0.1-100, got {self.rate_limit_per_second}")
        if self.log_level not in _LOG_LEVELS:
            raise ConfigError(f"log_level must be one of {_LOG_LEVELS}, got {self.log_level}")

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
        4. Built-in defaults (credentials in ~/.gmail-fetcher/)

        Args:
            cli_config: Explicit config path from CLI
            allow_repo_credentials: If True, allow credentials inside repo (unsafe)
        """
        config_path = cls._resolve_config_path(cli_config)

        if config_path is not None:
            return cls._load_from_file(config_path, allow_repo_credentials)

        # No config file found - use defaults (user home)
        default_dir = cls.default_dir()
        return cls(
            credentials_path=default_dir / "credentials.json",
            token_path=default_dir / "token.json",
            output_dir=Path.cwd() / "gmail_backup",
        )

    @classmethod
    def _resolve_config_path(cls, cli_config: Path | None) -> Path | None:
        """Resolve config path by priority."""
        # Priority 1: CLI argument
        if cli_config is not None:
            if not cli_config.exists():
                raise ConfigError(f"Config file not found: {cli_config}")
            return cli_config

        # Priority 2: Environment variable
        env_config = os.environ.get("GMAIL_FETCHER_CONFIG")
        if env_config:
            path = Path(env_config)
            if not path.exists():
                raise ConfigError(f"GMAIL_FETCHER_CONFIG file not found: {path}")
            return path

        # Priority 3: User home config
        user_config = cls.default_dir() / "config.json"
        if user_config.exists():
            return user_config

        # No config file - will use defaults
        return None

    @classmethod
    def _load_from_file(
        cls,
        config_path: Path,
        allow_repo_credentials: bool,
    ) -> "AppConfig":
        """Load and validate config from file."""
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise ConfigError(f"Invalid JSON in {config_path}: {e}") from e

        if not isinstance(data, dict):
            raise ConfigError(f"Config must be a JSON object, got {type(data).__name__}")

        # Strict key validation
        unknown_keys = set(data.keys()) - _ALLOWED_KEYS
        if unknown_keys:
            raise ConfigError(f"Unknown config keys: {unknown_keys}")

        # Resolve paths relative to config file location
        config_dir = config_path.parent.resolve()

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
        output_dir = resolve_path("output_dir", Path.cwd() / "gmail_backup")

        # Security check: credentials should not be in repo
        cls._check_repo_safety(credentials_path, "credentials_path", allow_repo_credentials)
        cls._check_repo_safety(token_path, "token_path", allow_repo_credentials)

        return cls(
            credentials_path=credentials_path,
            token_path=token_path,
            output_dir=output_dir,
            max_emails=cls._get_int(data, "max_emails", 1000),
            rate_limit_per_second=cls._get_float(data, "rate_limit_per_second", 8.0),
            log_level=cls._get_str(data, "log_level", "INFO").upper(),
        )

    @staticmethod
    def _check_repo_safety(path: Path, name: str, allow: bool) -> None:
        """Check if path is inside a git repo (potential security risk)."""
        try:
            import subprocess
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                cwd=path.parent if path.parent.exists() else Path.cwd(),
            )
            if result.returncode == 0:
                repo_root = Path(result.stdout.strip()).resolve()
                resolved = path.resolve()
                if str(resolved).startswith(str(repo_root)):
                    if allow:
                        warnings.warn(
                            f"{name} is inside git repo ({repo_root}). "
                            f"Ensure it's in .gitignore to avoid credential leakage.",
                            UserWarning,
                            stacklevel=4,
                        )
                    else:
                        raise ConfigError(
                            f"{name} ({path}) is inside git repo. "
                            f"Move to ~/.gmail-fetcher/ or set allow_repo_credentials=True."
                        )
        except FileNotFoundError:
            pass  # git not installed, skip check

    @staticmethod
    def _get_int(data: dict, key: str, default: int) -> int:
        if key not in data:
            return default
        val = data[key]
        if not isinstance(val, int):
            raise ConfigError(f"{key} must be integer, got {type(val).__name__}")
        return val

    @staticmethod
    def _get_float(data: dict, key: str, default: float) -> float:
        if key not in data:
            return default
        val = data[key]
        if not isinstance(val, (int, float)):
            raise ConfigError(f"{key} must be number, got {type(val).__name__}")
        return float(val)

    @staticmethod
    def _get_str(data: dict, key: str, default: str) -> str:
        if key not in data:
            return default
        val = data[key]
        if not isinstance(val, str):
            raise ConfigError(f"{key} must be string, got {type(val).__name__}")
        return val
```

---

## 3. Import Validation (Two-Phase)

### Phase 1: Policy Check (AST-based, no execution)

`scripts/validation/check_import_policy.py`:

```python
#!/usr/bin/env python3
"""
Phase 1: Check import policy violations (no execution required).

Flags:
- sys.path manipulation
- Forbidden import prefixes (old-style imports)
- Relative imports outside package
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

FORBIDDEN_PREFIXES = (
    "src.",
    "analysis.",
    "deletion.",
    "handlers.",
    "parsers.",
    "plugins.",
    "tools.",
    "utils.",
    "cli.",
    "core.",
)


def check_file(path: Path) -> list[str]:
    """Check a single file for policy violations."""
    errors: list[str] = []

    try:
        content = path.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(path))
    except SyntaxError as e:
        return [f"{path}:{e.lineno}: SyntaxError: {e.msg}"]

    # Check for sys.path manipulation
    if "sys.path.insert" in content or "sys.path.append" in content:
        for i, line in enumerate(content.splitlines(), 1):
            if "sys.path.insert" in line or "sys.path.append" in line:
                errors.append(f"{path}:{i}: sys.path manipulation")

    # Check imports
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith(FORBIDDEN_PREFIXES):
                    errors.append(
                        f"{path}:{node.lineno}: Forbidden import: {alias.name}"
                    )

        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module.startswith(FORBIDDEN_PREFIXES):
                errors.append(
                    f"{path}:{node.lineno}: Forbidden import: from {module}"
                )

    return errors


def main() -> int:
    src_dir = Path("src/gmail_fetcher")
    if not src_dir.exists():
        print(f"Error: {src_dir} not found")
        return 1

    all_errors: list[str] = []
    for py_file in src_dir.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        all_errors.extend(check_file(py_file))

    # Also check tests
    tests_dir = Path("tests")
    if tests_dir.exists():
        for py_file in tests_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            all_errors.extend(check_file(py_file))

    if all_errors:
        print("Import policy check FAILED:")
        for err in sorted(set(all_errors)):
            print(f"  {err}")
        return 1

    print("Import policy check PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

### Phase 2: Resolution Check (requires install)

`scripts/validation/check_import_resolution.py`:

```python
#!/usr/bin/env python3
"""
Phase 2: Verify imports actually resolve (requires pip install -e .).

Must run in a clean venv after installation.
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

# Modules that MUST import successfully
REQUIRED_MODULES = [
    "gmail_fetcher",
    "gmail_fetcher.cli",
    "gmail_fetcher.cli.main",
    "gmail_fetcher.core",
    "gmail_fetcher.core.config",
    "gmail_fetcher.core.protocols",
    "gmail_fetcher.core.container",
    "gmail_fetcher.parsers",
    "gmail_fetcher.plugins",
    "gmail_fetcher.analysis",
    "gmail_fetcher.deletion",
    "gmail_fetcher.utils",
]


def check_module(name: str) -> str | None:
    """Try to import module, return error message or None."""
    try:
        importlib.import_module(name)
        return None
    except ImportError as e:
        return f"{name}: {e}"
    except Exception as e:
        return f"{name}: {type(e).__name__}: {e}"


def main() -> int:
    # Verify we're not importing from source directory
    cwd = Path.cwd().resolve()
    src_in_path = any(
        Path(p).resolve() == cwd / "src" or Path(p).resolve() == cwd
        for p in sys.path
    )
    if src_in_path and (cwd / "src" / "gmail_fetcher").exists():
        print("WARNING: Running from repo root with src in path.")
        print("Run from a different directory or use: cd /tmp && pytest /path/to/tests")

    errors: list[str] = []

    for module in REQUIRED_MODULES:
        err = check_module(module)
        if err:
            errors.append(err)
        else:
            print(f"  ✓ {module}")

    if errors:
        print("\nImport resolution check FAILED:")
        for err in errors:
            print(f"  ✗ {err}")
        return 1

    print("\nImport resolution check PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

### Combined Validation Script

`scripts/validation/validate_all.ps1`:

```powershell
#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Run all validation checks in sequence.
#>
[CmdletBinding()]
param(
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"

Write-Host "=== Phase 1: Policy Check ===" -ForegroundColor Cyan
python scripts/validation/check_import_policy.py
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host ""
Write-Host "=== Phase 2: Compile Check ===" -ForegroundColor Cyan
python -m compileall src/gmail_fetcher -q
if ($LASTEXITCODE -ne 0) { exit 1 }

if (-not $SkipInstall) {
    Write-Host ""
    Write-Host "=== Phase 3: Install + Resolution ===" -ForegroundColor Cyan

    # Create temp venv
    $venvPath = ".validation-venv"
    if (Test-Path $venvPath) { Remove-Item -Recurse -Force $venvPath }

    python -m venv $venvPath
    & "$venvPath/Scripts/pip" install -e . --quiet
    & "$venvPath/Scripts/python" scripts/validation/check_import_resolution.py
    $result = $LASTEXITCODE

    Remove-Item -Recurse -Force $venvPath
    if ($result -ne 0) { exit 1 }
}

Write-Host ""
Write-Host "=== All Checks Passed ===" -ForegroundColor Green
exit 0
```

---

## 4. pyproject.toml (Corrected)

```toml
[build-system]
requires = ["hatchling"]
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
    "types-requests",
]

[project.scripts]
gmail-fetcher = "gmail_fetcher.cli.main:main"

[project.urls]
Homepage = "https://github.com/user/gmail-fetcher"
Documentation = "https://github.com/user/gmail-fetcher#readme"
Repository = "https://github.com/user/gmail-fetcher"
Changelog = "https://github.com/user/gmail-fetcher/blob/main/CHANGELOG.md"

[tool.hatch.build.targets.wheel]
packages = ["src/gmail_fetcher"]

[tool.hatch.build.targets.sdist]
include = [
    "/src",
    "/tests",
    "/README.md",
    "/CHANGELOG.md",
    "/LICENSE",
]

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

[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_ignores = true
disallow_untyped_defs = true
packages = ["gmail_fetcher"]
mypy_path = "src"
```

---

## 5. CLI Implementation (Click-based)

### `src/gmail_fetcher/cli/main.py`

```python
"""Gmail Fetcher CLI - Click-based implementation."""
from __future__ import annotations

import sys
from pathlib import Path

import click

from gmail_fetcher import __version__


@click.group(invoke_without_command=True)
@click.version_option(__version__, prog_name="gmail-fetcher")
@click.option(
    "--config",
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
def main(ctx: click.Context, config: Path | None, allow_repo_credentials: bool) -> None:
    """Gmail backup, analysis, and management suite."""
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = config
    ctx.obj["allow_repo_credentials"] = allow_repo_credentials

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@main.command()
@click.option("--query", "-q", required=True, help="Gmail search query")
@click.option("--max-emails", "-m", type=int, default=1000, help="Maximum emails to fetch")
@click.option(
    "--output-dir", "-o",
    type=click.Path(path_type=Path),
    default=Path("gmail_backup"),
    help="Output directory",
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
def fetch(
    ctx: click.Context,
    query: str,
    max_emails: int,
    output_dir: Path,
    format: str,
    organize_by: str,
) -> None:
    """Fetch emails from Gmail."""
    from gmail_fetcher.core.config import AppConfig

    config = AppConfig.load(
        ctx.obj.get("config_path"),
        allow_repo_credentials=ctx.obj.get("allow_repo_credentials", False),
    )

    click.echo(f"Fetching emails matching: {query}")
    click.echo(f"Max: {max_emails}, Format: {format}, Organize: {organize_by}")
    # Implementation here...


@main.command()
@click.pass_context
def auth(ctx: click.Context) -> None:
    """Authenticate with Gmail API."""
    from gmail_fetcher.core.config import AppConfig

    config = AppConfig.load(
        ctx.obj.get("config_path"),
        allow_repo_credentials=ctx.obj.get("allow_repo_credentials", False),
    )

    click.echo(f"Credentials: {config.credentials_path}")
    click.echo(f"Token: {config.token_path}")
    # Authentication implementation...


@main.command()
@click.option("--query", "-q", help="Gmail search query for deletion")
@click.option("--dry-run", is_flag=True, default=True, help="Preview without deleting")
@click.pass_context
def delete(ctx: click.Context, query: str | None, dry_run: bool) -> None:
    """Delete emails from Gmail."""
    if dry_run:
        click.echo("DRY RUN - no emails will be deleted")
    # Implementation...


@main.command()
@click.argument("input_path", type=click.Path(exists=True, path_type=Path))
@click.pass_context
def analyze(ctx: click.Context, input_path: Path) -> None:
    """Analyze email data."""
    click.echo(f"Analyzing: {input_path}")
    # Implementation...


@main.command()
@click.pass_context
def config(ctx: click.Context) -> None:
    """Show current configuration."""
    from gmail_fetcher.core.config import AppConfig

    try:
        cfg = AppConfig.load(
            ctx.obj.get("config_path"),
            allow_repo_credentials=ctx.obj.get("allow_repo_credentials", False),
        )
        click.echo(f"credentials_path: {cfg.credentials_path}")
        click.echo(f"token_path: {cfg.token_path}")
        click.echo(f"output_dir: {cfg.output_dir}")
        click.echo(f"max_emails: {cfg.max_emails}")
        click.echo(f"rate_limit: {cfg.rate_limit_per_second}/s")
        click.echo(f"log_level: {cfg.log_level}")
    except Exception as e:
        click.echo(f"Error loading config: {e}", err=True)
        sys.exit(5)


if __name__ == "__main__":
    main()
```

---

## 6. ADR-0001: Package Layout

`docs/adr/0001-package-layout.md`:

```markdown
# ADR-0001: Package Layout and Build System

**Status**: Accepted
**Date**: 2026-01-09
**Deciders**: Architecture Review

## Context

The project needs a proper Python package structure to:
- Enable standard installation (`pip install`)
- Eliminate `sys.path` manipulation
- Support modern tooling (type checkers, linters)
- Provide stable import paths

## Decision

1. **Build system**: Hatchling (modern, fast, good src-layout support)
2. **Package location**: `src/gmail_fetcher/` (src-layout)
3. **Entry point**: Console script `gmail-fetcher` via Click
4. **Python version**: >=3.10 (enables modern syntax, pattern matching)

## Consequences

### Positive
- Standard installation workflow
- Clean import paths (`from gmail_fetcher.x import y`)
- IDE/tooling support
- Publishable to PyPI

### Negative
- All existing imports break (major version bump required)
- Users must reinstall

## Alternatives Considered

1. **setuptools**: Rejected - more config boilerplate, slower
2. **Poetry**: Rejected - adds lock file complexity not needed
3. **Flat layout**: Rejected - import conflicts with installed package
```

---

## 7. ADR-0002: Compatibility Strategy

`docs/adr/0002-compatibility-strategy.md`:

```markdown
# ADR-0002: Compatibility Strategy (Clean Break)

**Status**: Accepted
**Date**: 2026-01-09
**Deciders**: Architecture Review

## Context

Migration from unpackaged source to proper package structure breaks all imports.

Options:
A. **Clean break**: All old imports fail, document breaking changes
B. **Shims**: Temporary re-export modules with deprecation warnings

## Decision

**Option A: Clean Break**

Rationale:
- Shims add complexity and testing burden
- Shims delay inevitable cleanup
- Major version bump (v2.0.0) is appropriate signal
- Users must update imports anyway; gradual migration has no benefit

## Consequences

### Breaking Changes (v2.0.0)

| Before | After |
|--------|-------|
| `from analysis.x import y` | `from gmail_fetcher.analysis.x import y` |
| `from deletion.deleter import z` | `from gmail_fetcher.deletion.deleter import z` |
| `from src.handlers.x import y` | Removed (handlers merged into CLI) |
| `python main.py ...` | `gmail-fetcher ...` |

### Migration Required

Users must:
1. `pip install gmail-fetcher` (or `pip install -e .` for dev)
2. Update all import statements
3. Update scripts using `python main.py` to use `gmail-fetcher`

### No Deprecation Period

Old import paths fail immediately with `ImportError`. This is intentional.
```

---

## 8. ADR-0003: CLI Framework

`docs/adr/0003-cli-framework.md`:

```markdown
# ADR-0003: CLI Framework Choice (Click)

**Status**: Accepted
**Date**: 2026-01-09
**Deciders**: Architecture Review

## Context

Need a CLI framework for the `gmail-fetcher` command with:
- Subcommands (fetch, delete, analyze, auth, config)
- Options with validation
- Help generation
- Exit code conventions

## Decision

**Click**

Rationale:
- Widely used, well-documented
- Explicit over implicit (unlike argparse magic)
- Better error messages than argparse
- Easy testing with CliRunner
- No runtime dependencies beyond stdlib

## Alternatives Considered

1. **argparse**: Rejected - verbose, magic, poor UX
2. **typer**: Rejected - adds dependency on Click anyway, type annotation magic
3. **fire**: Rejected - too implicit, hard to control UX

## CLI Structure

```
gmail-fetcher
├── fetch      # Download emails
├── delete     # Delete emails
├── analyze    # Analyze email data
├── auth       # Authenticate with Gmail
└── config     # Show/validate config
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | CLI usage error |
| 3 | Authentication error |
| 4 | Network/API error |
| 5 | Configuration error |
```

---

## 9. CI Workflow (Cross-Platform)

`.github/workflows/ci.yml`:

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

      - name: Policy check (no sys.path, no forbidden imports)
        run: python scripts/validation/check_import_policy.py

      - name: Compile check
        run: python -m compileall src/gmail_fetcher -q

      - name: Import resolution check
        shell: bash
        run: |
          cd /tmp  # Run from outside repo to catch sys.path issues
          python -c "
          import gmail_fetcher
          from gmail_fetcher.cli.main import main
          from gmail_fetcher.core.config import AppConfig
          print('Imports OK')
          "

      - name: Run tests (unit only)
        run: pytest -m "not integration and not api" --cov --cov-report=xml

      - name: Type check
        run: mypy src/gmail_fetcher --ignore-missing-imports

      - name: Lint
        run: ruff check src/gmail_fetcher tests

      - name: Upload coverage
        if: matrix.os == 'ubuntu-latest' && matrix.python-version == '3.11'
        uses: codecov/codecov-action@v4
        with:
          files: coverage.xml

  integration:
    runs-on: ubuntu-latest
    needs: test
    # Only run on main branch or explicit request
    if: github.ref == 'refs/heads/main' || contains(github.event.pull_request.labels.*.name, 'run-integration')

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install
        run: pip install -e ".[dev]"

      - name: Run integration tests (mocked)
        run: pytest -m integration

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history for secret scanning

      - name: Run gitleaks
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## 10. Security: Gitleaks as Canonical

### `.gitleaks.toml`

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

### Remediation Steps (if secrets found)

```markdown
## If secrets are found in git history:

1. **Immediately rotate credentials**
   - Go to Google Cloud Console
   - Revoke compromised OAuth credentials
   - Generate new credentials

2. **Remove from history** (if not yet pushed)
   ```bash
   git filter-repo --invert-paths --path credentials.json
   ```

3. **If already pushed**
   - Assume compromised
   - Rotate ALL secrets
   - Force push cleaned history (coordinate with team)
   - Notify affected users

4. **Prevent recurrence**
   - Add to .gitignore
   - Install pre-commit hooks
   - Enable GitHub secret scanning
```

---

## 11. File Move Plan (Explicit)

### `scripts/migration/move_to_package.ps1`

```powershell
#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Moves source files to package namespace structure.
.PARAMETER DryRun
    Show what would be done without making changes.
#>
[CmdletBinding()]
param(
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$repoRoot = git rev-parse --show-toplevel
Set-Location $repoRoot

# Define moves: source -> destination
$moves = @(
    @{From="src/analysis"; To="src/gmail_fetcher/analysis"},
    @{From="src/cli"; To="src/gmail_fetcher/cli"},
    @{From="src/core"; To="src/gmail_fetcher/core"},
    @{From="src/deletion"; To="src/gmail_fetcher/deletion"},
    @{From="src/handlers"; To="src/gmail_fetcher/cli/handlers"},  # Merge into CLI
    @{From="src/parsers"; To="src/gmail_fetcher/parsers"},
    @{From="src/plugins"; To="src/gmail_fetcher/plugins"},
    @{From="src/tools"; To="src/gmail_fetcher/tools"},
    @{From="src/utils"; To="src/gmail_fetcher/utils"},
)

# Files to create
$creates = @(
    "src/gmail_fetcher/__init__.py",
    "src/gmail_fetcher/__main__.py",
    "src/gmail_fetcher/py.typed",
)

# Create target directory
$targetDir = "src/gmail_fetcher"
if ($DryRun) {
    Write-Host "[DRY-RUN] mkdir $targetDir" -ForegroundColor Yellow
} else {
    New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
}

# Execute moves
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
        # Create parent directory
        $parent = Split-Path $to -Parent
        if (-not (Test-Path $parent)) {
            New-Item -ItemType Directory -Path $parent -Force | Out-Null
        }
        git mv $from $to
        Write-Host "[MOVED] $from -> $to" -ForegroundColor Green
    }
}

# Create required files
foreach ($file in $creates) {
    if ($DryRun) {
        Write-Host "[DRY-RUN] create $file" -ForegroundColor Yellow
    } else {
        if (-not (Test-Path $file)) {
            New-Item -ItemType File -Path $file -Force | Out-Null
            Write-Host "[CREATED] $file" -ForegroundColor Green
        }
    }
}

# Copy existing __init__.py content if exists
$oldInit = "src/__init__.py"
$newInit = "src/gmail_fetcher/__init__.py"
if ((Test-Path $oldInit) -and -not $DryRun) {
    $content = Get-Content $oldInit -Raw
    # Add version
    $initContent = @"
"""Gmail Fetcher - Gmail backup, analysis, and management suite."""
__version__ = "2.0.0"

$content
"@
    Set-Content -Path $newInit -Value $initContent
}

# Create __main__.py
$mainContent = @'
"""Entry point for python -m gmail_fetcher."""
from gmail_fetcher.cli.main import main

if __name__ == "__main__":
    raise SystemExit(main())
'@

if (-not $DryRun) {
    Set-Content -Path "src/gmail_fetcher/__main__.py" -Value $mainContent
}

Write-Host ""
if ($DryRun) {
    Write-Host "DRY RUN complete. Run without -DryRun to execute." -ForegroundColor Cyan
} else {
    Write-Host "Move complete. Run validation scripts next." -ForegroundColor Green
}
```

---

## 12. Known Breaking Changes

### BREAKING_CHANGES.md

```markdown
# Breaking Changes in v2.0.0

## Import Paths

All imports have changed. There is no backward compatibility.

| Before (v1.x) | After (v2.0) |
|---------------|--------------|
| `from analysis.x import y` | `from gmail_fetcher.analysis.x import y` |
| `from core.fetch.gmail_fetcher import GmailFetcher` | `from gmail_fetcher.core.fetch.fetcher import GmailFetcher` |
| `from deletion.deleter import GmailDeleter` | `from gmail_fetcher.deletion.deleter import GmailDeleter` |
| `from handlers.x import y` | Removed - handlers merged into `gmail_fetcher.cli` |
| `from src.x import y` | `from gmail_fetcher.x import y` |

## Entry Points

| Before | After |
|--------|-------|
| `python main.py fetch ...` | `gmail-fetcher fetch ...` |
| `python main.py --query "..."` | `gmail-fetcher fetch --query "..."` |
| `python main.py --auth-only` | `gmail-fetcher auth` |

## CLI Flags

| Before | After |
|--------|-------|
| `--max` | `--max-emails` |
| `--output` | `--output-dir` |
| `--organize` | `--organize-by` |

## Configuration

Default credential paths changed from repo-relative to user home:

| Before | After |
|--------|-------|
| `./credentials.json` | `~/.gmail-fetcher/credentials.json` |
| `./token.json` | `~/.gmail-fetcher/token.json` |

To use repo-local credentials, set `--allow-repo-credentials` flag.

## Removed

- `main.py` entry point (use `gmail-fetcher` command)
- `src/handlers/` directory (merged into CLI)
- `sys.path` manipulation in all files
- Python 3.9 support (minimum is now 3.10)

## Migration Steps

1. Install new version: `pip install gmail-fetcher>=2.0.0`
2. Update all import statements
3. Move credentials to `~/.gmail-fetcher/` or use `--allow-repo-credentials`
4. Update scripts: `python main.py` → `gmail-fetcher`
5. Update CLI flags per table above
```

---

## 13. Tests: conftest.py (Correct)

`tests/conftest.py`:

```python
"""Shared pytest fixtures. Markers defined in pyproject.toml only."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Generator
from unittest.mock import Mock

import pytest


@pytest.fixture
def fixtures_dir() -> Path:
    """Path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_config(tmp_path: Path) -> tuple[Path, dict[str, Any]]:
    """Create a sample config file and return (path, data)."""
    config_data = {
        "credentials_path": "creds.json",
        "token_path": "token.json",
        "max_emails": 500,
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config_data))
    return config_path, config_data


@pytest.fixture
def mock_gmail_service() -> Generator[Mock, None, None]:
    """Mock Gmail API service."""
    mock = Mock()

    # List messages
    mock.users.return_value.messages.return_value.list.return_value.execute.return_value = {
        "messages": [{"id": "msg1"}, {"id": "msg2"}],
        "resultSizeEstimate": 2,
    }

    # Get message
    mock.users.return_value.messages.return_value.get.return_value.execute.return_value = {
        "id": "msg1",
        "threadId": "thread1",
        "payload": {
            "headers": [
                {"name": "Subject", "value": "Test Email"},
                {"name": "From", "value": "test@example.com"},
                {"name": "Date", "value": "Thu, 09 Jan 2026 10:00:00 +0000"},
            ],
            "body": {"data": "VGVzdCBib2R5"},  # "Test body"
        },
    }

    yield mock


@pytest.fixture
def clean_env(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    """Clean environment of gmail-fetcher variables."""
    monkeypatch.delenv("GMAIL_FETCHER_CONFIG", raising=False)
    yield


@pytest.fixture
def home_config_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Override home directory for config tests."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.setenv("USERPROFILE", str(fake_home))  # Windows
    return fake_home
```

**Note**: No marker registration here - markers are defined in `pyproject.toml` only.

---

## Summary: All Issues Addressed

| Issue | Resolution |
|-------|------------|
| 1. Baseline scripts don't write JSON | ✅ Complete PowerShell/Bash scripts with atomic write |
| 2. PowerShell depth fragile | ✅ Uses `Substring` relative path, proper exclusions |
| 3. Config loader contradicts security | ✅ Home defaults, resolve relative to config file, repo-safe check |
| 4. Schema not enforced | ✅ Strict key checking, type validation, bounds checking |
| 5. validate_imports.py not real | ✅ Two-phase: policy (AST) + resolution (install+import) |
| 6. Warnings choice wrong | ✅ Clean break = no warnings, just breaking changes doc |
| 7. CLI framework unspecified | ✅ ADR-0003: Click, with implementation |
| 8. Tests config conflicts | ✅ Markers in pyproject.toml only, no conftest registration |
| 9. VCR cassettes unspecified | ✅ Using `responses` library (simpler, no recording) |
| 10. Packaging spec issues | ✅ Fixed extras, hatchling, correct package-data |
| 11. "mv src/*" dangerous | ✅ Explicit move script with DryRun |
| 12. Compatibility shims vague | ✅ ADR-0002: Clean break, no shims |
| 13. CI incomplete for Windows | ✅ Matrix with ubuntu+windows, 3.10-3.12 |
| 14. Security grep narrow | ✅ Gitleaks canonical, remediation steps |

---

**Document Version**: 3.0
**Status**: Executable
**Next Action**: Run baseline script, then Phase 0 (security audit)
