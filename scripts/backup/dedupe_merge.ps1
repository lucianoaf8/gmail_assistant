<#!
.SYNOPSIS
    Deduplicate and merge Gmail backups so only one copy of each message remains.

.DESCRIPTION
    Scans a Source backup (e.g., backup_unread_part2) and a Destination backup (e.g., backup_unread)
    for specific years (e.g., 2024, 2025). Uses the Gmail message ID embedded in filenames
    (the suffix before .eml/.md) to detect duplicates. Moves missing files to Destination and
    resolves conflicts so only one copy of each .eml and .md exists.

    Conflict policy is configurable: prefer the larger file (default), the destination, or the source.
    A DryRun mode previews actions using -WhatIf.

.PARAMETER Source
    Source backup root (default: backup_unread_part2)

.PARAMETER Destination
    Destination backup root (default: backup_unread)

.PARAMETER Years
    Years to process (default: 2024, 2025)

.PARAMETER Prefer
    Conflict policy: larger | destination | source (default: larger)

.PARAMETER DryRun
    Preview actions without making changes

.EXAMPLE
    .\dedupe_merge.ps1 -Source backup_unread_part2 -Destination backup_unread -Years 2024,2025 -DryRun

.EXAMPLE
    .\dedupe_merge.ps1 -Source backup_unread_part2 -Destination backup_unread -Years 2024,2025 -Prefer larger
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [string]$Source = "backup_unread_part2",

    [Parameter(Mandatory=$false)]
    [string]$Destination = "backup_unread",

    [Parameter(Mandatory=$false)]
    [int[]]$Years = @(2024, 2025),

    [ValidateSet('larger','destination','source')]
    [string]$Prefer = 'larger',

    [switch]$DryRun
)

function Get-MessageId {
    param([Parameter(Mandatory=$true)][string]$Name)
    # Extract token after the last underscore and before extension
    # Matches hex/decimal strings of length >= 8
    $m = [regex]::Match($Name, '_([0-9A-Fa-f]{8,})\.(eml|md)$')
    if ($m.Success) { return $m.Groups[1].Value }
    return $null
}

function Ensure-Dir { param([string]$Path) if (-not (Test-Path -LiteralPath $Path)) { New-Item -ItemType Directory -Path $Path -Force | Out-Null } }

function Larger-Of {
    param([System.IO.FileInfo]$A, [System.IO.FileInfo]$B)
    if ($A.Length -ge $B.Length) { return $A } else { return $B }
}

if (-not (Test-Path -LiteralPath $Source)) { throw "Source not found: $Source" }
if (-not (Test-Path -LiteralPath $Destination)) { New-Item -ItemType Directory -Path $Destination | Out-Null }

$whatIf = @{}
if ($DryRun) { $whatIf = @{WhatIf=$true} }

Write-Host "Deduping years $($Years -join ', ') from '$Source' into '$Destination' (prefer=$Prefer)" -ForegroundColor Cyan
if ($DryRun) { Write-Host "DRY-RUN mode: no changes will be made" -ForegroundColor Yellow }

# Build destination index: id -> path per extension
$destIdx = @{ eml = @{}, md = @{} }
foreach ($year in $Years) {
    $yrPath = Join-Path $Destination $year
    if (-not (Test-Path -LiteralPath $yrPath)) { continue }
    Get-ChildItem -LiteralPath $yrPath -Recurse -File | ForEach-Object {
        $id = Get-MessageId -Name $_.Name
        if ($null -ne $id) {
            $ext = $_.Extension.ToLower().TrimStart('.')
            $destIdx[$ext][$id] = $_.FullName
        }
    }
}

$moved=0; $deleted=0; $replaced=0; $skipped=0

foreach ($year in $Years) {
    $srcYear = Join-Path $Source $year
    if (-not (Test-Path -LiteralPath $srcYear)) { continue }

    # Only month subfolders 01..12
    Get-ChildItem -LiteralPath $srcYear -Directory | Where-Object { $_.Name -match '^[0-1][0-9]$' } | ForEach-Object {
        $srcMonth = $_.FullName
        $dstMonth = Join-Path (Join-Path $Destination $year) $_.Name
        Ensure-Dir $dstMonth

        Get-ChildItem -LiteralPath $srcMonth -File | ForEach-Object {
            $srcFile = $_
            $ext = $srcFile.Extension.ToLower().TrimStart('.')
            if ($ext -notin @('eml','md')) { return }
            $id = Get-MessageId -Name $srcFile.Name
            if ($null -eq $id) { return }

            $destPath = $null
            if ($destIdx[$ext].ContainsKey($id)) { $destPath = $destIdx[$ext][$id] }
            else { $destPath = Join-Path $dstMonth $srcFile.Name }

            if (Test-Path -LiteralPath $destPath) {
                $dstFile = Get-Item -LiteralPath $destPath
                if ($srcFile.Length -eq $dstFile.Length) {
                    # Same size -> assume duplicate, remove source copy
                    Remove-Item -LiteralPath $srcFile.FullName @whatIf
                    $deleted++
                } else {
                    switch ($Prefer) {
                        'larger' {
                            $keep = Larger-Of -A $srcFile -B $dstFile
                            if ($keep.FullName -eq $srcFile.FullName) {
                                # Replace destination with larger source
                                Move-Item -LiteralPath $srcFile.FullName -Destination $destPath -Force @whatIf
                                $replaced++
                            } else {
                                # Keep destination; drop source
                                Remove-Item -LiteralPath $srcFile.FullName @whatIf
                                $deleted++
                            }
                        }
                        'destination' {
                            Remove-Item -LiteralPath $srcFile.FullName @whatIf
                            $deleted++
                        }
                        'source' {
                            Move-Item -LiteralPath $srcFile.FullName -Destination $destPath -Force @whatIf
                            $replaced++
                        }
                    }
                }
            } else {
                Move-Item -LiteralPath $srcFile.FullName -Destination $destPath @whatIf
                $moved++
                $destIdx[$ext][$id] = $destPath
            }
        }
    }
}

# Clean up empty dirs in source years processed
foreach ($year in $Years) {
    $srcYear = Join-Path $Source $year
    if (-not (Test-Path -LiteralPath $srcYear)) { continue }
    Get-ChildItem -LiteralPath $srcYear -Recurse -Directory | Sort-Object FullName -Descending | ForEach-Object {
        if (-not (Get-ChildItem -LiteralPath $_.FullName -Force)) {
            Remove-Item -LiteralPath $_.FullName -Force @whatIf
        }
    }
}

Write-Host ""; Write-Host "Summary" -ForegroundColor Cyan
Write-Host ("  Moved     : {0}" -f $moved)
Write-Host ("  Replaced  : {0}" -f $replaced)
Write-Host ("  Deleted   : {0}" -f $deleted)
Write-Host ("  Skipped   : {0}" -f $skipped)
Write-Host "Done." -ForegroundColor Green

