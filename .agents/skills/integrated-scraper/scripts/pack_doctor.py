#!/usr/bin/env python3
"""Verify full-pack or task-scoped scraper dependencies without installing anything."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess


def load_doctor_module():
    spec = importlib.util.spec_from_file_location("integrated_scraper_pack_doctor_dependency", Path(__file__).with_name("doctor.py"))
    if spec is None or spec.loader is None:
        raise RuntimeError("无法加载 doctor.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


doctor = load_doctor_module()


PROJECT_ROOT = Path(__file__).resolve().parents[4]
MANIFEST_PATH = PROJECT_ROOT / "dependencies.manifest.json"
CONFIG_PATH = PROJECT_ROOT / "config" / "collection.local.json"
RUNTIME_CONTRACT_PATH = PROJECT_ROOT / "runtime.contract.json"
START_CHROME_PATH = PROJECT_ROOT / ".agents" / "skills" / "integrated-scraper" / "scripts" / "start_project_chrome.ps1"
FULL_PACK_IDS = ("opencli", "browser-harness", "last30days", "last30days-cn", "scrapling", "playwright", "yt-dlp")
SKILL_IDS = ("browser-harness", "last30days", "last30days-cn", "cloakbrowser")


def default_skill_roots() -> list[Path]:
    return [PROJECT_ROOT / ".agents" / "skills", Path.home() / ".codex" / "skills", Path.home() / ".agents" / "skills"]


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} 必须是 JSON 对象")
    return value


def validate_manifest(manifest: dict) -> dict[str, dict]:
    if manifest.get("manifest_type") != "installation-manifest":
        raise ValueError("依赖文件必须是 installation-manifest")
    entries = manifest.get("dependencies")
    if not isinstance(entries, list):
        raise ValueError("dependencies 必须是数组")
    by_id = {entry.get("id"): entry for entry in entries if isinstance(entry, dict)}
    if any(identifier not in by_id for identifier in (*FULL_PACK_IDS, "cloakbrowser")):
        raise ValueError("依赖清单缺少必需条目")
    for identifier, entry in by_id.items():
        if (
            not isinstance(entry.get("source_url"), (str, type(None)))
            or not entry.get("verification")
            or "installation" not in entry
            or not entry.get("version_policy")
        ):
            raise ValueError(f"依赖清单条目不完整：{identifier}")
    return by_id


def find_skill(skill_id: str, roots: list[Path]) -> Path | None:
    for root in roots:
        candidate = root / skill_id / "SKILL.md"
        if candidate.is_file():
            return candidate
    return None


def command_line(command: str, arguments: list[str]) -> list[str]:
    if os.name == "nt" and Path(command).suffix.lower() in {".cmd", ".bat"}:
        return ["cmd.exe", "/d", "/s", "/c", subprocess.list2cmdline([command, *arguments])]
    return [command, *arguments]


def smoke_command(command: str, arguments: list[str], expected: str) -> tuple[bool, str]:
    try:
        completed = subprocess.run(
            command_line(command, arguments),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=20,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return False, str(error)
    output = "\n".join(part.strip() for part in (completed.stdout, completed.stderr) if part.strip())
    ready = completed.returncode == 0 and re.search(rf"(?<![\w.]){re.escape(expected)}(?![\w.])", output) is not None
    return ready, output or f"exit={completed.returncode}"


def opencli_profile_probe(command: str, profile: str, expected_extension: str) -> tuple[bool, str]:
    try:
        completed = subprocess.run(
            command_line(command, ["profile", "list"]),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=20,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return False, str(error)
    matching = next((line.strip() for line in completed.stdout.splitlines() if re.search(rf"\b{re.escape(profile)}\b", line)), "")
    ready = completed.returncode == 0 and re.search(r"(?<![\w-])connected(?![\w-])", matching) is not None and f"v{expected_extension}" in matching
    return ready, matching or f"未发现已连接的 OpenCLI Profile：{profile}"


def skill_frontmatter_version(path: Path) -> str:
    match = re.search(r'^version:\s*["\']?([^"\'\r\n]+)', path.read_text(encoding="utf-8"), re.MULTILINE)
    return match.group(1).strip() if match else "unknown"


def project_chrome_probe() -> tuple[bool, str]:
    powershell = Path(r"C:\Program Files\PowerShell\7\pwsh.exe")
    executable = str(powershell) if powershell.is_file() else "powershell.exe"
    try:
        completed = subprocess.run(
            [executable, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(START_CHROME_PATH), "-CheckOnly"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=20,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return False, str(error)
    detail = completed.stdout.strip() or completed.stderr.strip() or f"exit={completed.returncode}"
    return completed.returncode == 0, detail


def check_pack(
    config: dict,
    manifest: dict,
    skill_roots: list[Path],
    *,
    command_checker=doctor.command_available,
    cdp_probe=doctor.probe_cdp,
    smoke_checker=smoke_command,
    profile_checker=opencli_profile_probe,
    chrome_owner_checker=project_chrome_probe,
    version_reader=skill_frontmatter_version,
    required_dependencies: set[str] | None = None,
) -> dict:
    entries = validate_manifest(manifest)
    contract = read_json(RUNTIME_CONTRACT_PATH)
    active_required = set(FULL_PACK_IDS) if required_dependencies is None else set(required_dependencies)
    unknown_required = active_required - set(entries)
    if unknown_required:
        raise ValueError(f"任务计划包含未登记依赖：{', '.join(sorted(unknown_required))}")
    if not active_required:
        raise ValueError("任务计划没有声明任何必需依赖")
    expected_versions = contract.get("tested_versions", {})
    base_required: set[str] = set()
    if "opencli" in active_required:
        base_required.add("opencli")
    if "browser-harness" in active_required:
        base_required.add("browser")
    if "scrapling" in active_required:
        base_required.add("scrapling")
    if "yt-dlp" in active_required:
        base_required.add("yt-dlp")
    if "playwright" in active_required:
        base_required.add("python")
    base = doctor.check(
        config,
        command_checker=command_checker,
        cdp_probe=cdp_probe,
        required_checks=base_required,
    )
    if base["status"] != "checked":
        return {"status": base["status"], "checks": {}, "detail": base.get("error", "本机配置无效")}

    checks: dict[str, dict[str, object]] = {}
    if "opencli" not in active_required:
        checks["opencli"] = {"status": "not_checked", "ready": None, "detail": "本次计划未选择 OpenCLI"}
    else:
        opencli_config = config.get("opencli", {})
        opencli_command = opencli_config.get("command") if isinstance(opencli_config, dict) else None
        opencli_profile = opencli_config.get("profile") if isinstance(opencli_config, dict) else None
        opencli_installed = bool(base["checks"]["opencli"]["ready"])
        opencli_smoke = smoke_checker(str(opencli_command), ["--version"], str(expected_versions["opencli"])) if opencli_installed else (False, "命令不可用")
        profile_ready = profile_checker(str(opencli_command), str(opencli_profile), str(expected_versions["opencli_extension"])) if opencli_smoke[0] else (False, "OpenCLI 未通过版本检查")
        if not opencli_installed or not opencli_smoke[0]:
            opencli_status = "blocked_dependency"
            opencli_detail = opencli_smoke[1]
        elif not profile_ready[0]:
            opencli_status = "awaiting_human"
            opencli_detail = profile_ready[1]
        else:
            opencli_status = "success"
            opencli_detail = f"OpenCLI {expected_versions['opencli']}；{profile_ready[1]}"
        checks["opencli"] = {"status": opencli_status, "ready": opencli_status == "success", "detail": opencli_detail}

    if "browser-harness" not in active_required:
        checks["browser-harness"] = {"status": "not_checked", "ready": None, "detail": "本次计划未选择 BrowserHarness"}
    else:
        browser_skill = find_skill("browser-harness", skill_roots)
        browser_config = config.get("browser_harness", {})
        browser_command = browser_config.get("command") if isinstance(browser_config, dict) else None
        browser_cli = command_checker(browser_command or "browser-harness")
        browser_smoke = smoke_checker(str(browser_command or "browser-harness"), ["--version"], str(expected_versions["browser_harness"])) if browser_cli else (False, "命令不可用")
        browser_cdp = bool(base["checks"]["browser"]["ready"])
        chrome_owned = chrome_owner_checker() if browser_cdp else (False, "项目 Chrome 未运行")
        if not browser_skill or not browser_cli or not browser_smoke[0]:
            browser_status = "blocked_dependency"
            browser_detail = browser_smoke[1] if browser_cli else "需要已安装的 browser-harness Skill 与本机命令"
        elif not browser_cdp or not chrome_owned[0]:
            browser_status = "awaiting_human"
            browser_detail = str(base["checks"]["browser"]["detail"] if not browser_cdp else chrome_owned[1])
        else:
            browser_status = "success"
            browser_detail = f"BrowserHarness {expected_versions['browser_harness']}；固定项目 Chrome 127.0.0.1:9222 已就绪"
        checks["browser-harness"] = {"status": browser_status, "ready": browser_status == "success", "detail": browser_detail}

    for skill_id in ("last30days", "last30days-cn"):
        if skill_id not in active_required:
            checks[skill_id] = {"status": "not_checked", "ready": None, "detail": f"本次计划未选择 {skill_id}"}
            continue
        skill_path = find_skill(skill_id, skill_roots)
        expected_key = "last30days" if skill_id == "last30days" else "last30days_cn"
        observed_version = version_reader(skill_path) if skill_path else "missing"
        version_ready = observed_version == str(expected_versions[expected_key])
        checks[skill_id] = {
            "status": "success" if skill_path and version_ready else "blocked_dependency",
            "ready": bool(skill_path and version_ready),
            "detail": f"{skill_path}；version={observed_version}" if skill_path else f"未在已检查的 Codex Skill 目录中找到 {skill_id}",
        }

    if "scrapling" not in active_required:
        checks["scrapling"] = {"status": "not_checked", "ready": None, "detail": "本次计划未选择 Scrapling"}
    else:
        scrapling_config = config.get("scrapling", {})
        scrapling_command = scrapling_config.get("executable") if isinstance(scrapling_config, dict) else None
        scrapling_installed = bool(base["checks"]["scrapling"]["ready"])
        scrapling_smoke = smoke_checker(str(scrapling_command), ["--version"], str(expected_versions["scrapling"])) if scrapling_installed else (False, "命令不可用")
        checks["scrapling"] = {"status": "success" if scrapling_smoke[0] else "blocked_dependency", "ready": scrapling_smoke[0], "detail": scrapling_smoke[1]}

    if "playwright" not in active_required:
        checks["playwright"] = {"status": "not_checked", "ready": None, "detail": "本次计划未声明 Playwright"}
    else:
        python_config = config.get("python", {})
        python_command = python_config.get("executable") if isinstance(python_config, dict) else None
        python_installed = bool(base["checks"]["python"]["ready"])
        python_smoke = smoke_checker(str(python_command), ["--version"], str(expected_versions["python"])) if python_installed else (False, "项目 Python 不可用")
        playwright_smoke = smoke_checker(
            str(python_command),
            ["-c", "import importlib.metadata as m; print(m.version('playwright'))"],
            str(expected_versions["playwright"]),
        ) if python_smoke[0] else (False, python_smoke[1])
        if playwright_smoke[0]:
            browser_path = python_config.get("playwright_browsers_path")
            script = "import os; os.environ['PLAYWRIGHT_BROWSERS_PATH']=" + repr(str(browser_path)) + "; from pathlib import Path; from playwright.sync_api import sync_playwright; p=sync_playwright().start(); assert Path(p.chromium.executable_path).is_file(), 'Playwright Chromium binary missing'; p.stop(); print('browser-binary-present')"
            playwright_smoke = smoke_checker(str(python_command), ["-c", script], "browser-binary-present")
        checks["playwright"] = {"status": "success" if playwright_smoke[0] else "blocked_dependency", "ready": playwright_smoke[0], "detail": playwright_smoke[1]}

    if "yt-dlp" not in active_required:
        checks["yt-dlp"] = {"status": "not_checked", "ready": None, "detail": "本次计划未声明 yt-dlp"}
    else:
        yt_dlp_config = config.get("yt_dlp", {})
        yt_dlp_command = yt_dlp_config.get("executable") if isinstance(yt_dlp_config, dict) else None
        yt_dlp_installed = bool(base["checks"]["yt-dlp"]["ready"])
        yt_dlp_smoke = smoke_checker(str(yt_dlp_command), ["--version"], str(expected_versions["yt_dlp"])) if yt_dlp_installed else (False, "命令不可用")
        checks["yt-dlp"] = {"status": "success" if yt_dlp_smoke[0] else "blocked_dependency", "ready": yt_dlp_smoke[0], "detail": yt_dlp_smoke[1]}

    cloak_skill = find_skill("cloakbrowser", skill_roots)
    if "cloakbrowser" in active_required:
        checks["cloakbrowser"] = {
            "status": "unassessed" if cloak_skill else "blocked_dependency",
            "ready": False,
            "available": bool(cloak_skill),
            "detail": "仅找到 Skill；9242 浏览器运行时和归属尚未验证，不能声明就绪" if cloak_skill else "已触发指纹兼容路径，但未找到 Cloakbrowser Skill",
        }
    else:
        checks["cloakbrowser"] = {
            "status": "compliant_skip",
            "ready": True,
            "available": bool(cloak_skill),
            "detail": "本次任务未触发明确指纹/反自动化兼容错误",
        }

    statuses = {identifier: item["status"] for identifier, item in checks.items()}
    if any(statuses.get(identifier) == "blocked_dependency" for identifier in active_required):
        status = "blocked_dependency"
    elif any(statuses.get(identifier) == "awaiting_human" for identifier in active_required):
        status = "awaiting_human"
    elif any(statuses.get(identifier) == "unassessed" for identifier in active_required):
        status = "unassessed"
    else:
        status = "success"
    resolution = {
        key: {
            "required": entries[key]["required"],
            "source_url": entries[key]["source_url"],
            "version_policy": entries[key]["version_policy"],
            "license": entries[key]["license"],
            "installation": entries[key]["installation"],
        }
        for key in entries
    }
    return {
        "status": status,
        "scope": "full_pack" if required_dependencies is None else "task_plan",
        "required_dependencies": sorted(active_required),
        "checks": checks,
        "resolution": resolution,
    }


def plan_requirements(plan: dict, contract: dict) -> set[str]:
    if plan.get("routing_policy") != contract.get("execution", {}).get("routing_mode"):
        raise ValueError("execution_plan 的路由模式与 runtime.contract.json 不一致")
    registry = contract.get("tool_routing", {}).get("tools", {})
    work_items = plan.get("work_items")
    if not isinstance(work_items, list) or not work_items:
        raise ValueError("execution_plan.work_items 必须是非空数组")
    expected_tools: set[str] = set()
    expected_dependencies: set[str] = set()
    for item in work_items:
        if not isinstance(item, dict):
            raise ValueError("execution_plan.work_items 只能包含对象")
        verification_tools = item.get("verification_tools", [])
        if not isinstance(verification_tools, list):
            raise ValueError("execution_plan.verification_tools 必须是数组")
        active_tools = [item.get("primary_tool"), *verification_tools]
        candidates = {
            candidate.get("tool"): candidate
            for candidate in item.get("candidates", [])
            if isinstance(candidate, dict)
        }
        for tool_id in active_tools:
            if tool_id not in registry or tool_id not in candidates:
                raise ValueError(f"execution_plan 使用未登记或未入选的工具：{tool_id}")
            expected_tools.add(tool_id)
            expected_dependencies.update(registry[tool_id].get("base_dependencies", []))
            expected_dependencies.update(candidates[tool_id].get("extra_dependencies", []))
    if set(plan.get("required_tools", [])) != expected_tools:
        raise ValueError("execution_plan.required_tools 与主工具/核验工具不一致")
    required = plan.get("required_dependencies")
    if not isinstance(required, list) or not required or any(not isinstance(item, str) for item in required):
        raise ValueError("execution_plan.required_dependencies 必须是非空字符串数组")
    if set(required) != expected_dependencies:
        raise ValueError("execution_plan.required_dependencies 与已选工具不一致")
    return set(required)


def tool_requirements(tool_ids: list[str], contract: dict) -> set[str]:
    registry = contract.get("tool_routing", {}).get("tools", {})
    required: set[str] = set()
    for tool_id in tool_ids:
        if tool_id not in registry:
            raise ValueError(f"未登记工具：{tool_id}")
        required.update(registry[tool_id].get("base_dependencies", []))
    return required


def selected_requirements(plan: dict, contract: dict, work_id: str, tool_id: str) -> set[str]:
    """Check only this atomic attempt, including its declared auxiliary dependencies."""
    plan_requirements(plan, contract)
    matches = [item for item in plan["work_items"] if item.get("id") == work_id]
    if len(matches) != 1:
        raise ValueError("必须指定唯一的原子任务")
    candidates = [item for item in matches[0]["candidates"] if item.get("tool") == tool_id]
    if len(candidates) != 1:
        raise ValueError("该工具不在原子任务候选中")
    return tool_requirements([tool_id], contract) | set(candidates[0].get("extra_dependencies", []))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--skills-root", type=Path, action="append", default=[])
    parser.add_argument("--plan", type=Path, help="只让本次计划实际需要的依赖影响总体状态")
    parser.add_argument("--work-item", help="限定当前原子任务，配合 --plan 和一个 --require-tool")
    parser.add_argument("--require-tool", action="append", default=[], help="降级前追加检查一个候选工具")
    parser.add_argument("--require-dependency", action="append", default=[], help="追加检查工具所需的辅助依赖")
    args = parser.parse_args()
    if not args.config.is_file():
        print(json.dumps({"status": "awaiting_human", "missing": ["config"], "next_action": "先运行 initialize.py 创建本机配置"}, ensure_ascii=False))
        return 2
    try:
        config = read_json(args.config)
        manifest = read_json(args.manifest)
        contract = read_json(RUNTIME_CONTRACT_PATH)
        required_dependencies: set[str] | None = None
        if args.plan:
            plan = read_json(args.plan)
            if args.work_item:
                if len(args.require_tool) != 1:
                    raise ValueError("--work-item 必须搭配一个 --require-tool")
                required_dependencies = selected_requirements(plan, contract, args.work_item, args.require_tool[0])
            else:
                required_dependencies = plan_requirements(plan, contract)
                if args.require_tool:
                    raise ValueError("降级检查请指定 --work-item，避免检查已失败主工具")
        elif args.work_item:
            raise ValueError("--work-item 必须搭配 --plan")
        if args.require_tool or args.require_dependency:
            if required_dependencies is None:
                required_dependencies = set()
            required_dependencies.update(tool_requirements(args.require_tool, contract))
            required_dependencies.update(args.require_dependency)
        roots = args.skills_root or default_skill_roots()
        result = check_pack(config, manifest, roots, required_dependencies=required_dependencies)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"status": "invalid_config", "error": str(error)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "success" else 2


if __name__ == "__main__":
    raise SystemExit(main())
