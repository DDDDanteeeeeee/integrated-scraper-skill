#!/usr/bin/env python3
"""Verify every declared Douyin Skill Pack dependency without installing anything."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path


def load_doctor_module():
    spec = importlib.util.spec_from_file_location("douyin_pack_doctor_dependency", Path(__file__).with_name("doctor.py"))
    if spec is None or spec.loader is None:
        raise RuntimeError("无法加载 doctor.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


doctor = load_doctor_module()


PROJECT_ROOT = Path(__file__).resolve().parents[4]
MANIFEST_PATH = PROJECT_ROOT / "dependencies.manifest.json"
CONFIG_PATH = PROJECT_ROOT / "config" / "collection.local.json"
REQUIRED_IDS = ("opencli", "browser-harness", "last30days", "last30days-cn", "scrapling")
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
    if any(identifier not in by_id for identifier in (*REQUIRED_IDS, "cloakbrowser")):
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


def check_pack(
    config: dict,
    manifest: dict,
    skill_roots: list[Path],
    *,
    command_checker=doctor.command_available,
    cdp_probe=doctor.probe_cdp,
) -> dict:
    entries = validate_manifest(manifest)
    base = doctor.check(config, command_checker=command_checker, cdp_probe=cdp_probe)
    if base["status"] != "checked":
        return {"status": base["status"], "checks": {}, "detail": base.get("error", "本机配置无效")}

    checks: dict[str, dict[str, object]] = {}
    opencli_ready = bool(base["checks"]["opencli"]["ready"])
    checks["opencli"] = {"status": "success" if opencli_ready else "blocked_dependency", **base["checks"]["opencli"]}

    browser_skill = find_skill("browser-harness", skill_roots)
    browser_cli = command_checker("browser-harness")
    browser_cdp = bool(base["checks"]["browser"]["ready"])
    if not browser_skill or not browser_cli:
        browser_status = "blocked_dependency"
        browser_detail = "需要已安装的 browser-harness Skill 与本机命令"
    elif not browser_cdp:
        browser_status = "awaiting_human"
        browser_detail = str(base["checks"]["browser"]["detail"])
    else:
        browser_status = "success"
        browser_detail = "Skill、命令和本机 CDP 已就绪"
    checks["browser-harness"] = {"status": browser_status, "ready": browser_status == "success", "detail": browser_detail}

    for skill_id in ("last30days", "last30days-cn"):
        skill_path = find_skill(skill_id, skill_roots)
        checks[skill_id] = {
            "status": "success" if skill_path else "blocked_dependency",
            "ready": bool(skill_path),
            "detail": str(skill_path) if skill_path else f"未在已检查的 Codex Skill 目录中找到 {skill_id}",
        }

    scrapling_ready = bool(base["checks"]["scrapling"]["ready"])
    checks["scrapling"] = {"status": "success" if scrapling_ready else "blocked_dependency", **base["checks"]["scrapling"]}

    cloak_skill = find_skill("cloakbrowser", skill_roots)
    checks["cloakbrowser"] = {
        "status": "compliant_skip",
        "ready": True,
        "available": bool(cloak_skill),
        "detail": "条件化依赖；无明确指纹/反自动化错误时不得安装或启动",
    }

    statuses = {identifier: item["status"] for identifier, item in checks.items()}
    if any(status == "blocked_dependency" for identifier, status in statuses.items() if identifier in REQUIRED_IDS):
        status = "blocked_dependency"
    elif statuses["browser-harness"] == "awaiting_human":
        status = "awaiting_human"
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
    return {"status": status, "checks": checks, "resolution": resolution}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--skills-root", type=Path, action="append", default=[])
    args = parser.parse_args()
    if not args.config.is_file():
        print(json.dumps({"status": "awaiting_human", "missing": ["config"], "next_action": "先运行 initialize.py 创建本机配置"}, ensure_ascii=False))
        return 2
    try:
        config = read_json(args.config)
        manifest = read_json(args.manifest)
        roots = args.skills_root or default_skill_roots()
        result = check_pack(config, manifest, roots)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"status": "invalid_config", "error": str(error)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "success" else 2


if __name__ == "__main__":
    raise SystemExit(main())
