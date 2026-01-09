<#!
.SYNOPSIS
    Merge selected years (by year/month) from one Gmail backup into another.

.DESCRIPTION
    Moves files from Source\<YEAR>\<MM> into Destination\<YEAR>\<MM>.
    - Creates year/month folders as needed.
    - Skips exact duplicates (same name and content).
    - If a file with the same name but different content exists, appends _dup, _dup2, ... to the filename.
    - Supports a dry-run mode to preview actions.

.PARAMETER Source
    Path to the source backup folder (e.g., backup_unread_part2).

.PARAMETER Destination
    Path to the destination backup folder (e.g., backup_unread).

.PARAMETER Years
    Years to move (e.g., 2024, 2025).

.PARAMETER Overwrite
    Overwrite existing files with the same path (dangerous). If not set, the script skips exact duplicates and renames conflicts.

.PARAMETER DryRun
    Preview the operations without making changes.

.EXAMPLE
    .\move_backup_years.ps1 -Source "backup_unread_part2" -Destination "backup_unread" -Years 2024,2025 -DryRun

.EXAMPLE
    .\move_backup_years.ps1 -Source "backup_unread_part2" -Destination "backup_unread" -Years 2024,2025
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [string]$Source = "backup_unread_part2",

    [Parameter(Mandatory=$false)]
    [string]$Destination = "backup_unread",

    [Parameter(Mandatory=$false)]
    [int[]]$Years = @(2024, 2025),

    [switch]$Overwrite,

    [switch]$DryRun
)

function New-UniquePath {
    param(
        [Parameter(Mandatory=$true)][string]$Path
    )
    if (-not (Test-Path -LiteralPath $Path)) { return $Path }
    $dir = Split-Path -LiteralPath $Path -Parent
    $name = Split-Path -LiteralPath $Path -Leaf
    $base = [System.IO.Path]::GetFileNameWithoutExtension($name)
    $ext  = [System.IO.Path]::GetExtension($name)
    $i = 1
    do {
        $candidate = Join-Path $dir ("{0}_dup{1}{2}" -f $base, $i, $ext)
        $i++
    } while (Test-Path -LiteralPath $candidate)
    return $candidate
}

if (-not (Test-Path -LiteralPath $Source)) {
    Write-Error "Source path not found: $Source"
    exit 1
}

if (-not (Test-Path -LiteralPath $Destination)) {
    if ($DryRun) {
        Write-Host "[DRY-RUN] Would create destination: $Destination" -ForegroundColor Yellow
    } else {
        New-Item -ItemType Directory -Path $Destination | Out-Null
    }
}

Write-Host "Merging years $($Years -join ', ') from '$Source' into '$Destination'" -ForegroundColor Cyan
if ($DryRun) { Write-Host "Running in DRY-RUN mode (no changes will be made)" -ForegroundColor Yellow }
if ($Overwrite) { Write-Host "Overwrite is ENABLED (existing files will be replaced)" -ForegroundColor Red }

$moved = 0
$skipped = 0
$renamed = 0
$overwritten = 0
$missingYears = @()

foreach ($year in $Years) {
    $yearPath = Join-Path $Source $year
    if (-not (Test-Path -LiteralPath $yearPath)) {
        $missingYears += $year
        continue
    }

    # Only consider MM subfolders (e.g., 01..12)
    Get-ChildItem -LiteralPath $yearPath -Directory | Where-Object { $_.Name -match '^[0-1][0-9]$' } | ForEach-Object {
        $monthDir = $_.FullName
        $destMonth = Join-Path (Join-Path $Destination $year) $_.Name

        if (-not (Test-Path -LiteralPath $destMonth)) {
            if ($DryRun) {
                Write-Host "[DRY-RUN] Would create: $destMonth" -ForegroundColor Yellow
            } else {
                New-Item -ItemType Directory -Path $destMonth -Force | Out-Null
            }
        }

        Get-ChildItem -LiteralPath $monthDir -File | ForEach-Object {
            $srcFile = $_.FullName
            $destFile = Join-Path $destMonth $_.Name

            if (Test-Path -LiteralPath $destFile) {
                if ($Overwrite) {
                    if ($DryRun) {
                        Write-Host "[DRY-RUN] Overwrite: $destFile" -ForegroundColor DarkYellow
                    } else {
                        Move-Item -LiteralPath $srcFile -Destination $destFile -Force
                    }
                    $overwritten++
                } else {
                    # Check if exact duplicate (same content)
                    $hashSrc = Get-FileHash -Algorithm SHA256 -LiteralPath $srcFile
                    $hashDst = Get-FileHash -Algorithm SHA256 -LiteralPath $destFile
                    if ($hashSrc.Hash -eq $hashDst.Hash) {
                        if ($DryRun) { Write-Host "[DRY-RUN] Skip (duplicate): $destFile" -ForegroundColor DarkGray }
                        else { Remove-Item -LiteralPath $srcFile } # remove duplicate from source after confirming
                        $skipped++
                    } else {
                        $unique = New-UniquePath -Path $destFile
                        if ($DryRun) {
                            Write-Host "[DRY-RUN] Rename conflict -> $unique" -ForegroundColor DarkCyan
                        } else {
                            Move-Item -LiteralPath $srcFile -Destination $unique
                        }
                        $renamed++
                    }
                }
            } else {
                if ($DryRun) {
                    Write-Host "[DRY-RUN] Move: $srcFile -> $destFile" -ForegroundColor Gray
                } else {
                    Move-Item -LiteralPath $srcFile -Destination $destFile
                }
                $moved++
            }
        }
    }
}

Write-Host ""; Write-Host "Summary" -ForegroundColor Cyan
Write-Host ("  Moved       : {0}" -f $moved)
Write-Host ("  Skipped dup : {0}" -f $skipped)
Write-Host ("  Renamed dup : {0}" -f $renamed)
Write-Host ("  Overwritten : {0}" -f $overwritten)
if ($missingYears.Count -gt 0) {
    Write-Host ("  Missing years in source: {0}" -f ($missingYears -join ', ')) -ForegroundColor Yellow
}

Write-Host "Done." -ForegroundColor Green

