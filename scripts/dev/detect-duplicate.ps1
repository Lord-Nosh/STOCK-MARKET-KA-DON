<#
.SYNOPSIS
  Checks for duplicate implementations, services, components, or files before creation.
.DESCRIPTION
  Scans workspace code for filenames, symbol exports, and imports to advise
  EXTEND_EXISTING, REPAIR_EXISTING, or CREATE_NEW.
#>

param (
    [Parameter(Mandatory=$true)]
    [string]$TargetName,

    [Parameter(Mandatory=$false)]
    [string]$SearchRoot = "."
)

Write-Host "Searching for existing capability matching: $TargetName..." -ForegroundColor Cyan

$Results = @{
    target = $TargetName
    files_found = @()
    symbols_found = @()
    recommendation = "CREATE_NEW"
}

# 1. Search filenames
$MatchedFiles = Get-ChildItem -Path $SearchRoot -Recurse -File -Include "*$TargetName*" -Exclude "node_modules", ".git", "dist", "build", "backups" -ErrorAction SilentlyContinue

foreach ($file in $MatchedFiles) {
    $Results.files_found += $file.FullName.Replace((Get-Location).Path + "\", "")
}

# 2. Search export/class/interface occurrences
$Pattern = "(class|interface|function|const)\s+.*$TargetName.*"
$SymbolMatches = Select-String -Path "$SearchRoot\stock-signal-bot\backend\app\**\*.py", "$SearchRoot\fast-framework\packages\**\*.ts" -Pattern $Pattern -ErrorAction SilentlyContinue

foreach ($m in $SymbolMatches) {
    $Results.symbols_found += "$($m.Filename):$($m.LineNumber): $($m.Line.Trim())"
}

# 3. Determine recommendation
if ($Results.files_found.Count -gt 0) {
    $Results.recommendation = "EXTEND_EXISTING"
    Write-Warning "Existing file(s) matched: $($Results.files_found -join ', ')"
} elseif ($Results.symbols_found.Count -gt 0) {
    $Results.recommendation = "REPAIR_OR_EXTEND_EXISTING"
    Write-Warning "Existing symbol(s) found: $($Results.symbols_found -join '; ')"
} else {
    Write-Host "No duplicates found. Safe to proceed with CREATE_NEW." -ForegroundColor Green
}

$Results | ConvertTo-Json -Depth 3
