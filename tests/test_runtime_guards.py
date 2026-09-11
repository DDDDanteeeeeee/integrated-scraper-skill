"""Offline Windows guard tests: no real CDP/Chrome/daemon calls or processes."""
from pathlib import Path
import os
import shutil
import subprocess
import unittest
import uuid

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / '.agents/skills/integrated-scraper/scripts'
PS = shutil.which('powershell.exe')


@unittest.skipUnless(os.name == 'nt' and PS, 'Windows PowerShell required')
class RuntimeGuardTests(unittest.TestCase):
    def setUp(self):
        # Isolate smoke-test mutexes from an actual user's running task.
        self.lock_name = 'IntegratedScraperGuardTest' + uuid.uuid4().hex

    def guard_loader(self):
        guard = str(SCRIPTS / 'runtime_guard.ps1').replace("'", "''")
        return f". ([scriptblock]::Create((Get-Content -LiteralPath '{guard}' -Raw).Replace('IntegratedScraperBrowser9222','{self.lock_name}')))"

    def ps(self, body):
        return subprocess.run(
            [PS, '-NoProfile', '-NonInteractive', '-Command',
             f"$ErrorActionPreference='Stop'; {self.guard_loader()}; {body}"],
            capture_output=True, text=True, timeout=20,
        )

    def owner(self, *, profile=r'C:\fixture\project profile', port='9222',
              executable=r'C:\fixture\chrome.exe', address='127.0.0.1'):
        return self.ps(r'''
function Get-ProjectBrowserListeners {
    [pscustomobject]@{OwningProcess=123; LocalAddress='ADDRESS'}
}
function Get-CimInstance {
    param($ClassName, $Filter, $ErrorAction)
    if ($Filter -ne 'ProcessId=123') { throw 'wrong listener PID' }
    [pscustomobject]@{
        ExecutablePath='EXECUTABLE'; ProcessId=123
        CommandLine='chrome.exe --remote-debugging-port=PORT --user-data-dir="PROFILE"'
    }
}
$null = Assert-ProjectBrowserOwner -ProfileDirectory 'C:\fixture\project profile' -ChromeExecutable 'C:\fixture\chrome.exe'
'''.replace('ADDRESS', address).replace('EXECUTABLE', executable)
                .replace('PORT', port).replace('PROFILE', profile))

    def test_exact_listener_owner_with_spaces(self):
        result = self.owner()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_profile_substring_is_not_ownership(self):
        result = self.owner(profile=r'C:\fixture\project profile-other')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('browser_owner_mismatch', result.stderr)

    def test_wrong_executable_and_other_project_port_rejected(self):
        for args in ({'executable': r'C:\other\chrome.exe'}, {'port': '9223'}, {'address': '0.0.0.0'}):
            with self.subTest(args=args):
                self.assertNotEqual(self.owner(**args).returncode, 0)

    def test_absent_and_inspection_failure_are_distinct(self):
        absent = self.ps("function Get-ProjectBrowserListeners {}; Assert-ProjectBrowserOwner -ProfileDirectory C:\\fixture -ChromeExecutable C:\\chrome.exe")
        self.assertIn('browser_not_running', absent.stderr)
        failed = self.ps("function Get-ProjectBrowserListeners { throw 'inspection denied' }; Assert-ProjectBrowserOwner -ProfileDirectory C:\\fixture -ChromeExecutable C:\\chrome.exe -AllowAbsent")
        self.assertNotEqual(failed.returncode, 0)
        self.assertIn('inspection denied', failed.stderr)

    def test_mutex_excludes_another_process_and_releases(self):
        holder = subprocess.Popen(
            [PS, '-NoProfile', '-NonInteractive', '-Command',
             f"$ErrorActionPreference='Stop'; {self.guard_loader()}; $lock=Enter-ProjectBrowserLock; try {{ [Console]::WriteLine('READY'); [Console]::ReadLine() | Out-Null }} finally {{ Exit-ProjectBrowserLock $lock }}"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        try:
            self.assertEqual(holder.stdout.readline().strip(), 'READY')
            blocked = self.ps('$lock=Enter-ProjectBrowserLock; Exit-ProjectBrowserLock $lock')
            self.assertNotEqual(blocked.returncode, 0)
            self.assertIn('browser_busy', blocked.stderr)
        finally:
            holder.communicate('\n', timeout=10)
        released = self.ps('$lock=Enter-ProjectBrowserLock; Exit-ProjectBrowserLock $lock')
        self.assertEqual(released.returncode, 0, released.stderr)

    def test_scripts_parse_without_execution(self):
        path = str(SCRIPTS).replace("'", "''")
        result = self.ps(f"Get-ChildItem -LiteralPath '{path}' -Filter *.ps1 | ForEach-Object {{ $errors=$null; $tokens=$null; $null=[System.Management.Automation.Language.Parser]::ParseFile($_.FullName,[ref]$tokens,[ref]$errors); if ($errors) {{ throw ($errors | Out-String) }} }}")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_all_browser_entrypoints_lock_and_validate(self):
        for name in ('invoke_opencli.ps1', 'invoke_browser_harness.ps1', 'invoke_project_python.ps1', 'start_project_chrome.ps1'):
            text = (SCRIPTS / name).read_text(encoding='utf-8-sig')
            with self.subTest(name=name):
                self.assertIn('Enter-ProjectBrowserLock', text)
                self.assertIn('Assert-ProjectBrowserOwner', text)
                self.assertIn('finally', text)
                self.assertIn('Exit-ProjectBrowserLock', text)
        startup = (SCRIPTS / 'start_runtime.ps1').read_text(encoding='utf-8-sig')
        self.assertIn('if ($chromeExitCode -ne 0)', startup)
        self.assertNotIn('$CheckOnly -and $chromeExitCode', startup)


if __name__ == '__main__':
    unittest.main()
