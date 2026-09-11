[CmdletBinding()]
param(
    [switch]$PassThru
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
$fixedCdpUrl = [string]$contract.browser.cdp_url
$fixedPort = [int]$contract.browser.remote_debugging_port
$fixedProfile = [string]$contract.opencli.profile
$profileDirectory = (Join-Path $projectRoot ([string]$contract.browser.profile_relative_path)).Replace('/', '\')

if ($fixedPort -ne 9222 -or $fixedCdpUrl -ne "http://127.0.0.1:9222") {
    throw "runtime.contract.json must keep the integrated-scraper browser on 127.0.0.1:9222"
}
if (@($contract.browser.forbidden_ports) -notcontains 9223) {
    throw "runtime.contract.json must explicitly forbid port 9223"
}
if ([string]$config.browser_harness.cdp_url -ne $fixedCdpUrl) {
    throw "collection.local.json CDP mismatch: expected $fixedCdpUrl"
}
if ([int]$config.browser_harness.remote_debugging_port -ne $fixedPort) {
    throw "collection.local.json port mismatch: expected $fixedPort"
}
if ([string]$config.opencli.profile -ne $fixedProfile) {
    throw "collection.local.json OpenCLI profile mismatch: expected $fixedProfile"
}
if ((Resolve-ProjectPhysicalPath ([string]$config.browser_harness.user_data_dir)) -ne (Resolve-ProjectPhysicalPath $profileDirectory)) {
    throw "collection.local.json browser profile must be $profileDirectory"
}

$env:OPENCLI_CDP_ENDPOINT = $fixedCdpUrl
$env:OPENCLI_CACHE_DIR = Join-Path $projectRoot ([string]$contract.opencli.cache_relative_path)
$env:OPENCLI_WINDOW = [string]$contract.opencli.window
$env:OPENCLI_BROWSER_CONNECT_TIMEOUT = [string]$contract.opencli.connect_timeout_seconds
$env:OPENCLI_BROWSER_COMMAND_TIMEOUT = [string]$contract.opencli.command_timeout_seconds
$env:BU_CDP_URL = $fixedCdpUrl
$env:BH_AGENT_WORKSPACE = Join-Path $projectRoot ([string]$contract.browser_harness.workspace_relative_path)
$env:BH_DOMAIN_SKILLS = if ([bool]$contract.browser_harness.domain_skills) { "1" } else { "0" }
$env:PLAYWRIGHT_BROWSERS_PATH = Join-Path $projectRoot ([string]$contract.python.playwright_browsers_relative_path)

$runtimeBin = Join-Path $projectRoot "runtime\bin"
$pathEntries = @($env:PATH -split ';' | Where-Object { $_ })
if ($pathEntries -notcontains $runtimeBin) {
    $env:PATH = "$runtimeBin;$env:PATH"
}

New-Item -ItemType Directory -Force -Path $env:OPENCLI_CACHE_DIR, $env:BH_AGENT_WORKSPACE, $env:PLAYWRIGHT_BROWSERS_PATH | Out-Null

if ($PassThru) {
    [ordered]@{
        status = "configured"
        project_root = $projectRoot
        browser_cdp = $env:OPENCLI_CDP_ENDPOINT
        browser_port = $fixedPort
        opencli_profile = $fixedProfile
        opencli_cache = $env:OPENCLI_CACHE_DIR
        browser_harness_workspace = $env:BH_AGENT_WORKSPACE
        playwright_browsers = $env:PLAYWRIGHT_BROWSERS_PATH
        forbidden_ports = @($contract.browser.forbidden_ports)
    } | ConvertTo-Json -Depth 4
}
