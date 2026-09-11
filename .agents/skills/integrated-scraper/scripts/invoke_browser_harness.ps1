[CmdletBinding(PositionalBinding = $false)]
param(
    [string]$ScriptPath,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$BrowserHarnessArguments
)

$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "set_runtime_env.ps1")

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..")).Path
$config = Get-Content -LiteralPath (Join-Path $projectRoot "config\collection.local.json") -Raw -Encoding UTF8 | ConvertFrom-Json
$browserHarnessCommand = [string]$config.browser_harness.command

if ($env:BU_CDP_URL -ne "http://127.0.0.1:9222") {
    throw "BrowserHarness CDP contract mismatch"
}
if (-not (Get-Command $browserHarnessCommand -ErrorAction SilentlyContinue)) {
    throw "BrowserHarness command not found: $browserHarnessCommand"
}

. (Join-Path $PSScriptRoot "runtime_guard.ps1")
$browserLock = Enter-ProjectBrowserLock
try {
    $null = Assert-ProjectBrowserOwner -ProfileDirectory $profileDirectory -ChromeExecutable ([string]$config.browser_harness.chrome_executable)
    if ($ScriptPath) {
        if ($BrowserHarnessArguments.Count -gt 0) { throw 'ScriptPath cannot be combined with BrowserHarness arguments' }
        $scriptSource = Get-Content -LiteralPath $ScriptPath -Raw -Encoding UTF8
        # ASCII transport avoids Windows PowerShell 5.1 pipeline code-page loss.
        $encodedSource = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($scriptSource))
        "exec(compile(__import__('base64').b64decode('$encodedSource').decode('utf-8'), '<project-script>', 'exec'))" | & $browserHarnessCommand
    } else {
        & $browserHarnessCommand @BrowserHarnessArguments
    }
    $commandExitCode = $LASTEXITCODE
} finally {
    Exit-ProjectBrowserLock $browserLock
}
exit $commandExitCode
