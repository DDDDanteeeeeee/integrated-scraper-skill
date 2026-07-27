#!/usr/bin/env python3
"""Validate that six-round status records truthfully describe a Douyin run."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROUNDS = ("01-opencli", "02-last30days", "03-last30days-cn", "04-browser-harness", "05-scrapling", "06-cloakbrowser")
ALLOWED = {"success", "partial_success", "awaiting_human", "blocked_user_action", "blocked_dependency", "compliant_skip", "failed"}
BLOCKING = {"awaiting_human", "blocked_user_action", "blocked_dependency", "failed"}
NO_FULL_SUCCESS = BLOCKING | {"partial_success"}
REQUIRED_MANIFEST_FIELDS = ("round", "skill", "task_id", "status", "timestamp", "target", "result")
REQUIRED_TASK_FIELDS = (
    "task_id",
    "target",
    "objective",
    "time_range",
    "decision_context",
    "success_criteria",
)


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} 必须是 JSON 对象")
    return value


def validate(rounds_dir: Path, summary_path: Path) -> list[str]:
    errors: list[str] = []
    statuses: list[str] = []
    task_path = rounds_dir.parent / "task.json"
    try:
        task = read_json(task_path)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return [str(error)]
    for field in REQUIRED_TASK_FIELDS:
        if field not in task:
            errors.append(f"缺少任务字段：{field}")
    task_id = task.get("task_id")
    task_target = task.get("target")
    for name in ROUNDS:
        path = rounds_dir / name / "round_manifest.json"
        if not path.is_file():
            errors.append(f"缺少 manifest：{name}")
            continue
        try:
            manifest = read_json(path)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            errors.append(str(error))
            continue
        if manifest.get("round") != name:
            errors.append(f"轮次名称不一致：{name}")
        for field in REQUIRED_MANIFEST_FIELDS:
            if field not in manifest:
                errors.append(f"缺少 manifest 字段：{name}.{field}")
        if manifest.get("task_id") != task_id:
            errors.append(f"任务 ID 不一致：{name}")
        if manifest.get("target") != task_target:
            errors.append(f"研究对象不一致：{name}")
        status = manifest.get("status")
        if status not in ALLOWED:
            errors.append(f"无效状态：{name}={status}")
        else:
            statuses.append(status)
            if status not in {"success", "compliant_skip"} and "recovery_condition" not in manifest:
                errors.append(f"非成功轮次缺少恢复条件：{name}")
    try:
        summary = read_json(summary_path)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return errors + [str(error)]
    overall = summary.get("overall_status")
    if overall not in ALLOWED:
        errors.append(f"无效总体状态：{overall}")
    if any(status in NO_FULL_SUCCESS for status in statuses) and overall == "success":
        errors.append("存在部分成功、阻塞或失败轮次时总体状态不得为 success")
    if summary.get("current_douyin_primary_evidence") is not True and overall == "success":
        errors.append("主抖音证据未明确存在时总体状态不得为 success")
    if summary.get("task_id") != task_id:
        errors.append("summary.task_id 与 task.json 不一致")
    if summary.get("target") != task_target:
        errors.append("summary.target 与 task.json 不一致")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rounds-dir", required=True, type=Path)
    parser.add_argument("--summary", required=True, type=Path)
    args = parser.parse_args()
    errors = validate(args.rounds_dir, args.summary)
    print(json.dumps({"ok": not errors, "errors": errors}, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
