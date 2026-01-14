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
    @{From="src/handlers"; To="src/gmail_assistant/cli/commands"},
    @{From="src/parsers"; To="src/gmail_assistant/parsers"},
    @{From="src/utils"; To="src/gmail_assistant/utils"}
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
