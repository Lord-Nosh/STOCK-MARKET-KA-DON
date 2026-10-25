# scripts/dev/dev.ps1 - Development controller for SMKD project (read‑only preflight checks and placeholders for other commands)

param(
    [Parameter(Mandatory=$true, Position=0)][ValidateSet('doctor','start','status','test','diagnose','cache','stop')]
    [string]$Command,
    [ValidateSet('changed','all')][string]$Scope,
    [switch]$LastRun
)

function Write-Result {
    param([string]$Status, [string]$Message)
    $color = switch ($Status) {
        'PASS' { 'Green' }
        'WARN' { 'Yellow' }
        'FAIL' { 'Red' }
        default { 'White' }
    }
    Write-Host "[$Status] $Message" -ForegroundColor $color
}

function Test-GitRepository {
    try {
        $root = git rev-parse --show-toplevel 2>$null
        if (-not $root) { throw 'Not a git repository.' }
        Write-Result -Status 'PASS' -Message "Git repository root: $root"
        $status = git status --porcelain 2>$null
        if ($status) { Write-Result -Status 'WARN' -Message 'Uncommitted changes present' } else { Write-Result -Status 'PASS' -Message 'Clean working tree' }
        $sub = git submodule status --recursive 2>$null
        Write-Result -Status 'PASS' -Message 'Submodule status retrieved'
    } catch {
        Write-Result -Status 'FAIL' -Message $_
    }
}

function Test-JsonManifests {
    $files = @('package.json')
    foreach ($f in $files) {
        $path = Join-Path $PSScriptRoot '..' $f
        if (Test-Path $path) {
            try { Get-Content $path -Raw | ConvertFrom-Json | Out-Null; Write-Result -Status 'PASS' -Message "$f is valid JSON" }
            catch { Write-Result -Status 'FAIL' -Message "$f contains invalid JSON" }
        } else { Write-Result -Status 'WARN' -Message "$f not found" }
    }
}

function Test-PnpmWorkspace {
    try {
        $pnpm = Get-Command pnpm -ErrorAction Stop
        $proc = Start-Process -FilePath $pnpm.Source -ArgumentList 'install','--dry-run' -NoNewWindow -RedirectStandardError 'pnpm_err.txt' -RedirectStandardOutput 'pnpm_out.txt' -PassThru -Wait
        $err = Get-Content 'pnpm_err.txt' -Raw
        if ($proc.ExitCode -eq 0 -and -not $err) { Write-Result -Status 'PASS' -Message 'PNPM workspace resolves' }
        else { Write-Result -Status 'FAIL' -Message "PNPM workspace error: $err" }
    } catch { Write-Result -Status 'FAIL' -Message 'pnpm command not found or failed' }
    finally { Remove-Item 'pnpm_out.txt','pnpm_err.txt' -ErrorAction SilentlyContinue }
}

function Test-PythonEnv {
    try {
        $ver = python --version 2>$null
        if (-not $ver) { throw 'Python not found' }
        Write-Result -Status 'PASS' -Message "Python interpreter detected: $ver"
    } catch { Write-Result -Status 'FAIL' -Message $_ }
}

function Test-Ports {
    $ports = @(8000,5173) # FastAPI, Vite
    foreach ($p in $ports) {
        $reachable = Test-NetConnection -ComputerName localhost -Port $p -InformationLevel Quiet
        if ($reachable) { Write-Result -Status 'WARN' -Message "Port $p open – service may already be running" }
        else { Write-Result -Status 'PASS' -Message "Port $p is free" }
    }
}

function Test-EnvVariables {
    $required = @('FASTAPI_ENV','PNPM_HOME')
    foreach ($v in $required) {
        if ($env:$v) { Write-Result -Status 'PASS' -Message "Env var $v set" } else { Write-Result -Status 'WARN' -Message "Missing env var: $v" }
    }
}

function Test-DiagnosticDir {
    $dir = Join-Path $PSScriptRoot '..' '.runtime' 'diagnostics'
    try {
        if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
        $tmp = Join-Path $dir 'write_test.tmp'
        Set-Content -Path $tmp -Value 'test' -Force
        Remove-Item $tmp -Force
        Write-Result -Status 'PASS' -Message 'Diagnostic directory writable'
    } catch { Write-Result -Status 'FAIL' -Message "Diagnostic directory not writable: $_" }
}

function Invoke-Doctor {
    Write-Host '=== SMKD Development Environment Doctor ==='
    $global:HasFail = $false
    Test-GitRepository
    Test-JsonManifests
    Test-PnpmWorkspace
    Test-PythonEnv
    Test-Ports
    Test-EnvVariables
    Test-DiagnosticDir
    if ($global:HasFail) { Write-Host "\nNext action: Resolve the first failure above." -ForegroundColor Red; exit 1 } else { Write-Host "\nAll checks passed. You may proceed with \"dev start\"." -ForegroundColor Green; exit 0 }
}

switch ($Command) {
    'doctor'   { Invoke-Doctor }
    'start'    { Write-Host 'Start command not yet implemented.' }
    'status'   { Write-Host 'Status command not yet implemented.' }
    'test'     { Write-Host "Test command placeholder – Scope: $Scope" }
    'diagnose' { Write-Host "Diagnose command placeholder – LastRun: $LastRun" }
    'cache'    { Write-Host 'Cache command placeholder.' }
    'stop'     { Write-Host 'Stop command placeholder.' }
    default    { Write-Error "Unknown subcommand: $Command"; exit 1 }
}
