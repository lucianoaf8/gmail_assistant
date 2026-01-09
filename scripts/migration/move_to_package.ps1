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

$targetDir = "src/gmail_assistant"
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
"""Entry point for python -m gmail_assistant."""
from gmail_assistant.cli.main import main

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
