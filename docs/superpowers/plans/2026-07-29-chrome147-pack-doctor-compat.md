# Chrome 147+ Pack Doctor Compatibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `pack_doctor.py` accept Chrome 147+ `/json/version` HTTP 404 only when BrowserHarness independently proves that its daemon is alive and at least one browser connection is active.

**Architecture:** Keep `doctor.py` as the strict loopback HTTP probe. Add a narrow BrowserHarness health fallback in `pack_doctor.py`; it runs `browser-harness --doctor`, parses only the daemon and active-connection health lines, and is consulted only for the explicit HTTP 404 compatibility case.

**Tech Stack:** Python 3.12 standard library (`subprocess`, `re`, `unittest`), existing Magewell Skill Pack scripts, BrowserHarness CLI 0.1.8.

---

## File map

- Modify: `tests/test_scripts.py`
  - Add the Chrome 147+ compatibility regression tests.
  - Add direct tests for BrowserHarness doctor-output parsing.
- Modify: `.agents/skills/magewell-douyin-intelligence/scripts/pack_doctor.py`
  - Add the bounded BrowserHarness health probe.
  - Add the explicit HTTP 404 fallback in `check_pack()`.
- Verify only: `.agents/skills/magewell-douyin-intelligence/scripts/doctor.py`
  - Preserve strict loopback URL and `/json/version` behavior.
- Verify only: `config/collection.local.json`
  - Use the existing Git-ignored local configuration for the real acceptance run.

### Task 1: Route only Chrome discovery 404 through BrowserHarness health

**Files:**
- Modify: `tests/test_scripts.py:128-185`
- Modify: `.agents/skills/magewell-douyin-intelligence/scripts/pack_doctor.py:41-92`

- [ ] **Step 1: Write the failing Chrome 147+ regression test**

Add `patch` to the test imports:

```python
from unittest.mock import patch
```

Add this method to `PackDoctorTests`:

```python
def test_accepts_chrome_discovery_404_when_browser_harness_is_connected(self):
    manifest = DependencyManifestTests().load_manifest()
    with tempfile.TemporaryDirectory() as directory:
        with patch.object(
            pack_doctor,
            "browser_harness_health",
            return_value=(True, "daemon 正常且存在 1 个活动连接"),
            create=True,
        ):
            result = pack_doctor.check_pack(
                self.config(),
                manifest,
                self.roots_with_skills(Path(directory)),
                command_checker=lambda _: True,
                cdp_probe=lambda _: (False, "HTTP Error 404: Not Found"),
            )
    self.assertEqual(result["status"], "success")
    self.assertEqual(result["checks"]["browser-harness"]["status"], "success")
    self.assertIn("Chrome 147+", result["checks"]["browser-harness"]["detail"])
```

Add the paired safety test:

```python
def test_keeps_chrome_discovery_404_blocked_without_browser_harness_connection(self):
    manifest = DependencyManifestTests().load_manifest()
    with tempfile.TemporaryDirectory() as directory:
        with patch.object(
            pack_doctor,
            "browser_harness_health",
            return_value=(False, "没有活动浏览器连接"),
            create=True,
        ):
            result = pack_doctor.check_pack(
                self.config(),
                manifest,
                self.roots_with_skills(Path(directory)),
                command_checker=lambda _: True,
                cdp_probe=lambda _: (False, "HTTP Error 404: Not Found"),
            )
    self.assertEqual(result["status"], "awaiting_human")
    self.assertEqual(result["checks"]["browser-harness"]["status"], "awaiting_human")
```

- [ ] **Step 2: Run the regression test and verify RED**

Run:

```powershell
& 'C:\Users\fddfd\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest tests.test_scripts.PackDoctorTests.test_accepts_chrome_discovery_404_when_browser_harness_is_connected -v
```

Expected: `FAIL`; current behavior returns `awaiting_human` instead of `success`.

- [ ] **Step 3: Add the minimal fallback seam and routing**

Add a stub health function before `check_pack()`:

```python
def browser_harness_health(command: str = "browser-harness", *, runner=None) -> tuple[bool, str]:
    return False, "browser-harness daemon 未就绪或没有活动浏览器连接"
```

Add an optional injection seam to the `check_pack()` signature:

```python
def check_pack(
    config: dict,
    manifest: dict,
    skill_roots: list[Path],
    *,
    command_checker=doctor.command_available,
    cdp_probe=doctor.probe_cdp,
    browser_health_checker=None,
) -> dict:
```

Change the BrowserHarness section in `check_pack()` so the strict CDP result remains primary and the compatibility fallback is limited to the exact 404 condition:

```python
browser_skill = find_skill("browser-harness", skill_roots)
browser_cli = command_checker("browser-harness")
browser_cdp = bool(base["checks"]["browser"]["ready"])
browser_detail = str(base["checks"]["browser"]["detail"])
health_check = browser_health_checker or browser_harness_health
if (
    browser_skill
    and browser_cli
    and not browser_cdp
    and "HTTP Error 404" in browser_detail
):
    browser_cdp, health_detail = health_check()
    if browser_cdp:
        browser_detail = f"Chrome 147+ 兼容验证通过；{health_detail}"

if not browser_skill or not browser_cli:
    browser_status = "blocked_dependency"
    browser_detail = "需要已安装的 browser-harness Skill 与本机命令"
elif not browser_cdp:
    browser_status = "awaiting_human"
else:
    browser_status = "success"
    if "Chrome 147+" not in browser_detail:
        browser_detail = "Skill、命令和本机 CDP 已就绪"
```

- [ ] **Step 4: Run both compatibility tests and verify GREEN**

Run:

```powershell
& 'C:\Users\fddfd\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest tests.test_scripts.PackDoctorTests.test_accepts_chrome_discovery_404_when_browser_harness_is_connected tests.test_scripts.PackDoctorTests.test_keeps_chrome_discovery_404_blocked_without_browser_harness_connection -v
```

Expected: both tests `PASS`.

- [ ] **Step 5: Commit the routing change**

```powershell
git add tests/test_scripts.py .agents/skills/magewell-douyin-intelligence/scripts/pack_doctor.py
git commit -m "fix: route Chrome 147 CDP checks through BrowserHarness"
```

### Task 2: Parse BrowserHarness local health safely

**Files:**
- Modify: `tests/test_scripts.py:1-185`
- Modify: `.agents/skills/magewell-douyin-intelligence/scripts/pack_doctor.py:6-55`

- [ ] **Step 1: Write the failing healthy-output parser test**

Add this import:

```python
from types import SimpleNamespace
```

Add this method to `PackDoctorTests`:

```python
def test_browser_harness_health_accepts_local_connection_with_optional_cloud_failure(self):
    completed = SimpleNamespace(
        stdout=(
            "browser-harness doctor\n"
            "  [ok  ] daemon alive\n"
            "  [ok  ] active browser connections — 1\n"
            "  [FAIL] Browser Use cloud auth — optional\n"
        ),
        stderr="",
        returncode=0,
    )
    ready, detail = pack_doctor.browser_harness_health(
        runner=lambda *args, **kwargs: completed
    )
    self.assertTrue(ready)
    self.assertIn("活动浏览器连接", detail)
```

- [ ] **Step 2: Add the safety test for zero active connections**

Add this method to `PackDoctorTests`:

```python
def test_browser_harness_health_rejects_zero_active_connections(self):
    completed = SimpleNamespace(
        stdout=(
            "browser-harness doctor\n"
            "  [ok  ] daemon alive\n"
            "  [FAIL] active browser connections — 0\n"
        ),
        stderr="",
        returncode=1,
    )
    ready, detail = pack_doctor.browser_harness_health(
        runner=lambda *args, **kwargs: completed
    )
    self.assertFalse(ready)
    self.assertIn("没有活动浏览器连接", detail)
```

- [ ] **Step 3: Run both parser tests and verify RED**

Run:

```powershell
& 'C:\Users\fddfd\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest tests.test_scripts.PackDoctorTests.test_browser_harness_health_accepts_local_connection_with_optional_cloud_failure tests.test_scripts.PackDoctorTests.test_browser_harness_health_rejects_zero_active_connections -v
```

Expected: the healthy-output test `FAIL`s because the Task 1 stub always returns false; the zero-connection safety test may already pass.

- [ ] **Step 4: Implement the bounded BrowserHarness health parser**

Add imports:

```python
import re
import subprocess
```

Replace the Task 1 stub with:

```python
def browser_harness_health(
    command: str = "browser-harness",
    *,
    runner=None,
) -> tuple[bool, str]:
    run = runner or subprocess.run
    try:
        completed = run(
            [command, "--doctor"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False, "browser-harness doctor 无法完成"

    output = f"{completed.stdout}\n{completed.stderr}"
    daemon_ok = re.search(r"\[ok\s*\]\s+daemon alive\b", output, re.IGNORECASE)
    active = re.search(
        r"\[ok\s*\]\s+active browser connections\s+[—-]\s+(\d+)",
        output,
        re.IGNORECASE,
    )
    if daemon_ok and active and int(active.group(1)) >= 1:
        return True, "browser-harness daemon 正常且存在活动浏览器连接"
    return False, "browser-harness daemon 未就绪或没有活动浏览器连接"
```

Do not include the captured doctor output in the returned detail; it can contain an active page title and URL.

- [ ] **Step 5: Run the parser and compatibility tests**

Run:

```powershell
& 'C:\Users\fddfd\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest tests.test_scripts.PackDoctorTests -v
```

Expected: all `PackDoctorTests` pass.

- [ ] **Step 6: Commit the health parser**

```powershell
git add tests/test_scripts.py .agents/skills/magewell-douyin-intelligence/scripts/pack_doctor.py
git commit -m "fix: verify BrowserHarness health for Chrome 147"
```

### Task 3: Run full project and live-environment verification

**Files:**
- Verify: `tests/test_scripts.py`
- Verify: `tests/test_metadata.py`
- Verify: `.agents/skills/magewell-douyin-intelligence/scripts/pack_doctor.py`
- Verify: `config/collection.local.json`

- [ ] **Step 1: Run every unit test**

Run:

```powershell
& 'C:\Users\fddfd\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest discover -s tests -v
```

Expected: all tests pass with `OK`.

- [ ] **Step 2: Locate and run the repository quick validator**

Run:

```powershell
rg --files | rg '(^|[\\/])quick_validate\.py$'
```

If a path is returned, run it with the bundled Python and require exit code 0. If no path is returned, record that the repository does not provide `quick_validate.py`; do not invent a replacement or claim it passed.

- [ ] **Step 3: Run BrowserHarness doctor without exposing captured output in project results**

Run:

```powershell
& 'C:\Users\fddfd\.local\bin\browser-harness.exe' --doctor
```

Expected:

```text
[ok  ] daemon alive
[ok  ] active browser connections — 1
```

The optional Browser Use Cloud auth check may remain failed.

- [ ] **Step 4: Run the real pack doctor**

Run:

```powershell
$env:PATH='C:\Users\fddfd\.local\bin;C:\Users\fddfd\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin;' + $env:PATH
& 'C:\Users\fddfd\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' '.agents\skills\magewell-douyin-intelligence\scripts\pack_doctor.py' --config 'config\collection.local.json'
```

Expected JSON conditions:

```json
{
  "status": "success",
  "checks": {
    "opencli": {"status": "success"},
    "browser-harness": {"status": "success"},
    "last30days": {"status": "success"},
    "last30days-cn": {"status": "success"},
    "scrapling": {"status": "success"},
    "cloakbrowser": {"status": "compliant_skip"}
  }
}
```

- [ ] **Step 5: Verify repository hygiene**

Run:

```powershell
git diff --check
git status --short --branch
git diff -- .agents/skills/magewell-douyin-intelligence/scripts/pack_doctor.py tests/test_scripts.py
```

Expected:

- no whitespace errors;
- `config/collection.local.json` is not listed;
- no browser data, OpenCLI trace, raw report, or credential file is staged;
- only intentional code/test/plan changes and the known local `work/` installer directory are visible.

- [ ] **Step 6: Report the verified installation state**

Report exact installed versions and fresh verification evidence:

- OpenCLI v1.8.6 with connected Profile `cw4ud6q8`;
- BrowserHarness v0.1.8 with an active local connection;
- last30days v3.18.3;
- last30days-cn v3.2.0-cn;
- Scrapling v0.4.12 and its successful DynamicFetcher smoke test;
- full unit-test count and `pack_doctor.py` overall `success`;
- Cloakbrowser remains `compliant_skip` because no fingerprint or anti-automation error occurred.

Do not push the branch without the user's separate final confirmation.
