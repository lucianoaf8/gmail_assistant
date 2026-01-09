#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Unified verification pipeline for Gmail Assistant.
.DESCRIPTION
    Executes the complete verification sequence:
    1. Baseline measurements
    2. Import policy check
    3. Package build
    4. Wheel installation test (isolated)
    5. Import resolution check (isolated)
    6. Test suite with coverage gate
    7. Security checks
    8. CLI smoke test
    9. Release checks (full DoD validation)
.PARAMETER SkipBuild
    Skip package build (use existing dist/)
.PARAMETER SkipTests
    Skip test suite execution
.PARAMETER SkipReleaseChecks
    Skip release_checks.ps1 (faster iteration)
.EXAMPLE
    .\scripts\verify_all.ps1
    .\scripts\verify_all.ps1 -SkipTests
#>
[CmdletBinding()]
param(
    [switch]$SkipBuild,
    [switch]$SkipTests,
    [switch]$SkipReleaseChecks
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

$exitCode = 0
$results = @{}

function Write-Step {
    param([string]$Name, [string]$Status, [string]$Color = "White")
    $symbol = switch ($Status) {
        "PASS" { "[PASS]"; $Color = "Green" }
        "FAIL" { "[FAIL]"; $Color = "Red" }
        "SKIP" { "[SKIP]"; $Color = "Yellow" }
        "RUN"  { "[....]"; $Color = "Cyan" }
        default { "[????]" }
    }
    Write-Host "$symbol $Name" -ForegroundColor $Color
}

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "    Gmail Assistant - Unified Verification Pipeline            " -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Repo: $repoRoot"
Write-Host "Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host ""

# ============================================================================
# Step 1: Baseline Measurements
# ============================================================================
Write-Host "--- Step 1: Baseline Measurements ---" -ForegroundColor Yellow
Write-Step "Baseline" "RUN"

try {
    & "$repoRoot/scripts/audit/baseline.ps1" -OutputDir "docs/audit" | Out-Null
    Write-Step "Baseline" "PASS"
    $results["Baseline"] = "PASS"
} catch {
    Write-Step "Baseline" "FAIL"
    Write-Host "  Error: $_" -ForegroundColor Red
    $results["Baseline"] = "FAIL"
    $exitCode = 1
}

Write-Host ""

# ============================================================================
# Step 2: Import Policy Check
# ============================================================================
Write-Host "--- Step 2: Import Policy Check ---" -ForegroundColor Yellow
Write-Step "Import Policy" "RUN"

try {
    $policyResult = python "$repoRoot/scripts/validation/check_import_policy.py"
    if ($LASTEXITCODE -eq 0) {
        Write-Step "Import Policy" "PASS"
        $results["Import Policy"] = "PASS"
    } else {
        Write-Step "Import Policy" "FAIL"
        Write-Host $policyResult
        $results["Import Policy"] = "FAIL"
        $exitCode = 1
    }
} catch {
    Write-Step "Import Policy" "FAIL"
    Write-Host "  Error: $_" -ForegroundColor Red
    $results["Import Policy"] = "FAIL"
    $exitCode = 1
}

Write-Host ""

# ============================================================================
# Step 3: Package Build
# ============================================================================
Write-Host "--- Step 3: Package Build ---" -ForegroundColor Yellow

if ($SkipBuild) {
    Write-Step "Build" "SKIP"
    $results["Build"] = "SKIP"
} else {
    Write-Step "Build" "RUN"

    try {
        # Clean dist/
        if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }

        # Install build tool
        python -m pip install --quiet build

        # Build
        python -m build --quiet 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "Build failed" }

        # Verify single wheel
        $wheels = Get-ChildItem dist -Filter *.whl -ErrorAction SilentlyContinue
        if ($wheels.Count -ne 1) {
            throw "Expected 1 wheel, found $($wheels.Count)"
        }

        Write-Step "Build" "PASS"
        Write-Host "  Wheel: $($wheels[0].Name)" -ForegroundColor Gray
        $results["Build"] = "PASS"
    } catch {
        Write-Step "Build" "FAIL"
        Write-Host "  Error: $_" -ForegroundColor Red
        $results["Build"] = "FAIL"
        $exitCode = 1
    }
}

Write-Host ""

# ============================================================================
# Step 4: Wheel Installation Test (Isolated)
# ============================================================================
Write-Host "--- Step 4: Wheel Installation Test ---" -ForegroundColor Yellow
Write-Step "Install Test" "RUN"

$testVenv = Join-Path $repoRoot ".verify-venv"

try {
    # Clean up existing venv
    if (Test-Path $testVenv) { Remove-Item -Recurse -Force $testVenv }

    # Create venv
    python -m venv $testVenv
    $venvPip = Join-Path $testVenv "Scripts/pip.exe"
    $venvPython = Join-Path $testVenv "Scripts/python.exe"
    if (-not (Test-Path $venvPip)) {
        $venvPip = Join-Path $testVenv "Scripts/pip"
        $venvPython = Join-Path $testVenv "Scripts/python"
    }

    # Find wheel
    $wheel = Get-ChildItem dist -Filter *.whl | Select-Object -First 1
    if (-not $wheel) { throw "No wheel found in dist/" }

    # Install
    & $venvPip install --quiet $wheel.FullName
    if ($LASTEXITCODE -ne 0) { throw "Wheel installation failed" }

    # Import test from temp directory (isolated execution)
    $tempDir = [System.IO.Path]::GetTempPath()
    Push-Location $tempDir
    try {
        $output = & $venvPython -c "import gmail_assistant; print(gmail_assistant.__version__)"
        if ($LASTEXITCODE -ne 0) { throw "Import failed" }
        Write-Step "Install Test" "PASS"
        Write-Host "  Version: $output" -ForegroundColor Gray
        $results["Install Test"] = "PASS"
    } finally {
        Pop-Location
    }

} catch {
    Write-Step "Install Test" "FAIL"
    Write-Host "  Error: $_" -ForegroundColor Red
    $results["Install Test"] = "FAIL"
    $exitCode = 1
} finally {
    if (Test-Path $testVenv) { Remove-Item -Recurse -Force $testVenv -ErrorAction SilentlyContinue }
}

Write-Host ""

# ============================================================================
# Step 5: Import Resolution Check (Isolated)
# ============================================================================
Write-Host "--- Step 5: Import Resolution Check ---" -ForegroundColor Yellow
Write-Step "Import Resolution" "RUN"

$resolutionVenv = Join-Path $repoRoot ".resolution-venv"

try {
    # Create isolated venv
    if (Test-Path $resolutionVenv) { Remove-Item -Recurse -Force $resolutionVenv }
    python -m venv $resolutionVenv

    $venvPip = Join-Path $resolutionVenv "Scripts/pip.exe"
    $venvPython = Join-Path $resolutionVenv "Scripts/python.exe"
    if (-not (Test-Path $venvPip)) {
        $venvPip = Join-Path $resolutionVenv "Scripts/pip"
        $venvPython = Join-Path $resolutionVenv "Scripts/python"
    }

    # Install wheel (not editable)
    $wheel = Get-ChildItem dist -Filter *.whl | Select-Object -First 1
    & $venvPip install --quiet $wheel.FullName

    # Run from temp directory for true isolation
    $tempDir = [System.IO.Path]::GetTempPath()
    $scriptContent = Get-Content "$repoRoot/scripts/validation/check_import_resolution.py" -Raw
    $tempScript = Join-Path $tempDir "check_import_resolution.py"
    Set-Content -Path $tempScript -Value $scriptContent -Encoding UTF8

    Push-Location $tempDir
    try {
        & $venvPython $tempScript
        if ($LASTEXITCODE -eq 0) {
            Write-Step "Import Resolution" "PASS"
            $results["Import Resolution"] = "PASS"
        } else {
            Write-Step "Import Resolution" "FAIL"
            $results["Import Resolution"] = "FAIL"
            $exitCode = 1
        }
    } finally {
        Pop-Location
        Remove-Item $tempScript -ErrorAction SilentlyContinue
    }

} catch {
    Write-Step "Import Resolution" "FAIL"
    Write-Host "  Error: $_" -ForegroundColor Red
    $results["Import Resolution"] = "FAIL"
    $exitCode = 1
} finally {
    if (Test-Path $resolutionVenv) { Remove-Item -Recurse -Force $resolutionVenv -ErrorAction SilentlyContinue }
}

Write-Host ""

# ============================================================================
# Step 6: Test Suite with Coverage Gate
# ============================================================================
Write-Host "--- Step 6: Test Suite ---" -ForegroundColor Yellow

if ($SkipTests) {
    Write-Step "Tests" "SKIP"
    $results["Tests"] = "SKIP"
} else {
    Write-Step "Tests" "RUN"

    try {
        # Install dev dependencies
        pip install -e ".[dev]" --quiet

        # Run tests with coverage (disable playwright plugin to avoid conflicts)
        python -m pytest tests/unit/ -q --tb=short --cov=src/gmail_assistant --cov-report=term --cov-fail-under=70 -p no:playwright 2>&1

        if ($LASTEXITCODE -eq 0) {
            Write-Step "Tests" "PASS"
            $results["Tests"] = "PASS"
        } else {
            Write-Step "Tests" "FAIL"
            $results["Tests"] = "FAIL"
            $exitCode = 1
        }
    } catch {
        Write-Step "Tests" "FAIL"
        Write-Host "  Error: $_" -ForegroundColor Red
        $results["Tests"] = "FAIL"
        $exitCode = 1
    }
}

Write-Host ""

# ============================================================================
# Step 7: Security Checks
# ============================================================================
Write-Host "--- Step 7: Security Checks ---" -ForegroundColor Yellow
Write-Step "Security" "RUN"

try {
    $securityOk = $true

    # Check no credentials tracked
    $tracked = git ls-files | Select-String -Pattern "(credentials|token)\.json$"
    if ($tracked) {
        Write-Host "  [FAIL] Credentials tracked: $tracked" -ForegroundColor Red
        $securityOk = $false
    }

    # Check no log files tracked
    $logs = git ls-files | Select-String -Pattern "\.log$"
    if ($logs) {
        Write-Host "  [FAIL] Log files tracked: $logs" -ForegroundColor Red
        $securityOk = $false
    }

    # Gitleaks (optional)
    $gitleaks = Get-Command gitleaks -ErrorAction SilentlyContinue
    if ($gitleaks) {
        gitleaks detect --no-banner --exit-code 1 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  [FAIL] Gitleaks found secrets" -ForegroundColor Red
            $securityOk = $false
        }
    }

    if ($securityOk) {
        Write-Step "Security" "PASS"
        $results["Security"] = "PASS"
    } else {
        Write-Step "Security" "FAIL"
        $results["Security"] = "FAIL"
        $exitCode = 1
    }

} catch {
    Write-Step "Security" "FAIL"
    Write-Host "  Error: $_" -ForegroundColor Red
    $results["Security"] = "FAIL"
    $exitCode = 1
}

Write-Host ""

# ============================================================================
# Step 8: CLI Smoke Test
# ============================================================================
Write-Host "--- Step 8: CLI Smoke Test ---" -ForegroundColor Yellow
Write-Step "CLI Smoke" "RUN"

try {
    # Ensure package is installed
    pip install -e . --quiet 2>&1 | Out-Null

    # Test --version
    $version = gmail-assistant --version 2>&1
    if ($LASTEXITCODE -ne 0) { throw "CLI --version failed" }

    # Test --help
    $help = gmail-assistant --help 2>&1
    if ($LASTEXITCODE -ne 0) { throw "CLI --help failed" }

    # Test subcommand helps
    $subcommands = @("fetch", "delete", "analyze", "auth", "config")
    foreach ($cmd in $subcommands) {
        $subHelp = gmail-assistant $cmd --help 2>&1
        if ($LASTEXITCODE -ne 0) { throw "CLI $cmd --help failed" }
    }

    Write-Step "CLI Smoke" "PASS"
    $results["CLI Smoke"] = "PASS"

} catch {
    Write-Step "CLI Smoke" "FAIL"
    Write-Host "  Error: $_" -ForegroundColor Red
    $results["CLI Smoke"] = "FAIL"
    $exitCode = 1
}

Write-Host ""

# ============================================================================
# Step 9: Release Checks
# ============================================================================
Write-Host "--- Step 9: Release Checks ---" -ForegroundColor Yellow

if ($SkipReleaseChecks) {
    Write-Step "Release Checks" "SKIP"
    $results["Release Checks"] = "SKIP"
} else {
    Write-Step "Release Checks" "RUN"

    try {
        & "$repoRoot/scripts/validation/release_checks.ps1"
        if ($LASTEXITCODE -eq 0) {
            Write-Step "Release Checks" "PASS"
            $results["Release Checks"] = "PASS"
        } else {
            Write-Step "Release Checks" "FAIL"
            $results["Release Checks"] = "FAIL"
            $exitCode = 1
        }
    } catch {
        Write-Step "Release Checks" "FAIL"
        Write-Host "  Error: $_" -ForegroundColor Red
        $results["Release Checks"] = "FAIL"
        $exitCode = 1
    }
}

Write-Host ""

# ============================================================================
# Summary
# ============================================================================
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "                        SUMMARY                                 " -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

$results.GetEnumerator() | Sort-Object Name | ForEach-Object {
    $color = switch ($_.Value) {
        "PASS" { "Green" }
        "FAIL" { "Red" }
        "SKIP" { "Yellow" }
        default { "White" }
    }
    Write-Host "  $($_.Value.PadRight(6)) $($_.Key)" -ForegroundColor $color
}

Write-Host ""

if ($exitCode -eq 0) {
    Write-Host "================================================================" -ForegroundColor Green
    Write-Host "  ALL CHECKS PASSED - Ready for release" -ForegroundColor Green
    Write-Host "================================================================" -ForegroundColor Green
} else {
    Write-Host "================================================================" -ForegroundColor Red
    Write-Host "  CHECKS FAILED - Review errors above" -ForegroundColor Red
    Write-Host "================================================================" -ForegroundColor Red
}

Write-Host ""
exit $exitCode
