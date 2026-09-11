#!/usr/bin/env python3
"""Validate an atomic best-tool scraper run and its acceptance results."""

from __future__ import annotations

import argparse
from collections import Counter
import json
import importlib.util
from pathlib import Path


def sibling(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


planner = sibling("plan_run")
evidence = sibling("evidence_contract")


EXECUTION_ALLOWED = {
    "success",
    "empty_verified",
    "partial_success",
    "awaiting_human",
    "blocked_user_action",
    "blocked_dependency",
    "unassessed",
    "failed",
}
OVERALL_ALLOWED = {
    "success",
    "partial_success",
    "awaiting_human",
    "blocked_user_action",
    "blocked_dependency",
    "failed",
}
ACCEPTED = {"success", "empty_verified"}
REQUIRED_TASK_FIELDS = (
    "task_id",
    "target",
    "objective",
    "time_range",
    "decision_context",
    "success_criteria",
    "work_items",
)
REQUIRED_EXECUTION_FIELDS = (
    "execution_id",
    "attempt_index",
    "work_item_id",
    "tool",
    "task_id",
    "status",
    "timestamp",
    "target",
    "acceptance_passed",
    "result",
)


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} 必须是 JSON 对象")
    return value


def _load_execution_manifests(run_dir: Path, work_id: str) -> tuple[list[dict], list[str]]:
    errors: list[str] = []
    execution_dir = run_dir / "work-items" / work_id / "executions"
    manifests: list[dict] = []
    if not execution_dir.is_dir():
        return [], [f"缺少原子任务执行目录：{work_id}"]
    for path in execution_dir.glob("*/execution_manifest.json"):
        try:
            manifest = read_json(path)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            errors.append(str(error))
            continue
        manifests.append(manifest)
    manifests.sort(key=lambda item: item.get("attempt_index", 0) if isinstance(item.get("attempt_index"), int) else 0)
    if not manifests:
        errors.append(f"原子任务没有执行 manifest：{work_id}")
    return manifests, errors


def _validate_manifest(
    manifest: dict,
    *,
    work_id: str,
    task_id: object,
    target: object,
    candidate_tools: set[str],
    run_dir: Path,
    criteria: list[str],
    task_fingerprint: str,
) -> list[str]:
    errors: list[str] = []
    execution_id = manifest.get("execution_id", "unknown")
    for field in REQUIRED_EXECUTION_FIELDS:
        if field not in manifest:
            errors.append(f"缺少 execution manifest 字段：{execution_id}.{field}")
    if manifest.get("work_item_id") != work_id:
        errors.append(f"原子任务 ID 不一致：{execution_id}")
    if manifest.get("task_id") != task_id:
        errors.append(f"任务 ID 不一致：{execution_id}")
    if manifest.get("target") != target:
        errors.append(f"研究对象不一致：{execution_id}")
    if manifest.get("task_fingerprint") != task_fingerprint:
        errors.append(f"执行记录不属于当前任务版本：{execution_id}")
    if manifest.get("tool") not in candidate_tools:
        errors.append(f"执行了未入选候选集的工具：{execution_id}={manifest.get('tool')}")
    status = manifest.get("status")
    if status not in EXECUTION_ALLOWED:
        errors.append(f"无效执行状态：{execution_id}={status}")
        return errors
    accepted = manifest.get("acceptance_passed")
    if status in ACCEPTED and accepted is not True:
        errors.append(f"成功执行必须通过验收：{execution_id}")
    if status not in ACCEPTED and accepted is not False:
        errors.append(f"未成功执行不得标记通过验收：{execution_id}")
    result = manifest.get("result")
    if not isinstance(result, dict):
        errors.append(f"result 必须是对象：{execution_id}")
    elif status == "success" and (not isinstance(result.get("evidence_count"), int) or result["evidence_count"] < 1):
        errors.append(f"success 必须记录正数 evidence_count：{execution_id}")
    elif status == "empty_verified" and (
        result.get("empty_verified") is not True
        or not isinstance(result.get("empty_evidence"), list)
        or not result["empty_evidence"]
    ):
        errors.append(f"empty_verified 必须保留明确的零结果证据：{execution_id}")
    if status not in ACCEPTED and not manifest.get("recovery_condition"):
        errors.append(f"未通过验收的执行缺少恢复条件：{execution_id}")
    if not isinstance(execution_id, str) or not execution_id:
        errors.append("execution_id 必须为非空字符串")
    if not evidence.timestamp(manifest.get("timestamp")):
        errors.append(f"执行时间无效：{execution_id}")
    if type(manifest.get("attempt_index")) is not int:
        errors.append(f"attempt_index 必须为整数：{execution_id}")
    if status in ACCEPTED and isinstance(result, dict):
        errors.extend(f"{execution_id}: {error}" for error in evidence.validate_evidence(result, run_dir, criteria, status))
    return errors


def validate(run_dir: Path, summary_path: Path, max_attempts_per_tool: int | None = None) -> list[str]:
    errors: list[str] = []
    try:
        task = read_json(run_dir / "task.json")
        plan = read_json(run_dir / "execution_plan.json")
        contract = read_json(planner.RUNTIME_CONTRACT_PATH)
        expected_plan = planner.build_plan(task, contract)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return [str(error)]
    # Plans are derived data. Never accept edited criteria, risk or ranking as authority.
    for field, value in expected_plan.items():
        if field != "generated_at" and plan.get(field) != value:
            errors.append(f"execution_plan 与当前任务/运行契约不一致：{field}；旧记录须保留，重新规划后执行")
    if errors:
        return errors
    limit = 1 + contract["execution"]["max_recovery_attempts_per_tool"]
    if max_attempts_per_tool is not None:
        if not 1 <= max_attempts_per_tool <= limit:
            return ["不得通过参数放宽运行契约的恢复上限"]
        limit = max_attempts_per_tool
    for field in REQUIRED_TASK_FIELDS:
        if field not in task:
            errors.append(f"缺少任务字段：{field}")
    task_id = task.get("task_id")
    target = task.get("target")
    if plan.get("task_id") != task_id:
        errors.append("execution_plan.task_id 与 task.json 不一致")
    if plan.get("target") != target:
        errors.append("execution_plan.target 与 task.json 不一致")
    if plan.get("routing_policy") != "atomic-best-tool":
        errors.append("execution_plan.routing_policy 必须是 atomic-best-tool")

    plan_items = plan.get("work_items")
    if not isinstance(plan_items, list) or not plan_items:
        return errors + ["execution_plan.work_items 必须是非空数组"]
    task_work_ids = {item.get("id") for item in task.get("work_items", []) if isinstance(item, dict)}
    plan_work_ids = {item.get("id") for item in plan_items if isinstance(item, dict)}
    if task_work_ids != plan_work_ids:
        errors.append("execution_plan 原子任务集合与 task.json 不一致")

    accepted_by_work: dict[str, list[str]] = {}
    manifest_by_id: dict[str, dict] = {}
    complete_by_work: dict[str, bool] = {}
    last_by_work: dict[str, str] = {}
    for item in plan_items:
        work_id = item.get("id")
        if not isinstance(work_id, str):
            errors.append("execution_plan 中存在无效原子任务 ID")
            continue
        candidates = item.get("candidates", [])
        ranked_tools = [candidate.get("tool") for candidate in candidates if isinstance(candidate, dict)]
        candidate_tools = set(ranked_tools)
        if not ranked_tools or item.get("primary_tool") != ranked_tools[0]:
            errors.append(f"主工具与排名不一致：{work_id}")
        if item.get("fallback_tools") != ranked_tools[1:]:
            errors.append(f"降级顺序与排名不一致：{work_id}")

        manifests, manifest_errors = _load_execution_manifests(run_dir, work_id)
        errors.extend(manifest_errors)
        for expected_index, manifest in enumerate(manifests, start=1):
            errors.extend(
                _validate_manifest(
                    manifest,
                    work_id=work_id,
                    task_id=task_id,
                    target=target,
                    candidate_tools=candidate_tools,
                    run_dir=run_dir,
                    criteria=item["acceptance_criteria"],
                    task_fingerprint=plan["task_fingerprint"],
                )
            )
            if manifest.get("attempt_index") != expected_index:
                errors.append(f"attempt_index 必须从 1 连续递增：{work_id}")
            execution_id = manifest.get("execution_id")
            if execution_id in manifest_by_id:
                errors.append(f"execution_id 重复：{execution_id}")
            elif isinstance(execution_id, str):
                manifest_by_id[execution_id] = manifest

        counts = Counter(manifest.get("tool") for manifest in manifests if manifest.get("status") not in {"awaiting_human", "blocked_user_action", "blocked_dependency"})
        for tool, count in counts.items():
            if count > limit:
                errors.append(f"单工具恢复次数超过上限：{work_id}.{tool}={count}")
        first_rank_sequence: list[int] = []
        seen_tools: set[str] = set()
        for manifest in manifests:
            tool = manifest.get("tool")
            if tool in candidate_tools and tool not in seen_tools:
                first_rank_sequence.append(ranked_tools.index(tool))
                seen_tools.add(tool)
        if first_rank_sequence != sorted(first_rank_sequence):
            errors.append(f"工具没有按排名顺序降级：{work_id}")

        previous = None
        verified_tools = set()
        for manifest in manifests:
            tool = manifest.get("tool")
            if tool not in ranked_tools:
                continue
            rank = ranked_tools.index(tool)
            if len(verified_tools) >= (2 if item["cross_validation_required"] else 1):
                errors.append(f"原子任务验收完成后仍继续执行：{work_id}")
            if previous is None:
                if rank != 0:
                    errors.append(f"必须先执行主工具：{work_id}")
            else:
                previous_tool = previous.get("tool")
                prior_rank = ranked_tools.index(previous_tool) if previous_tool in ranked_tools else -1
                prior_status = previous.get("status")
                if rank not in {prior_rank, prior_rank + 1}:
                    errors.append(f"不得越级或倒退切换工具：{work_id}")
                if prior_status in {"awaiting_human", "blocked_user_action"}:
                    resume = manifest.get("resume", {})
                    if not isinstance(resume, dict) or tool != previous_tool or resume.get("previous_execution_id") != previous.get("execution_id") or resume.get("condition_resolved") is not True or not resume.get("note") or not evidence.timestamp(resume.get("verified_at")):
                        errors.append(f"人工待办未复检，不得继续或降级：{work_id}")
                if prior_status in ACCEPTED and rank == prior_rank:
                    errors.append(f"通过验收后不得重复执行同一工具：{work_id}")
            previous = manifest
            if manifest.get("status") in ACCEPTED and manifest.get("acceptance_passed") is True:
                verified_tools.add(tool)

        accepted_manifests = [manifest for manifest in manifests if manifest.get("status") in ACCEPTED and manifest.get("acceptance_passed") is True]
        accepted_by_work[work_id] = [manifest.get("execution_id") for manifest in accepted_manifests if isinstance(manifest.get("execution_id"), str)]
        accepted_tools = {manifest.get("tool") for manifest in accepted_manifests}
        cross_required = item.get("cross_validation_required") is True
        complete_by_work[work_id] = bool(accepted_tools) and (not cross_required or len(accepted_tools) >= 2)
        last_by_work[work_id] = manifests[-1].get("status", "failed") if manifests else "failed"
        if not cross_required:
            accepted_indexes = [index for index, manifest in enumerate(manifests) if manifest in accepted_manifests]
            if accepted_indexes and accepted_indexes[0] != len(manifests) - 1:
                errors.append(f"主结果通过验收后仍重复执行其他工具：{work_id}")

    try:
        summary = read_json(summary_path)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return errors + [str(error)]
    if summary.get("task_id") != task_id:
        errors.append("summary.task_id 与 task.json 不一致")
    if summary.get("target") != target:
        errors.append("summary.target 与 task.json 不一致")
    if summary.get("task_fingerprint") != plan["task_fingerprint"]:
        errors.append("summary 不属于当前任务版本")
    overall = summary.get("overall_status")
    if overall not in OVERALL_ALLOWED:
        errors.append(f"无效总体状态：{overall}")

    summary_items = summary.get("work_items")
    if not isinstance(summary_items, list):
        return errors + ["summary.work_items 必须是数组"]
    summary_by_id = {item.get("id"): item for item in summary_items if isinstance(item, dict)}
    if len(summary_by_id) != len(summary_items):
        errors.append("summary 原子任务重复或无效")
    if set(summary_by_id) != plan_work_ids:
        errors.append("summary 原子任务集合与 execution_plan 不一致")

    accepted_work_count = 0
    for work_id in plan_work_ids:
        item = summary_by_id.get(work_id, {})
        status = item.get("status")
        accepted_ids = item.get("accepted_execution_ids")
        if not isinstance(accepted_ids, list):
            errors.append(f"summary 缺少 accepted_execution_ids：{work_id}")
            continue
        expected_ids = accepted_by_work.get(work_id, [])
        if set(accepted_ids) != set(expected_ids):
            errors.append(f"summary 验收执行记录不一致：{work_id}")
        if len(accepted_ids) != len(set(accepted_ids)):
            errors.append(f"summary 验收执行记录重复：{work_id}")
        if status in ACCEPTED:
            accepted_work_count += 1
            if not complete_by_work.get(work_id):
                errors.append(f"原子任务缺少独立交叉核验：{work_id}")
            if not accepted_ids or item.get("evidence_present") is not True:
                errors.append(f"成功原子任务必须关联已验收证据：{work_id}")
            observed_statuses = {manifest_by_id[eid]["status"] for eid in expected_ids}
            if status not in observed_statuses or ("success" in observed_statuses and status == "empty_verified"):
                errors.append(f"原子任务状态与实际非空/零结果不一致：{work_id}")
            if len({manifest_by_id[eid]["tool"] for eid in expected_ids}) >= 2:
                review = item.get("cross_validation", {})
                if not isinstance(review, dict) or not all(isinstance(review.get(key), str) and review[key].strip() for key in ("method", "independence_basis", "conclusion")) or review.get("execution_ids") != expected_ids:
                    errors.append(f"缺少交叉核验依据和结论：{work_id}")
        elif complete_by_work.get(work_id):
            errors.append(f"原子任务已有通过验收的执行，summary 状态却未成功：{work_id}")
        elif status not in EXECUTION_ALLOWED:
            errors.append(f"无效原子任务状态：{work_id}={status}")
        elif status != last_by_work.get(work_id):
            errors.append(f"未完成状态必须对应最后一次执行：{work_id}")

    total_work_count = len(plan_work_ids)
    if accepted_work_count == total_work_count:
        if overall != "success":
            errors.append("所有原子任务通过验收时总体状态必须为 success")
        if summary.get("current_primary_evidence") is not True:
            errors.append("总体 success 必须明确 current_primary_evidence=true")
        ids = {row["id"] for manifest in manifest_by_id.values() if manifest.get("status") in ACCEPTED for row in manifest.get("result", {}).get("evidence", []) if isinstance(row, dict) and isinstance(row.get("id"), str)}
        errors.extend(evidence.assessments(summary.get("assessments"), task["success_criteria"], ids))
    elif accepted_work_count > 0:
        if overall != "partial_success":
            errors.append("只有部分原子任务通过验收时总体状态必须为 partial_success")
    elif overall in {"success", "partial_success"}:
        errors.append("没有原子任务通过验收时总体状态不得为 success 或 partial_success")
    elif overall not in set(last_by_work.values()) | ({"failed"} if any(s in {"unassessed", "partial_success"} for s in last_by_work.values()) else set()):
        errors.append("总体阻塞状态与执行记录不一致")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--summary", required=True, type=Path)
    parser.add_argument("--max-attempts-per-tool", type=int, help="只允许收紧默认的首次执行加两次恢复")
    args = parser.parse_args()
    try:
        errors = validate(args.run_dir, args.summary, args.max_attempts_per_tool)
    except (ValueError, TypeError, KeyError, OSError) as error:
        errors = [f"无效运行记录：{error}"]
    print(json.dumps({"ok": not errors, "errors": errors}, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
