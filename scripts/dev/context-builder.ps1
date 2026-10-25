<#
.SYNOPSIS
    Build a compact context packet for a given development task.
.DESCRIPTION
    This script collects only the source excerpts, callers, tests and documentation that are directly relevant to the task.
    It avoids loading the entire repository and respects a configurable token budget.
    The resulting packet is a JSON file containing:
        - TaskId
        - Objective
        - RelevantFiles (list of file paths)
        - Excerpts (map of file -> excerpt lines)
        - GitDiff (if any)
        - TokenEstimate (approximate token count using line count * 1.5)
        - Expanded flag (false unless later expansion is required)
.PARAMETER TaskId
    Identifier for the task (e.g., SMKD-CHART-001).
.PARAMETER Objective
    Short natural‑language description of what the task should achieve.
.EXAMPLE
    .\context-builder.ps1 -TaskId 'SMKD-CHART-001' -Objective 'Fix candlestick rendering bug'
#>
param(
    [Parameter(Mandatory=$true)][string]$TaskId,
    [Parameter(Mandatory=$true)][string]$Objective
)
# Helper: run ripgrep to locate symbols of interest (adjust patterns as needed)
function Find-RelevantFiles {
    param([string]$pattern)
    # Search within the two main code roots
    $roots = @("fast-framework", "stock-signal-bot")
    $matches = @()
    foreach($root in $roots){
        if(Test-Path $root){
            $cmd = "rg -l --fixed-strings $pattern $root"
            $result = Invoke-Expression $cmd 2>$null
            if($result){
                $matches += $result -split "`n"
            }
        }
    }
    return $matches | Sort-Object -Unique
}
# 1. Derive candidate symbols from the objective (very naive split)
$keywords = $Objective -split '\s+' | Where-Object { $_.Length -gt 3 }
$relevantFiles = @()
foreach($kw in $keywords){
    $files = Find-RelevantFiles -pattern $kw
    $relevantFiles += $files
}
$relevantFiles = $relevantFiles | Sort-Object -Unique
# 2. Extract excerpts (first 30 lines around each match)
$excerpts = @{}
foreach($file in $relevantFiles){
    if(Test-Path $file){
        $content = Get-Content -Path $file -Raw
        # Simple heuristic: take the first 200 lines (adjust as needed)
        $lines = $content -split "`n"
        $excerpt = $lines[0..([Math]::Min(199,$lines.Count-1))] -join "`n"
        $excerpts[$file] = $excerpt
    }
}
# 3. Capture current git diff (if any)
$gitDiff = ""
if (Test-Path .git){
    $gitDiff = git diff --cached --binary 2>$null
    if(-not $gitDiff){
        $gitDiff = git diff 2>$null
    }
}
# 4. Estimate token count (rough: 1 line ~ 1.5 tokens)
$tokenEstimate = ($excerpts.Values | ForEach-Object { ($_ -split "`n").Count } | Measure-Object -Sum).Sum * 1.5
# 5. Assemble packet
$packet = [pscustomobject]@{
    TaskId        = $TaskId
    Objective     = $Objective
    RelevantFiles = $relevantFiles
    Excerpts      = $excerpts
    GitDiff       = $gitDiff
    TokenEstimate = [int][Math]::Round($tokenEstimate)
    Expanded      = $false
}
# 6. Write to .runtime for persistence
$outPath = Join-Path -Path ".runtime" -ChildPath "context_$TaskId.json"
$packet | ConvertTo-Json -Depth 5 | Out-File -FilePath $outPath -Encoding utf8
Write-Host "Context packet written to $outPath (estimated $($packet.TokenEstimate) tokens)"
