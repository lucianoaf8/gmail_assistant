<#!
.SYNOPSIS
    Remove duplicate emails within a backup tree so only one .eml and one .md per message ID remain.

.DESCRIPTION
    Scans ROOT for files under specified Years (e.g., 2024, 2025). For each message ID (parsed from
    filename suffix before extension), keeps a single file per extension (.eml, .md). Preference is
    to keep the largest file; ties are broken by last write time (newer wins).

.PARAMETER Root
    Backup root to clean (default: backup_unread)

.PARAMETER Years
    Years to process (default: 2024, 2025)

.PARAMETER DryRun
    Preview actions without making changes

.EXAMPLE
    .\dedupe_in_place.ps1 -Root backup_unread -Years 2024,2025 -DryRun

.EXAMPLE
    .\dedupe_in_place.ps1 -Root backup_unread -Years 2024,2025
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [string]$Root = "backup_unread",

    [Parameter(Mandatory=$false)]
    [int[]]$Years = @(2024, 2025),

    [switch]$DryRun
)

function Get-MessageId {
    param([Parameter(Mandatory=$true)][string]$Name)
    $m = [regex]::Match($Name, '_([0-9A-Fa-f]{8,})\.(eml|md)$')
    if ($m.Success) { return $m.Groups[1].Value }
    return $null
}

$whatIf = @{}
if ($DryRun) { $whatIf = @{WhatIf=$true} }

Write-Host "Deduplicating in '$Root' for years $($Years -join ', ')" -ForegroundColor Cyan
if ($DryRun) { Write-Host "DRY-RUN mode: no changes will be made" -ForegroundColor Yellow }

$toDelete = @()

foreach ($year in $Years) {
    $yrPath = Join-Path $Root $year
    if (-not (Test-Path -LiteralPath $yrPath)) { continue }

    $groups = @{}
    Get-ChildItem -LiteralPath $yrPath -Recurse -File | Where-Object { $_.Extension -match '^\.(eml|md)$' } | ForEach-Object {
        $id = Get-MessageId -Name $_.Name
        if ($null -eq $id) { return }
        $ext = $_.Extension.ToLower().TrimStart('.')
        $key = "$id|$ext"
        if (-not $groups.ContainsKey($key)) { $groups[$key] = @() }
        $groups[$key] += $_
    }

    foreach ($entry in $groups.GetEnumerator()) {
        $files = $entry.Value
        if ($files.Count -le 1) { continue }
        # Pick the one to keep: largest size, then newest LastWriteTime
        $keep = $files | Sort-Object Length, LastWriteTime -Descending | Select-Object -First 1
        $remove = $files | Where-Object { $_.FullName -ne $keep.FullName }
        foreach ($f in $remove) { $toDelete += $f.FullName }
        Write-Host ("Keeping: {0} and deleting {1} others" -f $keep.Name, ($remove.Count)) -ForegroundColor Gray
    }
}

$toDelete = $toDelete | Sort-Object -Unique
foreach ($p in $toDelete) {
    Remove-Item -LiteralPath $p @whatIf
}

Write-Host ("Deleted duplicates: {0}" -f $toDelete.Count) -ForegroundColor Green

