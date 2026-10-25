# scripts/dev/doctor.ps1 - Environment Doctor for SMKD project (read‑only preflight checks)

<#
    PURPOSE: Detect environment problems before development begins.
    OUTPUT: Lines prefixed with [PASS], [WARN], [FAIL] and a final recommendation.
    EXIT CODES:
        0 – no critical failures.
        1 – one or more FAIL entries.
        2 – the doctor script itself encountered an error.
#>

param()

function Write-Status {
    param([string]$Level, [string]$Message)
    switch ($Level) {
        'PASS' { Write-Host "[PASS] $Message" -ForegroundColor Green }
        'WARN' { Write-Host "[WARN] $Message" -ForegroundColor Yellow }
        'FAIL' { Write-Host "[FAIL] $Message" -ForegroundColor Red }
        default { Write-Host "[$Level] $Message" }
    }
}

# Track if any FAIL occurred
$global:HasFail = $false
$global:HasError = $false

try {
    # 1. Repository root
    $gitRoot = git rev-parse --show-toplevel 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $gitRoot) {
        Write-Status 'FAIL' 'Git repository not found.'
        $global:HasFail = $true
    } else {
        Write-Status 'PASS' "Git repository root detected: $gitRoot"
    }

    # 2. Git status (tracked/untracked changes)
    if ($gitRoot) {
        $gitStatus = git status --porcelain 2>$null
        if ($gitStatus) {
            Write-Status 'WARN' 'Working tree has uncommitted or untracked changes.'
        } else {
            Write-Status 'PASS' 'Clean working tree.'
        }
    }

    # 3. Submodule status (if any)
    if ($gitRoot) {
        $subStatus = git submodule status --recursive 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Status 'PASS' 'Submodule status retrieved.'
        } else {
            Write-Status 'WARN' 'No submodules or submodule status unavailable.'
        }
    }

    # 4. JSON manifest validation (all package.json files under repo)
    $jsonFiles = Get-ChildItem -Path $gitRoot -Recurse -Filter 'package.json' -File -ErrorAction SilentlyContinue
    if ($jsonFiles) {
        foreach ($jf in $jsonFiles) {
            try { Get-Content $jf.FullName -Raw | ConvertFrom-Json | Out-Null; Write-Status 'PASS' "Valid JSON: $($jf.FullName)" } catch { Write-Status 'FAIL' "Invalid JSON in $($jf.FullName): $($_.Exception.Message)"; $global:HasFail = $true }
        }
    } else {
        Write-Status 'WARN' 'No package.json files found to validate.'
    }

    # 5. PNPM availability and workspace validation
    $pnpmCmd = Get-Command pnpm -ErrorAction SilentlyContinue
    if ($pnpmCmd) {
        # dry‑run to ensure resolution without modifying cache
        $proc = Start-Process -FilePath 'cmd' -ArgumentList '/c','pnpm','install','--dry-run' -NoNewWindow -RedirectStandardError 'pnpm_err.tmp' -RedirectStandardOutput 'pnpm_out.tmp' -PassThru -Wait
        $err = Get-Content 'pnpm_err.tmp' -Raw
        if ($proc.ExitCode -eq 0 -and -not $err) {
            Write-Status 'PASS' 'PNPM workspace resolves.'
        } else {
            Write-Status 'FAIL' "PNPM workspace resolution failed: $err"; $global:HasFail = $true
        }
        Remove-Item 'pnpm_out.tmp','pnpm_err.tmp' -ErrorAction SilentlyContinue
    } else {
        Write-Status 'FAIL' 'PNPM command not found.'; $global:HasFail = $true
    }

    # 6. Python interpreter and fastapi import
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCmd) {
        $ver = & $pythonCmd.Source --version 2>$null
        Write-Status 'PASS' "Python interpreter detected: $ver"
        # Check fastapi import (backend dependency)
        try { & $pythonCmd.Source -c "import fastapi" 2>$null; Write-Status 'PASS' 'Python package fastapi importable.' } catch { Write-Status 'WARN' 'Python package fastapi not importable.' }
    } else {
        Write-Status 'FAIL' 'Python interpreter not found.'; $global:HasFail = $true
    }

    # 7. Required scripts / configuration files
    $requiredFiles = @(
        "scripts/dev/dev.ps1",
        "package.json",
        "pnpm-lock.yaml",
        "stock-signal-bot/backend/app/api/routes.py"
    )
    foreach ($rf in $requiredFiles) {
        $full = Join-Path $gitRoot $rf
        if (Test-Path $full) { Write-Status 'PASS' "Required file exists: $rf" } else { Write-Status 'FAIL' "Missing required file: $rf"; $global:HasFail = $true }
    }

    # 8. Diagnostic directory writability
    $diagDir = Join-Path $gitRoot '.runtime/diagnostics'
    try {
        if (-not (Test-Path $diagDir)) { New-Item -ItemType Directory -Path $diagDir -Force | Out-Null }
        $tmpFile = Join-Path $diagDir 'write_test.tmp'
        Set-Content -Path $tmpFile -Value 'test' -Force
        Remove-Item $tmpFile -Force
        Write-Status 'PASS' 'Diagnostic directory writable.'
    } catch {
        Write-Status 'FAIL' "Diagnostic directory not writable: $($_.Exception.Message)"; $global:HasFail = $true
    }

    # Summary
    if ($global:HasFail) {
        Write-Host "\nNext action: Resolve the first [FAIL] above before continuing." -ForegroundColor Red
        exit 1
    } else {
        Write-Host "\nAll critical checks passed. You may proceed with development." -ForegroundColor Green
        exit 0
    }
} catch {
    Write-Status 'FAIL' "Doctor script encountered an unexpected error: $($_.Exception.Message)"
    exit 2
}
