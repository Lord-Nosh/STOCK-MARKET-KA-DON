<#
.SYNOPSIS
    Execute a command and produce a compact JSON summary for AI consumption.
.DESCRIPTION
    The script runs a given command, records full stdout/stderr to a log file under .runtime/diagnostics,
    then emits a short JSON object containing the most relevant error information.
    The full log remains available for later expansion if needed.
.PARAMETER CommandLine
    The exact command line to execute (string). Use quotes as appropriate for PowerShell.
.PARAMETER TaskId
    Identifier of the surrounding development task, for correlation.
.EXAMPLE
    .\\command-output-summarizer.ps1 -TaskId 'SMKD-CHART-001' -CommandLine 'pnpm build'
#>
param(
    [Parameter(Mandatory=$true)][string]$TaskId,
    [Parameter(Mandatory=$true)][string]$CommandLine
)
# Ensure diagnostic directory exists
$diagDir = Join-Path -Path ".runtime" -ChildPath "diagnostics"
if(-not (Test-Path $diagDir)){
    New-Item -ItemType Directory -Path $diagDir | Out-Null
}
# Unique log filename based on timestamp
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logPath = Join-Path $diagDir "${TaskId}_$timestamp.log"
# Run the command, capturing full output
$processInfo = New-Object System.Diagnostics.ProcessStartInfo
$processInfo.FileName = "powershell"
$processInfo.Arguments = "-NoLogo -NoProfile -Command \"$CommandLine\""
$processInfo.RedirectStandardOutput = $true
$processInfo.RedirectStandardError = $true
$processInfo.UseShellExecute = $false
$processInfo.CreateNoWindow = $true
$process = [System.Diagnostics.Process]::Start($processInfo)
$stdout = $process.StandardOutput.ReadToEnd()
$stderr = $process.StandardError.ReadToEnd()
$process.WaitForExit()
$exitCode = $process.ExitCode
# Write full log
$fullLog = "Command: $CommandLine`nExitCode: $exitCode`n--- STDOUT ---`n$stdout`n--- STDERR ---`n$stderr"
$fullLog | Out-File -FilePath $logPath -Encoding utf8
# Helper to extract first relevant error line (very naive)
function Get-FirstErrorLine {
    param([string]$text)
    $lines = $text -split "`n"
    foreach($ln in $lines){
        if($ln -match "error|exception|failed|\berr\b|\bFAIL\b|\bTraceback\b" -i){
            return $ln.Trim()
        }
    }
    return $null
}
$firstError = Get-FirstErrorLine -text ($stdout + "`n" + $stderr)
# Build summary object
$summary = [pscustomobject]@{
    TaskId        = $TaskId
    CommandLine   = $CommandLine
    ExitCode      = $exitCode
    DurationSec   = $process.TotalProcessorTime.TotalSeconds
    FirstError    = $firstError
    LogPath       = $logPath
}
# Output as JSON to stdout (AI will receive this compact object)
$summary | ConvertTo-Json -Depth 3
Write-Host "Full log saved to $logPath"
