[CmdletBinding()]
param(
    [switch]$CheckOnly,
    [string]$PlanPath
)

$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "set_runtime_env.ps1")

$chromeScript = Join-Path $PSScriptRoot "start_project_chrome.ps1"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..")).Path
$configPath = Join-Path $projectRoot "config\collection.local.json"
$config = Get-Content -LiteralPath $configPath -Raw -Encoding UTF8 | ConvertFrom-Json
$pythonExecutable = [string]$config.python.executable

$requiresProjectChrome = $true
$resolvedPlanPath = $null
if ($PlanPath) {
    $resolvedPlanPath = (Resolve-Path -LiteralPath $PlanPath).Path
    $plan = Get-Content -LiteralPath $resolvedPlanPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $requiredTools = @($plan.required_tools)
    $requiresProjectChrome = ($requiredTools -contains "opencli") -or ($requiredTools -contains "browser-harness")
}

if ($requiresProjectChrome) {
    if ($CheckOnly) {
        & $chromeScript -CheckOnly
    } else {
        & $chromeScript
    }
    $chromeExitCode = $LASTEXITCODE
    if ($chromeExitCode -ne 0) {
        exit $chromeExitCode
    }
}
if (-not (Test-Path -LiteralPath $pythonExecutable -PathType Leaf)) {
    throw "Project Python not found: $pythonExecutable"
}

$doctorArguments = @((Join-Path $PSScriptRoot "pack_doctor.py"), "--config", $configPath)
if ($resolvedPlanPath) {
    $doctorArguments += @("--plan", $resolvedPlanPath)
}
& $pythonExecutable @doctorArguments
exit $LASTEXITCODE
