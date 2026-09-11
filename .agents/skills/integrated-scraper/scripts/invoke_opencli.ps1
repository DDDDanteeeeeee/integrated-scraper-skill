[CmdletBinding(PositionalBinding = $false)]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$OpenCliArguments
)

$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "set_runtime_env.ps1")

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..")).Path
$config = Get-Content -LiteralPath (Join-Path $projectRoot "config\collection.local.json") -Raw -Encoding UTF8 | ConvertFrom-Json
$contract = Get-Content -LiteralPath (Join-Path $projectRoot "runtime.contract.json") -Raw -Encoding UTF8 | ConvertFrom-Json
$openCliCommand = [string]$config.opencli.command
$fixedProfile = [string]$contract.opencli.profile

if ([string]$config.opencli.profile -ne $fixedProfile -or $fixedProfile -ne "integrated-scraper-9222") {
    throw "OpenCLI profile contract mismatch"
}
if (-not (Get-Command $openCliCommand -ErrorAction SilentlyContinue)) {
    throw "OpenCLI command not found: $openCliCommand"
}

if (@($OpenCliArguments | Where-Object { $_ -match '^--profile(?:=|$)' }).Count -gt 0) {
    throw 'OpenCLI profile overrides are forbidden; the project entrypoint selects the fixed profile.'
}
. (Join-Path $PSScriptRoot "runtime_guard.ps1")
$browserLock = Enter-ProjectBrowserLock
try {
    $null = Assert-ProjectBrowserOwner -ProfileDirectory $profileDirectory -ChromeExecutable ([string]$config.browser_harness.chrome_executable)
    & $openCliCommand --profile $fixedProfile @OpenCliArguments
    $commandExitCode = $LASTEXITCODE
} finally {
    Exit-ProjectBrowserLock $browserLock
}
exit $commandExitCode
