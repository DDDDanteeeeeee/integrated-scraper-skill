from __future__ import annotations

import importlib.util
import json
import hashlib
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / ".agents" / "skills" / "integrated-scraper"


def load_module(name: str, relative_path: str):
    spec = importlib.util.spec_from_file_location(name, SKILL_ROOT / relative_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载 {relative_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


doctor = load_module("doctor", "scripts/doctor.py")
validator = load_module("validator", "scripts/validate_run.py")
initializer = load_module("initializer", "scripts/initialize.py")
pack_doctor = load_module("pack_doctor", "scripts/pack_doctor.py")
planner = load_module("planner", "scripts/plan_run.py")


def fixed_config() -> dict:
    return initializer.build_config(
        opencli_command="opencli",
        browser_harness_command="browser-harness",
    )


class DoctorTests(unittest.TestCase):
    def test_contract_path_alias_is_normalized(self):
        config = fixed_config()
        config["runtime_contract"] = str(ROOT / "config" / ".." / "runtime.contract.json")
        self.assertIsNone(doctor.fixed_runtime_error(config))

    def test_other_contract_path_still_rejected(self):
        config = fixed_config()
        config["runtime_contract"] = str(ROOT / "other-runtime.contract.json")
        self.assertEqual(doctor.fixed_runtime_error(config), "runtime_contract 路径不匹配")

    def test_rejects_sensitive_local_config(self):
        result = doctor.check({"opencli": {"session": "forbidden"}})
        self.assertEqual(result["status"], "invalid_config")

    def test_example_placeholders_are_not_ready(self):
        config = fixed_config()
        config["opencli"]["command"] = "replace-with-local-command"
        config["scrapling"]["executable"] = "replace-with-local-command"
        result = doctor.check(config)
        self.assertFalse(result["checks"]["opencli"]["ready"])
        self.assertFalse(result["checks"]["scrapling"]["ready"])

    def test_rejects_qishui_port(self):
        config = fixed_config()
        config["browser_harness"]["cdp_url"] = "http://127.0.0.1:9223"
        config["browser_harness"]["remote_debugging_port"] = 9223
        result = doctor.check(config)
        self.assertEqual(result["status"], "invalid_config")
        self.assertIn("9222", result["error"])

    def test_rejects_non_loopback_cdp_endpoint(self):
        ready, detail = doctor.probe_cdp("https://example.com")
        self.assertFalse(ready)
        self.assertIn("本机", detail)


def candidate(tool: str, score: int, *, extra_dependencies: list[str] | None = None) -> dict:
    return {
        "tool": tool,
        "reason": f"{tool} 可以满足本项验收",
        "hard_gates": {
            "capability_fit": True,
            "authorization_allowed": True,
            "can_meet_acceptance": True,
            "runtime_possible": True,
        },
        "scores": {
            "success_probability": score,
            "data_quality": score,
            "direct_usability": score,
            "browser_login_fit": score,
            "cost_efficiency": score,
            "runtime_readiness": score,
            "permission_risk_fit": score,
            "historical_performance": score,
        },
        "extra_dependencies": extra_dependencies or [],
    }


def atomic_task(*, cross_validation: bool = False, candidate_tools: list[tuple[str, int]] | None = None) -> dict:
    contract = json.loads((ROOT / "runtime.contract.json").read_text(encoding="utf-8"))
    choices = candidate_tools or [("scrapling", 5), ("opencli", 4)]
    chosen = {tool for tool, _ in choices}
    excluded = [
        {"tool": tool, "reason": "本项不需要该工具的能力"}
        for tool in contract["tool_routing"]["tools"]
        if tool not in chosen
    ]
    return {
        "task_id": "20260727-camping-projector",
        "target": "露营投影仪",
        "objective": "提取真实用户需求和产品机会",
        "time_range": "最近 30 天",
        "decision_context": "新品策划团队",
        "success_criteria": ["每条结论附公开来源"],
        "work_items": [
            {
                "id": "W1",
                "requirement": "提取公开页面中的真实使用需求",
                "acceptance_criteria": ["至少取得一条可回溯的公开证据，或明确证明为零条"],
                "risk_level": "high" if cross_validation else "normal",
                "cross_validation_required": cross_validation,
                "candidates": [candidate(tool, score) for tool, score in choices],
                "excluded_tools": excluded,
            }
        ],
    }


class PlanRunTests(unittest.TestCase):
    def contract(self) -> dict:
        return json.loads((ROOT / "runtime.contract.json").read_text(encoding="utf-8"))

    def test_selects_only_highest_scoring_primary_by_default(self):
        plan = planner.build_plan(atomic_task(), self.contract())
        item = plan["work_items"][0]
        self.assertEqual(item["primary_tool"], "scrapling")
        self.assertEqual(item["fallback_tools"], ["opencli"])
        self.assertEqual(plan["required_tools"], ["scrapling"])
        self.assertEqual(plan["required_dependencies"], ["scrapling"])

    def test_only_executable_tool_is_selected_even_when_not_ready(self):
        task = atomic_task(candidate_tools=[("scrapling", 0)])
        plan = planner.build_plan(task, self.contract())
        self.assertEqual(plan["work_items"][0]["primary_tool"], "scrapling")

    def test_rejects_silent_tool_omission(self):
        task = atomic_task()
        task["work_items"][0]["excluded_tools"].pop()
        with self.assertRaisesRegex(ValueError, "未评估全部工具"):
            planner.build_plan(task, self.contract())

    def test_high_risk_item_requires_independent_candidate(self):
        task = atomic_task(cross_validation=True, candidate_tools=[("scrapling", 5)])
        with self.assertRaisesRegex(ValueError, "可执行工具不足两个"):
            planner.build_plan(task, self.contract())


class ValidatorTests(unittest.TestCase):
    def make_run(
        self,
        root: Path,
        attempts: list[tuple[str, str]] | None = None,
        *,
        overall: str = "success",
        work_status: str = "success",
        cross_validation: bool = False,
    ) -> list[str]:
        task = atomic_task(cross_validation=cross_validation)
        (root / "task.json").write_text(json.dumps(task, ensure_ascii=False), encoding="utf-8")
        contract = json.loads((ROOT / "runtime.contract.json").read_text(encoding="utf-8"))
        plan = planner.build_plan(task, contract)
        (root / "execution_plan.json").write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")
        attempts = attempts or [("scrapling", "success")]
        accepted_ids: list[str] = []
        all_evidence_ids: list[str] = []
        for index, (tool, status) in enumerate(attempts, start=1):
            execution_id = f"W1-{index:02d}-{tool}"
            path = root / "work-items" / "W1" / "executions" / f"{index:02d}-{tool}"
            path.mkdir(parents=True)
            accepted = status in validator.ACCEPTED
            result = {"evidence_count": 1} if status == "success" else {}
            if status == "empty_verified":
                result = {"empty_verified": True, "empty_evidence": ["页面明确显示 0 条"]}
            if accepted:
                accepted_ids.append(execution_id)
                evidence_id = execution_id + "-source"
                all_evidence_ids.append(evidence_id)
                raw = path / "source.txt"
                raw.write_text("Synthetic test fixture: visible result", encoding="utf-8")
                result["evidence"] = [{"id": evidence_id, "url": "https://example.com/test", "captured_at": "2026-07-27T00:00:00+08:00", "path": raw.relative_to(root).as_posix(), "sha256": hashlib.sha256(raw.read_bytes()).hexdigest()}]
                result["assessments"] = [{"criterion": criterion, "passed": True, "reason": "Synthetic fixture only", "evidence_ids": [evidence_id]} for criterion in task["work_items"][0]["acceptance_criteria"]]
                if status == "empty_verified":
                    result["empty_evidence"] = [evidence_id]
            (path / "execution_manifest.json").write_text(
                json.dumps(
                    {
                        "execution_id": execution_id,
                        "task_fingerprint": plan["task_fingerprint"],
                        "attempt_index": index,
                        "work_item_id": "W1",
                        "tool": tool,
                        "task_id": task["task_id"],
                        "status": status,
                        "timestamp": "2026-07-27T00:00:00+08:00",
                        "target": task["target"],
                        "acceptance_passed": accepted,
                        "result": result,
                        **({"recovery_condition": "修复后按排名继续"} if not accepted else {}),
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
        summary = root / "summary.json"
        summary.write_text(
            json.dumps(
                {
                    "task_id": task["task_id"],
                    "target": task["target"],
                    "overall_status": overall,
                    "task_fingerprint": plan["task_fingerprint"],
                    "current_primary_evidence": overall == "success",
                    "assessments": [{"criterion": criterion, "passed": True, "reason": "Synthetic fixture only", "evidence_ids": all_evidence_ids} for criterion in task["success_criteria"]],
                    "work_items": [
                        {
                            "id": "W1",
                            "status": work_status,
                            "accepted_execution_ids": accepted_ids,
                            "evidence_present": bool(accepted_ids),
                            "cross_validation": {"method": "fixture comparison", "independence_basis": "separate fixture observations", "conclusion": "fixtures agree", "execution_ids": accepted_ids},
                        }
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return validator.validate(root, summary)

    def test_accepts_complete_truthful_run(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(self.make_run(Path(directory)), [])

    def test_accepts_primary_failure_when_ranked_fallback_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            errors = self.make_run(Path(directory), [("scrapling", "failed"), ("opencli", "success")])
        self.assertEqual(errors, [])

    def test_rejects_duplicate_tool_after_result_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            errors = self.make_run(Path(directory), [("scrapling", "success"), ("opencli", "success")])
        self.assertIn("主结果通过验收后仍重复执行其他工具：W1", errors)

    def test_rejects_cross_task_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_run(root)
            path = root / "work-items" / "W1" / "executions" / "01-scrapling" / "execution_manifest.json"
            manifest = json.loads(path.read_text(encoding="utf-8"))
            manifest["task_id"] = "another-task"
            path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
            errors = validator.validate(root, root / "summary.json")
        self.assertIn("任务 ID 不一致：W1-01-scrapling", errors)

    def test_accepts_verified_empty_result(self):
        with tempfile.TemporaryDirectory() as directory:
            errors = self.make_run(Path(directory), [("scrapling", "empty_verified")], work_status="empty_verified")
        self.assertEqual(errors, [])

    def test_high_risk_item_requires_two_accepted_tools(self):
        with tempfile.TemporaryDirectory() as directory:
            errors = self.make_run(Path(directory), [("scrapling", "success")], cross_validation=True)
        self.assertIn("原子任务缺少独立交叉核验：W1", errors)

    def test_accepts_high_risk_item_with_independent_verification(self):
        with tempfile.TemporaryDirectory() as directory:
            errors = self.make_run(
                Path(directory),
                [("scrapling", "success"), ("opencli", "success")],
                cross_validation=True,
            )
        self.assertEqual(errors, [])


class InitializerTests(unittest.TestCase):
    def test_initialization_accepts_local_chrome_path(self):
        with tempfile.TemporaryDirectory(prefix="local chrome ") as directory:
            chrome = Path(directory) / "chrome.exe"
            chrome.write_bytes(b"fixture, not executed")
            config = initializer.build_config(chrome_executable=str(chrome))
            self.assertEqual(config["browser_harness"]["chrome_executable"], str(chrome))
            self.assertEqual(config["browser_harness"]["remote_debugging_port"], 9222)

    def test_initialization_rejects_missing_chrome(self):
        with self.assertRaises(ValueError):
            initializer.build_config(chrome_executable="missing/chrome.exe")

    def test_rejects_nonfixed_profile(self):
        with self.assertRaises(ValueError):
            initializer.build_config(opencli_profile="collection-work")

    def test_builds_non_secret_local_config(self):
        config = initializer.build_config()
        self.assertEqual(config["opencli"]["profile"], "integrated-scraper-9222")
        self.assertEqual(config["browser_harness"]["remote_debugging_port"], 9222)
        self.assertEqual(config["output_root"], r"D:\integrated-scraper-output")
        self.assertIsNone(doctor.contains_sensitive_key(config))

    def test_never_overwrites_existing_config(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "collection.local.json"
            path.write_text("{}", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                initializer.write_config(path, initializer.build_config())

    def test_rejects_external_config_target(self):
        self.assertFalse(initializer.is_project_config_path(Path("C:/outside/collection.local.json")))


class DependencyManifestTests(unittest.TestCase):
    def load_manifest(self):
        manifest_path = ROOT / "dependencies.manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["manifest_type"], "installation-manifest")
        return manifest

    def test_lists_all_execution_dependencies_with_resolution_data(self):
        manifest = self.load_manifest()
        ids = [item["id"] for item in manifest["dependencies"]]
        self.assertEqual(ids, ["opencli", "browser-harness", "last30days", "last30days-cn", "scrapling", "playwright", "yt-dlp", "cloakbrowser"])
        self.assertTrue(all(item["confirmation_required_before_install"] for item in manifest["dependencies"]))
        self.assertTrue(all("version_policy" in item and "installation" in item for item in manifest["dependencies"]))


class PackDoctorTests(unittest.TestCase):
    def config(self):
        return fixed_config()

    @staticmethod
    def successful_smoke(_command, _arguments, expected):
        return True, expected

    @staticmethod
    def connected_profile(_command, profile, expected):
        return True, f"{profile} connected v{expected}"

    def roots_with_skills(self, root: Path, missing: str | None = None):
        for skill_id in pack_doctor.SKILL_IDS:
            if skill_id == missing:
                continue
            path = root / skill_id
            path.mkdir(parents=True)
            (path / "SKILL.md").write_text("---\nname: test\ndescription: test\n---\n", encoding="utf-8")
        return [root]

    def test_plan_requirements_reject_tampered_dependency_scope(self):
        contract = json.loads((ROOT / "runtime.contract.json").read_text(encoding="utf-8"))
        plan = planner.build_plan(atomic_task(), contract)
        plan["required_dependencies"] = ["opencli"]
        with self.assertRaisesRegex(ValueError, "已选工具不一致"):
            pack_doctor.plan_requirements(plan, contract)

    def test_requires_every_non_conditional_dependency(self):
        manifest = DependencyManifestTests().load_manifest()
        with tempfile.TemporaryDirectory() as directory:
            result = pack_doctor.check_pack(
                self.config(),
                manifest,
                self.roots_with_skills(Path(directory), missing="last30days"),
                command_checker=lambda _: True,
                cdp_probe=lambda _: (True, "Chrome"),
                smoke_checker=self.successful_smoke,
                profile_checker=self.connected_profile,
                chrome_owner_checker=lambda: (True, "owned"),
                version_reader=lambda _: "3.3.2",
            )
        self.assertEqual(result["status"], "blocked_dependency")
        self.assertEqual(result["checks"]["last30days"]["status"], "blocked_dependency")
        self.assertEqual(result["resolution"]["last30days"]["installation"], "npx skills add mvanhorn/last30days-skill -g")

    def test_browser_authorization_is_awaiting_human(self):
        manifest = DependencyManifestTests().load_manifest()
        with tempfile.TemporaryDirectory() as directory:
            result = pack_doctor.check_pack(
                self.config(),
                manifest,
                self.roots_with_skills(Path(directory)),
                command_checker=lambda _: True,
                cdp_probe=lambda _: (False, "需要 CDP 授权"),
                smoke_checker=self.successful_smoke,
                profile_checker=self.connected_profile,
                chrome_owner_checker=lambda: (True, "owned"),
                version_reader=lambda path: "3.3.2" if path.parent.name == "last30days" else "3.0.0-cn",
            )
        self.assertEqual(result["status"], "awaiting_human")
        self.assertEqual(result["checks"]["browser-harness"]["status"], "awaiting_human")

    def test_unselected_dependency_does_not_block_task_plan(self):
        manifest = DependencyManifestTests().load_manifest()
        with tempfile.TemporaryDirectory() as directory:
            result = pack_doctor.check_pack(
                self.config(),
                manifest,
                self.roots_with_skills(Path(directory), missing="last30days"),
                command_checker=lambda _: True,
                cdp_probe=lambda _: (False, "项目 Chrome 未运行"),
                smoke_checker=self.successful_smoke,
                profile_checker=lambda *_: (False, "固定 Profile 未连接"),
                chrome_owner_checker=lambda: (False, "项目 Chrome 未运行"),
                version_reader=lambda path: "3.3.2" if path and path.parent.name == "last30days" else "3.0.0-cn",
                required_dependencies={"scrapling"},
            )
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["scope"], "task_plan")
        self.assertEqual(result["required_dependencies"], ["scrapling"])
        self.assertEqual(result["checks"]["last30days"]["status"], "not_checked")
        self.assertEqual(result["checks"]["browser-harness"]["status"], "not_checked")

    def test_selected_dependency_still_blocks_task_plan(self):
        manifest = DependencyManifestTests().load_manifest()
        with tempfile.TemporaryDirectory() as directory:
            result = pack_doctor.check_pack(
                self.config(),
                manifest,
                self.roots_with_skills(Path(directory), missing="last30days"),
                command_checker=lambda _: True,
                cdp_probe=lambda _: (True, "Chrome"),
                smoke_checker=self.successful_smoke,
                profile_checker=self.connected_profile,
                chrome_owner_checker=lambda: (True, "owned"),
                version_reader=lambda path: "3.3.2" if path and path.parent.name == "last30days" else "3.0.0-cn",
                required_dependencies={"last30days"},
            )
        self.assertEqual(result["status"], "blocked_dependency")

    def test_reports_success_only_when_all_required_dependencies_are_ready(self):
        manifest = DependencyManifestTests().load_manifest()
        with tempfile.TemporaryDirectory() as directory:
            result = pack_doctor.check_pack(
                self.config(),
                manifest,
                self.roots_with_skills(Path(directory)),
                command_checker=lambda _: True,
                cdp_probe=lambda _: (True, "Chrome"),
                smoke_checker=self.successful_smoke,
                profile_checker=self.connected_profile,
                chrome_owner_checker=lambda: (True, "owned"),
                version_reader=lambda path: "3.3.2" if path.parent.name == "last30days" else "3.0.0-cn",
            )
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["checks"]["cloakbrowser"]["status"], "compliant_skip")

    def test_missing_fixed_opencli_profile_is_awaiting_human(self):
        manifest = DependencyManifestTests().load_manifest()
        with tempfile.TemporaryDirectory() as directory:
            result = pack_doctor.check_pack(
                self.config(),
                manifest,
                self.roots_with_skills(Path(directory)),
                command_checker=lambda _: True,
                cdp_probe=lambda _: (True, "Chrome"),
                smoke_checker=self.successful_smoke,
                profile_checker=lambda *_: (False, "固定 Profile 未连接"),
                chrome_owner_checker=lambda: (True, "owned"),
                version_reader=lambda path: "3.3.2" if path.parent.name == "last30days" else "3.0.0-cn",
            )
        self.assertEqual(result["status"], "awaiting_human")
        self.assertEqual(result["checks"]["opencli"]["status"], "awaiting_human")


if __name__ == "__main__":
    unittest.main()
