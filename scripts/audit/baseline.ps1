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
$commitSha = & git rev-parse HEAD 2>$null
if (-not $commitSha) {
    $commitSha = "no-commits"
}

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
            $segments = @(($relativePath -split '[\\/]') | Where-Object { $_ -ne '' })
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
