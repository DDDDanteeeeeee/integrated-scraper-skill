"""Adversarial fixtures: structural success must not disguise missing deliverables."""
import json
import hashlib
from pathlib import Path
import tempfile
import unittest
import test_scripts as fixtures
from test_scripts import validator, planner, atomic_task, pack_doctor, ROOT


class AcceptanceRegressionTests(unittest.TestCase):
    def test_collection_check_recomputed_not_trusted(self):
        self.make()
        source = self.root / 'work-items/W1/executions/01-scrapling/source.txt'
        check = {'records': [], 'page_state': 'content_ready', 'displayed_count': 2,
                 'count_unit': 'all_comment_nodes', 'ok': True}
        source.write_text(json.dumps(check), encoding='utf-8')
        def bind(m):
            m['result']['evidence'][0]['sha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
            m['result']['collection_check'] = {'evidence_id': m['result']['evidence'][0]['id']}
        self.edit(self.manifest(), bind)
        self.assertTrue(self.validate())
        check['displayed_count'] = 0
        source.write_text(json.dumps(check), encoding='utf-8')
        self.edit(self.manifest(), bind)
        self.assertEqual(self.validate(), [])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def make(self, attempts=None, **kwargs):
        return fixtures.ValidatorTests().make_run(self.root, attempts, **kwargs)

    def edit(self, relative, change):
        path = self.root / relative
        data = json.loads(path.read_text(encoding="utf-8"))
        change(data)
        path.write_text(json.dumps(data), encoding="utf-8")

    def validate(self):
        return validator.validate(self.root, self.root / "summary.json")

    def manifest(self, index=1, tool="scrapling"):
        return f"work-items/W1/executions/{index:02d}-{tool}/execution_manifest.json"

    def test_missing_evidence_is_rejected(self):
        self.make()
        self.edit(self.manifest(), lambda m: m["result"].pop("evidence"))
        self.assertTrue(self.validate())

    def test_nonempty_cannot_be_reported_as_empty(self):
        self.make()
        self.edit("summary.json", lambda s: s["work_items"][0].update(status="empty_verified"))
        self.assertTrue(self.validate())

    def test_rebuilt_plan_does_not_reuse_old_execution(self):
        self.make()
        self.edit("task.json", lambda t: t.update(objective="Changed objective"))
        task = planner.read_json(self.root / "task.json")
        plan = planner.build_plan(task, planner.read_json(ROOT / "runtime.contract.json"))
        (self.root / "execution_plan.json").write_text(json.dumps(plan), encoding="utf-8")
        self.assertTrue(self.validate())

    def test_modified_evidence_is_rejected(self):
        self.make()
        (self.root / "work-items/W1/executions/01-scrapling/source.txt").write_text("changed")
        self.assertTrue(self.validate())

    def test_missing_file_is_rejected(self):
        self.make()
        self.edit(self.manifest(), lambda m: m["result"]["evidence"][0].update(path="missing.txt"))
        self.assertTrue(self.validate())

    def test_path_escape_is_rejected(self):
        self.make()
        self.edit(self.manifest(), lambda m: m["result"]["evidence"][0].update(path="../outside.txt"))
        self.assertTrue(self.validate())

    def test_unknown_criterion_evidence_is_rejected(self):
        self.make()
        self.edit(self.manifest(), lambda m: m["result"]["assessments"][0].update(evidence_ids=["unknown"]))
        self.assertTrue(self.validate())

    def test_skipped_primary_is_rejected(self):
        self.assertTrue(self.make([("opencli", "success")]))

    def test_auth_cannot_fall_back(self):
        self.assertTrue(self.make([("scrapling", "awaiting_human"), ("opencli", "success")]))

    def test_rank_cannot_go_back(self):
        self.assertTrue(self.make([("scrapling", "failed"), ("opencli", "failed"), ("scrapling", "success")]))

    def test_changed_task_is_rejected(self):
        self.make()
        self.edit("task.json", lambda t: t.update(objective="Different requirement"))
        self.assertTrue(self.validate())

    def test_changed_plan_risk_is_rejected(self):
        self.make()
        self.edit("execution_plan.json", lambda p: p["work_items"][0].update(cross_validation_required=True))
        self.assertTrue(self.validate())

    def test_human_pause_is_valid_unfinished_state(self):
        self.assertEqual(self.make([("scrapling", "awaiting_human")], overall="awaiting_human", work_status="awaiting_human"), [])

    def test_human_resume_requires_same_tool_and_recheck(self):
        self.assertTrue(self.make([("scrapling", "awaiting_human"), ("scrapling", "success")]))
        self.edit(self.manifest(2), lambda m: m.update(resume={"previous_execution_id": "W1-01-scrapling", "condition_resolved": True, "verified_at": "2026-07-27T00:01:00+08:00", "note": "same profile verified"}))
        self.assertEqual(self.validate(), [])

    def test_cross_check_pause_can_be_reported_honestly(self):
        self.assertEqual(self.make([("scrapling", "success"), ("opencli", "awaiting_human")], cross_validation=True, overall="awaiting_human", work_status="awaiting_human"), [])

    def test_recovery_limit_cannot_be_relaxed(self):
        self.make()
        self.assertTrue(validator.validate(self.root, self.root / "summary.json", 100))

    def test_fallback_scope_drops_failed_primary_keeps_auxiliary(self):
        contract = planner.read_json(ROOT / "runtime.contract.json")
        task = atomic_task()
        task["work_items"][0]["candidates"][1]["extra_dependencies"] = ["yt-dlp"]
        plan = planner.build_plan(task, contract)
        self.assertEqual(pack_doctor.selected_requirements(plan, contract, "W1", "opencli"), {"opencli", "yt-dlp"})

    def test_unsafe_work_id_is_rejected(self):
        task = atomic_task()
        task["work_items"][0]["id"] = "../outside"
        with self.assertRaises(ValueError):
            planner.build_plan(task, planner.read_json(ROOT / "runtime.contract.json"))


if __name__ == "__main__":
    unittest.main()
