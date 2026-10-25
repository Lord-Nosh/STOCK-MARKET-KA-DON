<#
.SYNOPSIS
  CLI wrapper for the SMKD deterministic development controller.
.EXAMPLE
  .\scripts\dev\devctl.ps1 create -TaskId "DEV-010" -Title "Environment Doctor"
  .\scripts\dev\devctl.ps1 status -TaskId "DEV-010"
  .\scripts\dev\devctl.ps1 run -TaskId "DEV-010" -Command "git status"
  .\scripts\dev\devctl.ps1 verify -TaskId "DEV-010" -TestExitCode 0
#>

param (
    [Parameter(Mandatory=$true, Position=0)]
    [ValidateSet("create", "pack", "status", "run", "verify", "doctor", "workflow")]
    [string]$Action,

    [Parameter(Mandatory=$false)]
    [string]$TaskId,

    [Parameter(Mandatory=$false)]
    [string]$Title,

    [Parameter(Mandatory=$false)]
    [string]$Scope = "",

    [Parameter(Mandatory=$false)]
    [string]$Acceptance = "",

    [Parameter(Mandatory=$false)]
    [string]$Command = "",

    [Parameter(Mandatory=$false)]
    [string]$ChangedFiles = "",

    [Parameter(Mandatory=$false)]
    [int]$TestExitCode = 0
)

$ControllerPy = Join-Path $PSScriptRoot "controller\cli.py"

if ($Action -eq "doctor") {
    & "$PSScriptRoot\doctor.ps1"
    exit $LASTEXITCODE
}

    $prevPyPath = $env:PYTHONPATH
    $env:PYTHONPATH = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
    switch ($Action) {
        "create" {
            $cmdArgs = @("create", "--task-id", $TaskId, "--title", $Title)
            if ($Scope) { $cmdArgs += @("--scope", $Scope) }
            if ($Acceptance) { $cmdArgs += @("--acceptance", $Acceptance) }
            python $ControllerPy @cmdArgs
        }
        "pack" {
            python $ControllerPy pack --task-id $TaskId
        }
        "status" {
            python $ControllerPy status --task-id $TaskId
        }
        "run" {
            python $ControllerPy run --task-id $TaskId --command $Command
        }
        "verify" {
            python $ControllerPy verify --task-id $TaskId --changed-files $ChangedFiles --test-exit $TestExitCode
        }
        "workflow" {
            $cmdArgs = @("workflow", "--task-id", $TaskId)
            if ($ChangedFiles) { $cmdArgs += @("--changed-files", $ChangedFiles) }
            python $ControllerPy @cmdArgs
        }
    }
    $env:PYTHONPATH = $prevPyPath
