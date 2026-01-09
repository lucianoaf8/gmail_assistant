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
    $repoRoot = $PWD.Path
    Set-Location $tempDir
    $output = & "$repoRoot/$venvPath/Scripts/python" -c @"
import gmail_assistant
print(f'Version: {gmail_assistant.__version__}')
from gmail_assistant.cli.main import main
from gmail_assistant.core.config import AppConfig
print('All imports OK')
"@
    if ($LASTEXITCODE -ne 0) { throw "Import check failed" }
    Write-Host $output
    Write-Host "[OK] Import resolution passed" -ForegroundColor Green

    # CLI check
    & "$repoRoot/$venvPath/Scripts/gmail-fetcher" --version
    if ($LASTEXITCODE -ne 0) { throw "CLI --version failed" }
    Write-Host "[OK] CLI works" -ForegroundColor Green

} catch {
    Write-Host "[FAIL] Check 1 failed: $_" -ForegroundColor Red
    $exitCode = 1
} finally {
    Set-Location $repoRoot
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
    $repoRoot = $PWD.Path
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
