#!/usr/bin/env python3
"""Build and validate an atomic, best-tool execution plan for a scraper task."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import hashlib
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[4]
RUNTIME_CONTRACT_PATH = PROJECT_ROOT / "runtime.contract.json"
REQUIRED_TASK_FIELDS = (
    "task_id",
    "target",
    "objective",
    "time_range",
    "decision_context",
    "success_criteria",
    "work_items",
)
REQUIRED_WORK_ITEM_FIELDS = (
    "id",
    "requirement",
    "acceptance_criteria",
    "risk_level",
    "cross_validation_required",
    "candidates",
    "excluded_tools",
)
HARD_GATES = (
    "capability_fit",
    "authorization_allowed",
    "can_meet_acceptance",
    "runtime_possible",
)


def fingerprint(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode("utf-8")).hexdigest()


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} 必须是 JSON 对象")
    return value


def _nonempty_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _nonempty_text_list(value: object) -> bool:
    return isinstance(value, list) and bool(value) and all(_nonempty_text(item) for item in value)


def validate_task(task: dict, contract: dict) -> list[str]:
    errors: list[str] = []
    for field in REQUIRED_TASK_FIELDS:
        if field not in task:
            errors.append(f"缺少任务字段：{field}")
    if errors:
        return errors
    if not _nonempty_text_list(task.get("success_criteria")):
        errors.append("success_criteria 必须是非空字符串数组")
    work_items = task.get("work_items")
    if not isinstance(work_items, list) or not work_items:
        errors.append("work_items 必须是非空数组")
        return errors

    routing = contract.get("tool_routing", {})
    tools = routing.get("tools", {})
    weights = routing.get("weights", {})
    score_scale = routing.get("score_scale", {})
    registered_tools = set(tools)
    allowed_dependencies = set(routing.get("allowed_dependencies", []))
    score_min = score_scale.get("min", 0)
    score_max = score_scale.get("max", 5)
    if not registered_tools or not weights or sum(weights.values()) != 100:
        return errors + ["runtime.contract.json 的 tool_routing 不完整或权重之和不是 100"]

    seen_ids: set[str] = set()
    for index, item in enumerate(work_items):
        label = f"work_items[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{label} 必须是对象")
            continue
        for field in REQUIRED_WORK_ITEM_FIELDS:
            if field not in item:
                errors.append(f"{label} 缺少字段：{field}")
        work_id = item.get("id")
        if not _nonempty_text(work_id) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", work_id):
            errors.append(f"{label}.id 必须是非空字符串")
        elif work_id in seen_ids:
            errors.append(f"原子任务 ID 重复：{work_id}")
        else:
            seen_ids.add(work_id)
        if not _nonempty_text(item.get("requirement")):
            errors.append(f"{label}.requirement 必须是非空字符串")
        if not _nonempty_text_list(item.get("acceptance_criteria")):
            errors.append(f"{label}.acceptance_criteria 必须是非空字符串数组")
        if item.get("risk_level") not in {"normal", "high"}:
            errors.append(f"{label}.risk_level 只能是 normal 或 high")
        if not isinstance(item.get("cross_validation_required"), bool):
            errors.append(f"{label}.cross_validation_required 必须是布尔值")
        if item.get("risk_level") == "high" and item.get("cross_validation_required") is not True:
            errors.append(f"{label} 是高风险结论，必须交叉核验")

        candidates = item.get("candidates")
        excluded = item.get("excluded_tools")
        if not isinstance(candidates, list) or not candidates:
            errors.append(f"{label}.candidates 必须至少包含一个工具")
            candidates = []
        if not isinstance(excluded, list):
            errors.append(f"{label}.excluded_tools 必须是数组")
            excluded = []

        candidate_tools: list[str] = []
        for candidate_index, candidate in enumerate(candidates):
            candidate_label = f"{label}.candidates[{candidate_index}]"
            if not isinstance(candidate, dict):
                errors.append(f"{candidate_label} 必须是对象")
                continue
            tool = candidate.get("tool")
            if tool not in registered_tools:
                errors.append(f"{candidate_label}.tool 未登记：{tool}")
                continue
            candidate_tools.append(tool)
            if not _nonempty_text(candidate.get("reason")):
                errors.append(f"{candidate_label}.reason 必须说明为什么可执行")
            gates = candidate.get("hard_gates")
            if not isinstance(gates, dict) or any(gates.get(name) is not True for name in HARD_GATES):
                errors.append(f"{candidate_label}.hard_gates 必须全部通过；未通过的工具应放入 excluded_tools")
            scores = candidate.get("scores")
            if not isinstance(scores, dict) or set(scores) != set(weights):
                errors.append(f"{candidate_label}.scores 必须完整包含：{', '.join(weights)}")
            else:
                for name, score in scores.items():
                    if not isinstance(score, (int, float)) or isinstance(score, bool) or not score_min <= score <= score_max:
                        errors.append(f"{candidate_label}.scores.{name} 必须在 {score_min} 到 {score_max} 之间")
            extra_dependencies = candidate.get("extra_dependencies", [])
            if not isinstance(extra_dependencies, list) or any(dep not in allowed_dependencies for dep in extra_dependencies):
                errors.append(f"{candidate_label}.extra_dependencies 包含未登记依赖")

        excluded_tools: list[str] = []
        for excluded_index, entry in enumerate(excluded):
            excluded_label = f"{label}.excluded_tools[{excluded_index}]"
            if not isinstance(entry, dict) or entry.get("tool") not in registered_tools:
                errors.append(f"{excluded_label}.tool 未登记")
                continue
            excluded_tools.append(entry["tool"])
            if not _nonempty_text(entry.get("reason")):
                errors.append(f"{excluded_label}.reason 必须说明排除原因")

        accounted = candidate_tools + excluded_tools
        if len(accounted) != len(set(accounted)):
            errors.append(f"{label} 的工具在候选或排除列表中重复")
        missing_tools = registered_tools - set(accounted)
        if missing_tools:
            errors.append(f"{label} 未评估全部工具：{', '.join(sorted(missing_tools))}")
        if item.get("cross_validation_required") is True and len(candidate_tools) < 2:
            errors.append(f"{label} 要求交叉核验，但可执行工具不足两个")
    return errors


def _score(candidate: dict, weights: dict[str, int], score_max: int) -> float:
    return round(sum(float(candidate["scores"][name]) / score_max * weight for name, weight in weights.items()), 2)


def build_plan(task: dict, contract: dict) -> dict:
    errors = validate_task(task, contract)
    if errors:
        raise ValueError("；".join(errors))

    routing = contract["tool_routing"]
    weights = routing["weights"]
    score_max = routing["score_scale"]["max"]
    registry = routing["tools"]
    required_tools: set[str] = set()
    required_dependencies: set[str] = set()
    planned_items: list[dict] = []

    for item in task["work_items"]:
        ranked = []
        for candidate in item["candidates"]:
            enriched = dict(candidate)
            enriched["weighted_score"] = _score(candidate, weights, score_max)
            ranked.append(enriched)
        ranked.sort(key=lambda candidate: (-candidate["weighted_score"], candidate["tool"]))
        for rank, candidate in enumerate(ranked, start=1):
            candidate["rank"] = rank

        primary = ranked[0]["tool"]
        fallbacks = [candidate["tool"] for candidate in ranked[1:]]
        verification_tools = [ranked[1]["tool"]] if item["cross_validation_required"] else []
        active_tools = [primary, *verification_tools]
        required_tools.update(active_tools)
        for candidate in ranked:
            if candidate["tool"] not in active_tools:
                continue
            required_dependencies.update(registry[candidate["tool"]]["base_dependencies"])
            required_dependencies.update(candidate.get("extra_dependencies", []))

        planned_items.append(
            {
                "id": item["id"],
                "requirement": item["requirement"],
                "acceptance_criteria": item["acceptance_criteria"],
                "risk_level": item["risk_level"],
                "cross_validation_required": item["cross_validation_required"],
                "candidates": ranked,
                "excluded_tools": item["excluded_tools"],
                "primary_tool": primary,
                "fallback_tools": fallbacks,
                "verification_tools": verification_tools,
            }
        )

    return {
        "schema_version": 1,
        "task_fingerprint": fingerprint(task),
        "contract_fingerprint": fingerprint(contract),
        "routing_policy": contract["execution"]["routing_mode"],
        "task_id": task["task_id"],
        "target": task["target"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "required_tools": sorted(required_tools),
        "required_dependencies": sorted(required_dependencies),
        "work_items": planned_items,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", required=True, type=Path)
    parser.add_argument("--contract", type=Path, default=RUNTIME_CONTRACT_PATH)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        task = read_json(args.task)
        contract = read_json(args.contract)
        plan = build_plan(task, contract)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(json.dumps({"ok": False, "errors": [str(error)]}, ensure_ascii=False))
        return 1
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "plan": plan}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
