[CmdletBinding()]
param(
    [switch]$CheckOnly
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "runtime_guard.ps1")

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..")).Path
$contractPath = Join-Path $projectRoot "runtime.contract.json"
$configPath = Join-Path $projectRoot "config\collection.local.json"

if (-not (Test-Path -LiteralPath $contractPath -PathType Leaf)) {
    throw "Runtime contract not found: $contractPath"
}
if (-not (Test-Path -LiteralPath $configPath -PathType Leaf)) {
    throw "Local collection config not found: $configPath"
}

$contract = Get-Content -LiteralPath $contractPath -Raw -Encoding UTF8 | ConvertFrom-Json
$config = Get-Content -LiteralPath $configPath -Raw -Encoding UTF8 | ConvertFrom-Json
$chromeExecutable = [string]$config.browser_harness.chrome_executable
$profileDirectory = [System.IO.Path]::GetFullPath([string]$config.browser_harness.user_data_dir)
$cdpUrl = [string]$contract.browser.cdp_url
$cdpPort = [int]$contract.browser.remote_debugging_port
$cdpAddress = [string]$contract.browser.remote_debugging_address
$expectedProfile = [System.IO.Path]::GetFullPath((Join-Path $projectRoot ([string]$contract.browser.profile_relative_path)))
$versionUrl = "$cdpUrl/json/version"

if ($cdpPort -ne 9222 -or $cdpUrl -ne "http://127.0.0.1:9222" -or $cdpAddress -ne "127.0.0.1") {
    throw "Integrated scraper Chrome must use 127.0.0.1:9222"
}
if (@($contract.browser.forbidden_ports) -notcontains 9223) {
    throw "Port 9223 must remain forbidden for this project"
}
if ((Resolve-ProjectPhysicalPath $profileDirectory) -ne (Resolve-ProjectPhysicalPath $expectedProfile)) {
    throw "Project Chrome profile mismatch: expected $expectedProfile"
}

if (-not (Test-Path -LiteralPath $chromeExecutable)) {
    throw "Project Chrome not found: $chromeExecutable"
}

function Get-CdpVersion {
    try {
        return (Invoke-WebRequest -UseBasicParsing -Uri $versionUrl -TimeoutSec 3).Content | ConvertFrom-Json
    } catch {
        return $null
    }
}

. (Join-Path $PSScriptRoot "runtime_guard.ps1")
$browserLock = Enter-ProjectBrowserLock
try {
$projectProcess = Assert-ProjectBrowserOwner -ProfileDirectory $profileDirectory -ChromeExecutable $chromeExecutable -AllowAbsent
if ($projectProcess) {
    $existing = Get-CdpVersion
    if (-not $existing) { throw 'project_cdp_unavailable: the project browser owns 9222 but CDP is not ready; check local authorization.' }
    [ordered]@{
        status = "already_running"
        cdp_url = $cdpUrl
        profile = $profileDirectory
        browser = $existing.Browser
        pid = $projectProcess.ProcessId
    } | ConvertTo-Json -Depth 4
    exit 0
}

if ($CheckOnly) {
    [ordered]@{
        status = "not_running"
        cdp_url = $cdpUrl
        profile = $profileDirectory
    } | ConvertTo-Json -Depth 4
    exit 2
}

New-Item -ItemType Directory -Force -Path $profileDirectory | Out-Null
Start-Process -FilePath $chromeExecutable -WindowStyle Hidden -ArgumentList @(
    "--remote-debugging-address=$cdpAddress",
    "--remote-debugging-port=$cdpPort",
    "--user-data-dir=`"$profileDirectory`"",
    "--no-first-run",
    "--no-default-browser-check",
    "about:blank"
)

for ($attempt = 0; $attempt -lt 20; $attempt++) {
    Start-Sleep -Milliseconds 500
    $projectProcess = Assert-ProjectBrowserOwner -ProfileDirectory $profileDirectory -ChromeExecutable $chromeExecutable -AllowAbsent
    $existing = if ($projectProcess) { Get-CdpVersion } else { $null }
    if ($existing) {
        [ordered]@{
            status = "started"
            cdp_url = $cdpUrl
            profile = $profileDirectory
            browser = $existing.Browser
            pid = $projectProcess.ProcessId
        } | ConvertTo-Json -Depth 4
        exit 0
    }
}

throw "Project Chrome did not expose $cdpUrl within 10 seconds."
} finally {
    Exit-ProjectBrowserLock $browserLock
}
