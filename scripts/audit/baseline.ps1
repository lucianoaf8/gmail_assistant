#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Captures baseline measurements and writes JSON atomically.
.DESCRIPTION
    Measures repository structure metrics against defined targets.
    Outputs JSON file with schema version 1.4 (corrected metric names).
.PARAMETER OutputDir
    Directory for baseline JSON output. Default: docs/audit
.EXAMPLE
    .\scripts\audit\baseline.ps1 -OutputDir docs/audit
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

# Excluded directory names (segment-based)
$excludeNames = @(
    '.git', '__pycache__', 'node_modules', 'backups', '.venv', 'venv',
    '.pytest_cache', '.mypy_cache', '.ruff_cache', 'htmlcov', 'dist', 'build', '*.egg-info'
)

function Test-ShouldExclude {
    param([string]$FullPath)
    $relativePath = $FullPath.Substring($repoRoot.Length).TrimStart('\', '/')
    $segments = @($relativePath -split '[\/]')
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
            $segments = @(($relativePath -split '[\/]') | Where-Object { $_ -ne '' })
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

# Checks for expected post-migration package structure
function Get-PostMigrationPackageModuleCount {
    $expectedModules = @(
        "src/gmail_assistant/core",
        "src/gmail_assistant/cli",
        "src/gmail_assistant/analysis"
    )
    return @($expectedModules | Where-Object { Test-Path (Join-Path $repoRoot $_) }).Count
}

# Legacy structure modules
function Get-LegacyPackageModuleCount {
    $legacy = @("src/core", "src/cli", "src/analysis", "src/handlers")
    return @($legacy | Where-Object { Test-Path (Join-Path $repoRoot $_) }).Count
}

function Get-PythonFileCount {
    $srcPath = Join-Path $repoRoot "src"
    if (-not (Test-Path $srcPath)) { return 0 }
    return @(Get-ChildItem -Path $srcPath -Filter "*.py" -Recurse -File |
        Where-Object { -not (Test-ShouldExclude $_.FullName) }).Count
}

function Get-TestFileCount {
    $testsPath = Join-Path $repoRoot "tests"
    if (-not (Test-Path $testsPath)) { return 0 }
    return @(Get-ChildItem -Path $testsPath -Filter "test_*.py" -Recurse -File |
        Where-Object { -not (Test-ShouldExclude $_.FullName) }).Count
}

function Get-PostMigrationEntryPointCount {
    $entryPoints = @(
        "src/gmail_assistant/cli/main.py",
        "src/gmail_assistant/__main__.py"
    )
    return @($entryPoints | Where-Object { Test-Path (Join-Path $repoRoot $_) }).Count
}

function Get-LegacyEntryPointCount {
    $legacy = @("main.py", "src/cli/main.py")
    return @($legacy | Where-Object { Test-Path (Join-Path $repoRoot $_) }).Count
}

function Get-HiddenDocsCount {
    $claudeDocsPath = Join-Path $repoRoot "docs/claude-docs"
    if (-not (Test-Path $claudeDocsPath)) { return 0 }
    return @(Get-ChildItem -Path $claudeDocsPath -Filter "*.md" -File).Count
}

# Collect measurements
Write-Host "Collecting measurements..." -ForegroundColor Cyan

$measurements = [ordered]@{
    max_folder_depth                  = Get-MaxFolderDepth
    sys_path_inserts                  = Get-SysPathInsertCount
    post_migration_package_modules    = Get-PostMigrationPackageModuleCount
    legacy_package_modules            = Get-LegacyPackageModuleCount
    python_source_files               = Get-PythonFileCount
    test_files                        = Get-TestFileCount
    post_migration_entry_points       = Get-PostMigrationEntryPointCount
    legacy_entry_points               = Get-LegacyEntryPointCount
    hidden_docs                       = Get-HiddenDocsCount
}

$baseline = [ordered]@{
    schema_version                    = "1.4"
    depth_convention                  = "segments_under_repo_root"
    timestamp                         = $timestamp
    commit_sha                        = $commitSha
    repo_root                         = $repoRoot
    measurements                      = $measurements
    targets = [ordered]@{
        max_folder_depth              = 3
        sys_path_inserts              = 0
        post_migration_package_modules = 3
        legacy_package_modules        = 0
        post_migration_entry_points   = 2
        legacy_entry_points           = 0
        hidden_docs                   = 0
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
$allPass = $true
$measurements.GetEnumerator() | ForEach-Object {
    $target = $baseline.targets[$_.Key]
    if ($null -ne $target) {
        $pass = $_.Value -le $target
        # For "post_migration_*" metrics, we want >= target
        if ($_.Key -like "post_migration_*") {
            $pass = $_.Value -ge $target
        }
        $status = if ($pass) { "[PASS]" } else { "[FAIL]" }
        $color = if ($pass) { "Green" } else { "Red" }
        if (-not $pass) { $allPass = $false }
        Write-Host "  $status $($_.Key): $($_.Value) (target: $target)" -ForegroundColor $color
    } else {
        Write-Host "  [INFO] $($_.Key): $($_.Value)" -ForegroundColor Gray
    }
}

Write-Host ""
if ($allPass) {
    Write-Host "All targets met." -ForegroundColor Green
    exit 0
} else {
    Write-Host "Some targets not met." -ForegroundColor Yellow
    exit 0  # Non-blocking for pre-migration runs
}
