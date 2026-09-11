[CmdletBinding(PositionalBinding = $false)]
param(
    [switch]$BrowserControl,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$PythonArguments
)

$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "set_runtime_env.ps1")

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..")).Path
$config = Get-Content -LiteralPath (Join-Path $projectRoot "config\collection.local.json") -Raw -Encoding UTF8 | ConvertFrom-Json
$pythonExecutable = [string]$config.python.executable

if (-not (Test-Path -LiteralPath $pythonExecutable -PathType Leaf)) {
    throw "Project Python not found: $pythonExecutable"
}

$browserLock = $null
try {
    if ($BrowserControl) {
        . (Join-Path $PSScriptRoot "runtime_guard.ps1")
        $browserLock = Enter-ProjectBrowserLock
        $null = Assert-ProjectBrowserOwner -ProfileDirectory $profileDirectory -ChromeExecutable ([string]$config.browser_harness.chrome_executable)
    }
    & $pythonExecutable @PythonArguments
    $commandExitCode = $LASTEXITCODE
} finally {
    if ($null -ne $browserLock) { Exit-ProjectBrowserLock $browserLock }
}
exit $commandExitCode
