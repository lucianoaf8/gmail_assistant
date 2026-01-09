# Gmail Fetcher Implementation Plan v7

**Document ID**: 0109-2200_implementation_plan_v7.md
**Release Version**: 2.0.0
**Status**: Executable (all bugs from v6 review fixed)

---

## Version Alignment

| Artifact | Version | Notes |
|----------|---------|-------|
| This document | v7 (internal revision) | |
| Release | **2.0.0** | Major bump for breaking changes |
| `pyproject.toml` | `version = "2.0.0"` | |
| `gmail_fetcher/__init__.py` | `__version__ = "2.0.0"` | |
| CHANGELOG.md | `## [2.0.0]` | |
| BREAKING_CHANGES.md | References v2.0.0 | |
| Classifier | `Development Status :: 4 - Beta` | Appropriate for major restructure |

---

## v6 Issues Fixed in v7

| # | Issue | Fix |
|---|-------|-----|
| 1 | baseline.ps1 checks pre-migration paths only | Updated to check both legacy AND post-migration paths |
| 2 | CI baseline invocation fails on Ubuntu (CRLF/exec issues) | Changed to explicit `pwsh -NoProfile -File` invocation |
| 3 | Config `resolve_path()` throws TypeError for non-strings | Added type validation before `Path()` call |

---

## Platform Contract

**v7 CLARIFICATION**: This project is **Windows-first** with cross-platform CI support:

- Primary development environment: Windows
- CI runs on: Ubuntu + Windows (GitHub Actions)
- PowerShell scripts MUST work under `pwsh` on both platforms
- Dev prerequisite for non-Windows contributors: PowerShell Core (`pwsh`)

---

## 1. Baseline Script (v7 Fixes)

### `scripts/audit/baseline.ps1`

```powershell
#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Captures baseline measurements and writes JSON atomically.
    v4: segment-based exclusion
    v5: schema_version 1.1, depth_convention field
    v6: Only script (removed baseline.sh - Windows-focused project)
    v7: Updated paths for post-migration layout (src/gmail_fetcher/...)
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

# Excluded directory names (segment-based, not path-based)
$excludeNames = @('.git', '__pycache__', 'node_modules', 'backups', '.venv', 'venv', '.pytest_cache', '.mypy_cache', '.ruff_cache', 'htmlcov', 'dist', 'build', '*.egg-info')

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
    # Counts OCCURRENCES (not files)
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

# v7 FIX: Support both legacy AND post-migration layouts
function Get-ConfigLocationCount {
    $locations = @(
        "config/app",
        "config/analysis",
        "src/analysis",                  # legacy
        "src/gmail_fetcher/analysis"     # post-migration
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

# v7 FIX: Support both legacy AND post-migration entry points
function Get-EntryPointCount {
    $entryPoints = @(
        "main.py",                            # optional legacy shim
        "src/cli/main.py",                    # legacy
        "src/gmail_fetcher/cli/main.py",      # post-migration CLI
        "src/gmail_fetcher/__main__.py"       # post-migration python -m support
    )
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
# v7: Updated targets for post-migration layout
#   - entry_points = 2 (cli/main.py + __main__.py)
#   - config_locations = 1 (only src/gmail_fetcher/analysis expected)
$baseline = [ordered]@{
    schema_version = "1.2"  # v7: bumped for target changes
    depth_convention = "segments_under_repo_root"
    timestamp = $timestamp
    commit_sha = $commitSha
    repo_root = $repoRoot
    measurements = $measurements
    targets = [ordered]@{
        max_folder_depth = 3
        sys_path_inserts = 0
        config_locations = 1    # post-migration: only src/gmail_fetcher/analysis
        entry_points = 2        # v7: cli/main.py + __main__.py
        hidden_docs = 0
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

---

## 2. Configuration Loader (v7 Fixes)

```python
# src/gmail_fetcher/core/config.py
"""
Configuration loader with secure defaults and strict validation.

v4 fixes:
- Default output_dir is home-based, not CWD
- Repo-safety uses is_relative_to (Python 3.10+)
- Repo root determined from config file or project, not credential path
- Handles git-not-installed explicitly

v5 fixes:
- Repo-safety checks BOTH config dir AND CWD repo roots

v6 fixes:
- Re-added try/except ValueError around is_relative_to
  (Windows cross-drive paths CAN raise ValueError, e.g., C:\ vs D:\)

v7 fixes:
- Added type validation in resolve_path() before Path() call
  (prevents TypeError for non-string config values like integers)
"""
from __future__ import annotations

import json
import os
import subprocess
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any

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

        default_dir = cls.default_dir()
        return cls(
            credentials_path=default_dir / "credentials.json",
            token_path=default_dir / "token.json",
            output_dir=default_dir / "backups",
        )

    @classmethod
    def _resolve_config_path(cls, cli_config: Path | None) -> Path | None:
        if cli_config is not None:
            resolved = cli_config.resolve()
            if not resolved.exists():
                raise ConfigError(f"Config file not found: {resolved}")
            return resolved

        env_config = os.environ.get("GMAIL_FETCHER_CONFIG")
        if env_config:
            resolved = Path(env_config).resolve()
            if not resolved.exists():
                raise ConfigError(f"GMAIL_FETCHER_CONFIG not found: {resolved}")
            return resolved

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

        unknown_keys = set(data.keys()) - _ALLOWED_KEYS
        if unknown_keys:
            raise ConfigError(f"Unknown config keys: {sorted(unknown_keys)}")

        config_dir = config_path.parent

        def resolve_path(key: str, default: Path) -> Path:
            if key not in data:
                return default
            # v7 FIX: Validate type before Path() to ensure ConfigError, not TypeError
            raw = data[key]
            if not isinstance(raw, str):
                raise ConfigError(f"{key} must be string path, got {type(raw).__name__}")
            p = Path(raw)
            if not p.is_absolute():
                p = (config_dir / p).resolve()
            return p

        default_dir = cls.default_dir()
        credentials_path = resolve_path("credentials_path", default_dir / "credentials.json")
        token_path = resolve_path("token_path", default_dir / "token.json")
        output_dir = resolve_path("output_dir", default_dir / "backups")

        # Check BOTH config dir repo AND CWD repo for credential safety
        repo_roots = cls._find_all_repo_roots(config_path.parent)

        for repo_root in repo_roots:
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
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            pass
        return None

    @classmethod
    def _find_all_repo_roots(cls, config_dir: Path) -> list[Path]:
        """
        Find repo roots from BOTH config directory AND CWD.
        Returns deduplicated list of repo roots to check.
        """
        roots: set[Path] = set()

        config_repo = cls._find_repo_root(config_dir)
        if config_repo:
            roots.add(config_repo)

        cwd_repo = cls._find_repo_root(Path.cwd())
        if cwd_repo:
            roots.add(cwd_repo)

        return list(roots)

    @staticmethod
    def _check_path_safety(
        path: Path,
        name: str,
        repo_root: Path,
        allow: bool,
    ) -> None:
        """Check if path is inside repo (security risk)."""
        resolved = path.resolve()

        # v6 FIX: Windows cross-drive paths CAN raise ValueError
        try:
            is_inside_repo = resolved.is_relative_to(repo_root)
        except ValueError:
            # Different drives on Windows - definitely not inside repo
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

## 3. Import Policy Checker

```python
#!/usr/bin/env python3
# scripts/validation/check_import_policy.py
"""
Check import policy violations.

v4 fixes:
- Only forbids OLD top-level package names that existed before migration
- Does not forbid legitimate third-party packages named 'core', etc.

v5 fixes:
- Actually validates relative imports (level > 0)
- Better error messages: special-case 'src' as never-importable
- Validates relative imports don't escape package boundary

(No changes needed for v6/v7)
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

# OLD top-level package names that existed before migration
OLD_PACKAGE_ROOTS = frozenset({
    "analysis",
    "deletion",
    "handlers",
    "parsers",
    "plugins",
    "tools",
    "utils",
    "cli",
    "core",
})

# 'src' is NEVER a valid import root
INVALID_IMPORT_ROOTS = frozenset({"src"})


def get_import_root(module: str) -> str:
    """Get the root package name from an import."""
    return module.split(".")[0]


def get_package_depth(file_path: Path, package_root: Path) -> int:
    """
    Calculate how deep a file is within the package.
    Returns number of directories between package_root and file's parent.
    """
    try:
        relative = file_path.parent.relative_to(package_root)
        return len(relative.parts)
    except ValueError:
        return -1  # File not under package root


def check_relative_import(
    node: ast.ImportFrom,
    file_path: Path,
    package_root: Path,
) -> str | None:
    """
    Validate relative imports don't escape package boundary.
    Returns error message if violation found, None otherwise.
    """
    if node.level == 0:
        return None  # Absolute import

    file_depth = get_package_depth(file_path, package_root)
    if file_depth < 0:
        return (
            f"{file_path}:{node.lineno}: Relative import outside package "
            f"(level={node.level})"
        )

    # level=1 means current package, level=2 means parent, etc.
    # If level > file_depth + 1, we're escaping the package
    if node.level > file_depth + 1:
        return (
            f"{file_path}:{node.lineno}: Relative import escapes package boundary "
            f"(level={node.level}, max_allowed={file_depth + 1})"
        )

    return None


def check_file(path: Path, package_root: Path | None) -> list[str]:
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
            stripped = line.lstrip()
            if not stripped.startswith("#"):
                errors.append(f"{path}:{i}: sys.path manipulation forbidden")

    # Check imports
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = get_import_root(alias.name)

                if root in INVALID_IMPORT_ROOTS:
                    errors.append(
                        f"{path}:{node.lineno}: Invalid import root: 'import {alias.name}' "
                        f"- '{root}' is not a package and can never be imported"
                    )
                elif root in OLD_PACKAGE_ROOTS:
                    errors.append(
                        f"{path}:{node.lineno}: Old import: 'import {alias.name}' "
                        f"- use 'from gmail_fetcher.{root} import ...' instead"
                    )

        elif isinstance(node, ast.ImportFrom):
            # Check relative imports
            if node.level > 0 and package_root is not None:
                rel_error = check_relative_import(node, path, package_root)
                if rel_error:
                    errors.append(rel_error)
                continue  # Relative import checked, skip absolute checks

            if node.module is None:
                continue  # `from . import x` with level > 0 already handled

            root = get_import_root(node.module)

            if root in INVALID_IMPORT_ROOTS:
                errors.append(
                    f"{path}:{node.lineno}: Invalid import: 'from {node.module}' "
                    f"- '{root}' is not a package and can never be imported"
                )
            elif root in OLD_PACKAGE_ROOTS:
                errors.append(
                    f"{path}:{node.lineno}: Old import: 'from {node.module}' "
                    f"- use 'from gmail_fetcher.{root} import ...' instead"
                )

    return errors


def main() -> int:
    check_dirs: list[tuple[Path, Path | None]] = []  # (dir, package_root)

    # Post-migration layout
    src_pkg = Path("src/gmail_fetcher")
    if src_pkg.exists():
        check_dirs.append((src_pkg, src_pkg))
    else:
        # Pre-migration layout
        src_dir = Path("src")
        if src_dir.exists():
            check_dirs.append((src_dir, None))

    tests_dir = Path("tests")
    if tests_dir.exists():
        check_dirs.append((tests_dir, None))

    if not check_dirs:
        print("Warning: No src/ or tests/ directory found")
        return 0

    all_errors: list[str] = []

    for check_dir, package_root in check_dirs:
        for py_file in check_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            all_errors.extend(check_file(py_file, package_root))

    if all_errors:
        print(f"Import policy check FAILED ({len(all_errors)} violations):")
        for err in sorted(set(all_errors)):
            print(f"  {err}")
        return 1

    print("Import policy check PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

---

## 4. pyproject.toml

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

# v6 FIX: Correct Hatchling src-layout configuration
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

## 5. CLI Implementation

```python
# src/gmail_fetcher/cli/main.py
"""
Gmail Fetcher CLI - Click-based implementation.

v4 fixes:
- Proper exit code mapping via exception handler
- Config/CLI flag precedence: CLI overrides config
- Version from package metadata

(No changes needed for v5/v6/v7)
"""
from __future__ import annotations

import functools
import sys
from pathlib import Path

import click

from gmail_fetcher.core.config import AppConfig, ConfigError

EXIT_SUCCESS = 0
EXIT_GENERAL_ERROR = 1
EXIT_USAGE_ERROR = 2
EXIT_AUTH_ERROR = 3
EXIT_NETWORK_ERROR = 4
EXIT_CONFIG_ERROR = 5


def get_version() -> str:
    """Get version from package metadata or fallback."""
    try:
        from importlib.metadata import version
        return version("gmail-fetcher")
    except Exception:
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

    try:
        config = AppConfig.load(config_path, allow_repo_credentials=allow_repo_credentials)
        ctx.obj["config"] = config
    except ConfigError:
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
    default=None,
    help="Maximum emails to fetch (overrides config)",
)
@click.option(
    "--output-dir", "-o",
    type=click.Path(path_type=Path),
    default=None,
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

    click.echo(f"Would delete emails matching: {query}")


@main.command()
@click.argument("input_path", type=click.Path(exists=True, path_type=Path))
@click.pass_context
@handle_errors
def analyze(ctx: click.Context, input_path: Path) -> None:
    """Analyze email data."""
    click.echo(f"Analyzing: {input_path}")


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

## 6. Package `__init__.py`

```python
# src/gmail_fetcher/__init__.py
"""Gmail Fetcher - Gmail backup, analysis, and management suite."""

__version__ = "2.0.0"
__all__ = ["__version__"]
```

---

## 7. CI Workflow (v7 - Fixed Baseline Invocation)

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

      # Use pwsh for all platforms (cross-platform PowerShell)
      - name: Import resolution check
        shell: pwsh
        run: |
          $tempDir = [System.IO.Path]::GetTempPath()
          Push-Location $tempDir
          try {
              python -c @"
          import gmail_fetcher
          from gmail_fetcher.cli.main import main
          from gmail_fetcher.core.config import AppConfig
          print('Version:', gmail_fetcher.__version__)
          print('File:', gmail_fetcher.__file__)
          print('Imports OK')
          "@
              if ($LASTEXITCODE -ne 0) { throw "Import check failed" }
          } finally {
              Pop-Location
          }

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

  build-validation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Clean and build package
        run: |
          rm -rf dist/
          pip install build
          python -m build

      - name: Verify single wheel exists
        run: |
          WHEEL_COUNT=$(ls dist/*.whl 2>/dev/null | wc -l)
          if [ "$WHEEL_COUNT" -ne 1 ]; then
            echo "ERROR: Expected 1 wheel, found $WHEEL_COUNT"
            ls -la dist/
            exit 1
          fi
          echo "Found wheel: $(ls dist/*.whl)"

      - name: Install wheel in clean venv
        run: |
          python -m venv /tmp/test-venv
          /tmp/test-venv/bin/pip install dist/gmail_fetcher-*.whl

      - name: Verify installation
        run: |
          cd /tmp
          /tmp/test-venv/bin/python -c "
          import gmail_fetcher
          print('Version:', gmail_fetcher.__version__)
          print('File:', gmail_fetcher.__file__)
          assert gmail_fetcher.__version__ == '2.0.0', 'Version mismatch'
          assert 'site-packages' in gmail_fetcher.__file__, 'Not installed in site-packages'

          from gmail_fetcher.cli.main import main
          from gmail_fetcher.core.config import AppConfig
          print('All imports OK')
          "

      - name: Verify CLI works
        run: |
          /tmp/test-venv/bin/gmail-fetcher --version
          /tmp/test-venv/bin/gmail-fetcher --help

  # v7 FIX: Explicit pwsh invocation to avoid CRLF/exec issues
  baseline-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run baseline measurements
        shell: pwsh
        run: |
          pwsh -NoProfile -File ./scripts/audit/baseline.ps1 -OutputDir "docs/audit"

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

  release-dod:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4

      - name: Check no forbidden files exist
        run: |
          errors=0

          if [ -f "main.py" ]; then
            echo "WARNING: main.py exists - ensure it's documented as legacy shim"
          fi

          for dir in src/analysis src/deletion src/handlers src/cli src/core src/parsers src/plugins src/tools src/utils; do
            if [ -d "$dir" ] && [ ! -d "src/gmail_fetcher" ]; then
              echo "ERROR: $dir exists but src/gmail_fetcher doesn't - migration incomplete"
              errors=1
            fi
          done

          if git ls-files | grep -qE '(credentials|token)\.json$'; then
            echo "ERROR: Credentials or tokens tracked in git"
            errors=1
          fi

          if git ls-files | grep -qE '\.log$'; then
            echo "ERROR: Log files tracked in git"
            errors=1
          fi

          exit $errors
```

---

## 8. Move Script

```powershell
#!/usr/bin/env pwsh
# scripts/migration/move_to_package.ps1
<#
.SYNOPSIS
    Moves source files to package namespace structure.

v4 fixes:
- Preflight checks (destination doesn't exist, clean working tree)
- Always writes __init__.py with version
- Post-move validation

v5 fixes:
- Properly handles both tracked and untracked src/__init__.py
- Validates removal

(No changes needed for v6/v7)
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

$gitStatus = git status --porcelain
if ($gitStatus -and -not $Force) {
    Write-Host "ERROR: Working tree is not clean. Commit or stash changes first." -ForegroundColor Red
    Write-Host "Use -Force to override (not recommended)." -ForegroundColor Yellow
    exit 1
}

if ((Test-Path $targetDir) -and -not $Force) {
    Write-Host "ERROR: $targetDir already exists. Remove it first or use -Force." -ForegroundColor Red
    exit 1
}

Write-Host "[OK] Preflight checks passed" -ForegroundColor Green

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

$pytypedPath = "$targetDir/py.typed"
if ($DryRun) {
    Write-Host "[DRY-RUN] Write $pytypedPath"
} else {
    Set-Content -Path $pytypedPath -Value "" -Encoding UTF8
    Write-Host "[CREATED] $pytypedPath" -ForegroundColor Green
}

# Handle old src/__init__.py (tracked OR untracked)
$oldInit = "src/__init__.py"
if (Test-Path $oldInit) {
    if ($DryRun) {
        Write-Host "[DRY-RUN] Remove $oldInit (tracked or untracked)"
    } else {
        # Check if tracked
        $isTracked = git ls-files --error-unmatch $oldInit 2>$null
        if ($LASTEXITCODE -eq 0) {
            git rm $oldInit
            Write-Host "[GIT-REMOVED] $oldInit (was tracked)" -ForegroundColor Yellow
        } else {
            Remove-Item $oldInit -Force
            Write-Host "[REMOVED] $oldInit (was untracked)" -ForegroundColor Yellow
        }

        # Validate removal
        if (Test-Path $oldInit) {
            Write-Host "[ERROR] Failed to remove $oldInit" -ForegroundColor Red
            exit 1
        }
    }
}

# Post-move validation
if (-not $DryRun) {
    Write-Host ""
    Write-Host "=== Post-Move Validation ===" -ForegroundColor Cyan

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

    # Verify no old __init__.py remains
    if (Test-Path "src/__init__.py") {
        Write-Host "[FAIL] src/__init__.py still exists" -ForegroundColor Red
        $allOk = $false
    } else {
        Write-Host "[OK] src/__init__.py removed" -ForegroundColor Green
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

## 9. Release DoD Checks

```powershell
#!/usr/bin/env pwsh
# scripts/validation/release_checks.ps1
<#
.SYNOPSIS
    Must-pass release checks. Run before tagging a release.

v5 fixes:
- Absolute path handling using $repoRoot throughout
- Clean dist/ before build
- Select wheel by exact name pattern
- Use Push-Location/Pop-Location for safe navigation

(No changes needed for v6/v7)
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

# Check 1: Build and install wheel
Write-Host "Check 1: Build and install wheel" -ForegroundColor Yellow
Write-Host "---"

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

    # Select wheel by exact pattern, verify single wheel
    $wheels = Get-ChildItem (Join-Path $distPath "gmail_fetcher-*.whl")
    if ($wheels.Count -ne 1) {
        throw "Expected 1 wheel, found $($wheels.Count): $($wheels.Name -join ', ')"
    }
    $wheelPath = $wheels[0].FullName
    Write-Host "[OK] Single wheel found: $($wheels[0].Name)" -ForegroundColor Green

    # Create venv and install
    python -m venv $venvPath
    $venvPython = Join-Path $venvPath "Scripts\python.exe"
    $venvPip = Join-Path $venvPath "Scripts\pip.exe"
    $venvCli = Join-Path $venvPath "Scripts\gmail-fetcher.exe"

    & $venvPip install --quiet $wheelPath
    if ($LASTEXITCODE -ne 0) { throw "Wheel installation failed" }
    Write-Host "[OK] Wheel installed" -ForegroundColor Green

    # Import checks from temp dir using absolute venv paths
    $tempDir = [System.IO.Path]::GetTempPath()
    Push-Location $tempDir
    try {
        $output = & $venvPython -c @"
import gmail_fetcher
print(f'Version: {gmail_fetcher.__version__}')
print(f'File: {gmail_fetcher.__file__}')
from gmail_fetcher.cli.main import main
from gmail_fetcher.core.config import AppConfig
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

# Check 2: Tests pass from outside repo
Write-Host "Check 2: Tests from outside repo" -ForegroundColor Yellow
Write-Host "---"

$venvPath2 = Join-Path $repoRoot ".test-check-venv"

try {
    if (Test-Path $venvPath2) { Remove-Item -Recurse -Force $venvPath2 }

    python -m venv $venvPath2
    $venvPip2 = Join-Path $venvPath2 "Scripts\pip.exe"
    $venvPytest = Join-Path $venvPath2 "Scripts\pytest.exe"

    Push-Location $repoRoot
    try {
        & $venvPip2 install --quiet -e ".[dev]"
        if ($LASTEXITCODE -ne 0) { throw "Dev install failed" }
    } finally {
        Pop-Location
    }

    # Run tests from temp directory using absolute paths
    $tempDir = [System.IO.Path]::GetTempPath()
    $testsPath = Join-Path $repoRoot "tests"

    Push-Location $tempDir
    try {
        & $venvPytest $testsPath -m "not integration and not api" -q
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

# Check 3: Security checks
Write-Host "Check 3: Security checks" -ForegroundColor Yellow
Write-Host "---"

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

---

## 10. Summary: All v6 Issues Fixed in v7

| # | Issue | Fix |
|---|-------|-----|
| 1 | baseline.ps1 checks pre-migration paths only | Added `src/gmail_fetcher/cli/main.py`, `src/gmail_fetcher/__main__.py`, `src/gmail_fetcher/analysis` to path checks |
| 2 | CI baseline invocation fails on Ubuntu | Changed to `pwsh -NoProfile -File ./scripts/audit/baseline.ps1` |
| 3 | Config `resolve_path()` throws TypeError | Added `isinstance(raw, str)` check before `Path()` call |

### Baseline Targets (v7)

| Metric | Target | Rationale |
|--------|--------|-----------|
| `max_folder_depth` | 3 | Keep structure shallow |
| `sys_path_inserts` | 0 | No sys.path hacks allowed |
| `config_locations` | 1 | Only `src/gmail_fetcher/analysis` expected post-migration |
| `entry_points` | 2 | `cli/main.py` + `__main__.py` post-migration |
| `hidden_docs` | 0 | No docs/claude-docs files |

---

## v7 Verification Commands

### Baseline smoke (cross-platform)
```bash
pwsh -NoProfile -File scripts/audit/baseline.ps1 -OutputDir docs/audit
ls docs/audit/*_baseline.json 2>/dev/null || dir docs/audit/*_baseline.json
```

### Config type-hardening test
```powershell
@'
{"credentials_path": 123}
'@ | Set-Content -Encoding utf8 .\bad_config.json

python -c "from pathlib import Path; from gmail_fetcher.core.config import AppConfig;
try: AppConfig.load(Path('bad_config.json'))
except Exception as e: print(type(e).__name__, e)"
# Expect: ConfigError credentials_path must be string path, got int

Remove-Item .\bad_config.json
```

### Wheel contains correct package
```bash
rm -rf dist/ && python -m build
python -c "import glob, zipfile; w=glob.glob('dist/*.whl')[0]; z=zipfile.ZipFile(w);
assert any(n=='gmail_fetcher/__init__.py' for n in z.namelist()); print('OK')"
```

---

**Document Version**: v7
**Release Version**: 2.0.0
**Status**: Executable - all v6 bugs fixed
