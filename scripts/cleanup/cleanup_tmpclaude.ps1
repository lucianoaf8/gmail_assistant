# Cleanup tmpclaude-*-cwd and nul files
# Claude Code bug: https://github.com/anthropics/claude-code/issues/17636
# Also prevents nul file creation on Windows

param(
    [string]$Path = $PWD,
    [switch]$Recurse,
    [switch]$DryRun
)

# Clean tmpclaude files
$tmpPattern = "tmpclaude-*-cwd"
$tmpFiles = if ($Recurse) {
    Get-ChildItem -Path $Path -Filter $tmpPattern -Recurse -ErrorAction SilentlyContinue
} else {
    Get-ChildItem -Path $Path -Filter $tmpPattern -ErrorAction SilentlyContinue
}

if ($tmpFiles) {
    Write-Host "Found $($tmpFiles.Count) tmpclaude files"
    foreach ($file in $tmpFiles) {
        if ($DryRun) {
            Write-Host "[DRY RUN] Would delete: $($file.FullName)"
        } else {
            Remove-Item $file.FullName -Force
            Write-Host "Deleted: $($file.FullName)"
        }
    }
} else {
    Write-Host "No tmpclaude files found"
}

# Clean nul files (Windows device name that can be created accidentally)
$nulFiles = if ($Recurse) {
    Get-ChildItem -Path $Path -Filter "nul" -Recurse -ErrorAction SilentlyContinue
} else {
    Get-ChildItem -Path $Path -Filter "nul" -ErrorAction SilentlyContinue
}

if ($nulFiles) {
    Write-Host "Found $($nulFiles.Count) nul files"
    foreach ($file in $nulFiles) {
        if ($DryRun) {
            Write-Host "[DRY RUN] Would delete: $($file.FullName)"
        } else {
            Remove-Item $file.FullName -Force
            Write-Host "Deleted: $($file.FullName)"
        }
    }
} else {
    Write-Host "No nul files found"
}
