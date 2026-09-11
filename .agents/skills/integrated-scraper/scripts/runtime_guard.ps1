# Shared, fail-closed guards. This file has no startup or browser side effects.
function Resolve-ProjectPhysicalPath {
    param([Parameter(Mandatory = $true)][string]$Path)
    $resolved = [System.IO.Path]::GetFullPath($Path)
    for ($hop = 0; $hop -lt 16; $hop++) {
        $cursor = $resolved
        $changed = $false
        while ($cursor) {
            if (Test-Path -LiteralPath $cursor) {
                $item = Get-Item -LiteralPath $cursor -Force -ErrorAction Stop
                if ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) {
                    $targets = @($item.Target)
                    if ($targets.Count -ne 1 -or -not $targets[0]) { throw 'Unverifiable path reparse target' }
                    $target = [string]$targets[0]
                    if (-not [System.IO.Path]::IsPathRooted($target)) { $target = Join-Path (Split-Path $cursor -Parent) $target }
                    $suffix = $resolved.Substring($cursor.Length).TrimStart('\')
                    $resolved = [System.IO.Path]::GetFullPath($(if ($suffix) { Join-Path $target $suffix } else { $target }))
                    $changed = $true
                    break
                }
            }
            $parent = Split-Path $cursor -Parent
            if ($parent -eq $cursor) { break }
            $cursor = $parent
        }
        if (-not $changed) { return $resolved }
    }
    throw 'Path reparse chain exceeds limit'
}

function Enter-ProjectBrowserLock {
    $mutex = [System.Threading.Mutex]::new($false, 'Global\IntegratedScraperBrowser9222')
    try {
        try { $acquired = $mutex.WaitOne(0) }
        catch [System.Threading.AbandonedMutexException] { $acquired = $true }
        if (-not $acquired) {
            throw 'browser_busy: another integrated-scraper controller owns port 9222; retry after it finishes.'
        }
        return $mutex
    } catch {
        $mutex.Dispose()
        throw
    }
}

function Exit-ProjectBrowserLock {
    param([System.Threading.Mutex]$Mutex)
    if ($null -ne $Mutex) {
        try { $Mutex.ReleaseMutex() } finally { $Mutex.Dispose() }
    }
}

function Get-ProjectBrowserListeners {
    # Do not suppress access/provider errors: inability to inspect is not a free port.
    @(Get-NetTCPConnection -State Listen -ErrorAction Stop | Where-Object { $_.LocalPort -eq 9222 })
}

function Assert-ProjectBrowserOwner {
    param(
        [Parameter(Mandatory = $true)][string]$ProfileDirectory,
        [Parameter(Mandatory = $true)][string]$ChromeExecutable,
        [switch]$AllowAbsent
    )
    $listeners = @(Get-ProjectBrowserListeners)
    if ($listeners.Count -eq 0) {
        if ($AllowAbsent) { return $null }
        throw 'browser_not_running: project Chrome must be running on 127.0.0.1:9222.'
    }
    $owners = @($listeners | Select-Object -ExpandProperty OwningProcess -Unique)
    if ($owners.Count -ne 1 -or @($listeners | Where-Object { $_.LocalAddress -notin @('127.0.0.1', '::1') }).Count -gt 0) {
        throw 'browser_owner_mismatch: port 9222 must have exactly one loopback-only owner.'
    }
    $ownerId = [int]$owners[0]
    $process = Get-CimInstance Win32_Process -Filter "ProcessId=$ownerId" -ErrorAction Stop
    if ($null -eq $process -or -not $process.ExecutablePath -or -not $process.CommandLine) {
        throw 'browser_owner_unverifiable: cannot inspect the actual port 9222 owner.'
    }
    if ((Resolve-ProjectPhysicalPath ([string]$process.ExecutablePath)) -ne (Resolve-ProjectPhysicalPath $ChromeExecutable)) {
        throw 'browser_owner_mismatch: listener executable is not the configured project Chrome.'
    }
    $commandLine = [string]$process.CommandLine
    $profileArgs = [regex]::Matches($commandLine, '(?:^|\s)--user-data-dir=(?:"([^"]+)"|(\S+))')
    $portArgs = [regex]::Matches($commandLine, '(?:^|\s)--remote-debugging-port=(?:"(\d+)"|(\d+))(?=\s|$)')
    if ($profileArgs.Count -ne 1 -or $portArgs.Count -ne 1 -or $commandLine -match '(?:^|\s)--type=') {
        throw 'browser_owner_mismatch: listener must be the project browser main process with unambiguous arguments.'
    }
    $actualProfile = $profileArgs[0].Groups[1].Value
    if (-not $actualProfile) { $actualProfile = $profileArgs[0].Groups[2].Value }
    $actualPort = $portArgs[0].Groups[1].Value
    if (-not $actualPort) { $actualPort = $portArgs[0].Groups[2].Value }
    if ($actualPort -ne '9222' -or (Resolve-ProjectPhysicalPath $actualProfile) -ne (Resolve-ProjectPhysicalPath $ProfileDirectory)) {
        throw 'browser_owner_mismatch: listener does not own the exact project profile and port 9222.'
    }
    return $process
}
