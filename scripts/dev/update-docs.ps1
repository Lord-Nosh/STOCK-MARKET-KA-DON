<#
.SYNOPSIS
  Selectively updates or reports documentation affected by code changes based on DOCS_MAP.yml.
.PARAMETER DryRun
  Lists affected docs and required verification checks without modifying any files.
.PARAMETER Report
  Generates a JSON status report of documentation synchronization.
#>

param (
    [switch]$DryRun,
    [switch]$Report,
    [string[]]$ChangedFiles = @()
)

$DocsMapFile = Join-Path $PSScriptRoot "..\..\docs\dev\DOCS_MAP.yml"

if (-not (Test-Path $DocsMapFile)) {
    Write-Error "DOCS_MAP.yml not found at: $DocsMapFile"
    exit 1
}

# Determine changed files from Git if none passed explicitly
if ($ChangedFiles.Count -eq 0) {
    $MainStatus = git status --porcelain
    $SubStatus = git -C fast-framework status --porcelain 2>$null

    foreach ($line in ($MainStatus -split "`r?`n")) {
        if ($line.Length -gt 3) {
            $f = $line.Substring(3).Trim()
            if ($f -notmatch "fast-framework") { $ChangedFiles += $f }
        }
    }
    foreach ($line in ($SubStatus -split "`r?`n")) {
        if ($line.Length -gt 3) {
            $f = "fast-framework/" + $line.Substring(3).Trim()
            $ChangedFiles += $f
        }
    }
}

Write-Host "Evaluating $( $ChangedFiles.Count ) changed file(s)..." -ForegroundColor Cyan

$AffectedDocs = [System.Collections.Generic.HashSet[string]]::new()
$RequiredChecks = [System.Collections.Generic.HashSet[string]]::new()

# Simple parser for DOCS_MAP.yml rules
$Content = Get-Content $DocsMapFile -Raw
$RuleBlocks = $Content -split "- source:\s*"

foreach ($block in $RuleBlocks) {
    if (-not $block.Trim() -or $block.StartsWith("#")) { continue }
    $lines = $block -split "`r?`n"
    $pattern = $lines[0].Trim().Trim('"').Trim("'")

    # Convert glob pattern to regex
    $regexPattern = [regex]::Escape($pattern).Replace("\*\*", ".*").Replace("\*", "[^/]*")

    $matched = $false
    foreach ($cf in $ChangedFiles) {
        $norm = $cf.Replace("\", "/")
        if ($norm -match "^$regexPattern" -or $norm -match "$regexPattern") {
            $matched = $true
            break
        }
    }

    if ($matched) {
        $inDocs = $false
        $inChecks = $false
        foreach ($l in $lines) {
            if ($l -match "docs:") { $inDocs = $true; $inChecks = $false; continue }
            if ($l -match "checks:") { $inDocs = $false; $inChecks = $true; continue }
            if ($l -match "^\s*-\s*""(.*)""") {
                $item = $matches[1]
                if ($inDocs) { $AffectedDocs.Add($item) | Out-Null }
                if ($inChecks) { $RequiredChecks.Add($item) | Out-Null }
            }
        }
    }
}

$Result = @{
    timestamp = (Get-Date -Format "o")
    changed_files = $ChangedFiles
    affected_docs = @($AffectedDocs)
    required_checks = @($RequiredChecks)
    sync_status = if ($AffectedDocs.Count -gt 0) { "NEEDS_REVIEW" } else { "NOT_REQUIRED" }
}

if ($DryRun) {
    Write-Host "`n[DRY RUN] Documentation Evaluation:" -ForegroundColor Yellow
    Write-Host "Affected Docs: $($AffectedDocs.Count)"
    foreach ($d in $AffectedDocs) { Write-Host "  -> $d" -ForegroundColor Green }
    Write-Host "`nRequired Verification Checks: $($RequiredChecks.Count)"
    foreach ($c in $RequiredChecks) { Write-Host "  -> $c" -ForegroundColor Cyan }
}

if ($Report) {
    $Result | ConvertTo-Json -Depth 4
}
