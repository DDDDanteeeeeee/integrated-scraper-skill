from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents" / "skills" / "integrated-scraper" / "SKILL.md"
OPENAI_YAML = ROOT / ".agents" / "skills" / "integrated-scraper" / "agents" / "openai.yaml"


class MetadataTests(unittest.TestCase):
    def test_skill_metadata_is_explicit_and_project_local(self):
        text = SKILL.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\nname: integrated-scraper\n"))
        self.assertIn("dependencies.manifest.json", text)
        self.assertIn("pack_doctor.py", text)
        self.assertIn("不固定\n来源、平台", text)
        self.assertIn("路由规则", text)
        self.assertIn("每个已登记工具必须出现在候选或排除列表中", text)
        self.assertIn("主工具通过验收后停止", text)
        self.assertIn("原始证据、URL、状态", text)
        self.assertIn("empty_verified", text)
        self.assertIn("不能\n单独证明评论为零", text)
        self.assertFalse((ROOT / ".agents" / "skills" / "magewell-douyin-intelligence").exists())
        self.assertFalse((ROOT / ".agents" / "skills" / "douyin-intelligence").exists())

    def test_skill_frontmatter_matches_official_constraints(self):
        text = SKILL.read_text(encoding="utf-8")
        match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
        self.assertIsNotNone(match)
        fields = dict(line.split(": ", 1) for line in match.group(1).splitlines())
        self.assertEqual(set(fields), {"name", "description"})
        self.assertRegex(fields["name"], r"^[a-z0-9-]+$")
        self.assertLessEqual(len(fields["name"]), 64)
        self.assertLessEqual(len(fields["description"]), 1024)
        self.assertNotRegex(fields["description"], r"[<>]")
        self.assertNotIn("Magewell", fields["description"])
        self.assertNotIn("抖音", fields["description"])

    def test_manifest_replaces_misleading_lock_file(self):
        self.assertFalse((ROOT / "dependencies.lock.json").exists())
        manifest = json.loads((ROOT / "dependencies.manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["manifest_type"], "installation-manifest")
        self.assertEqual(manifest["pack_id"], "integrated-scraper")

    def test_runtime_contract_locks_project_ports(self):
        contract = json.loads((ROOT / "runtime.contract.json").read_text(encoding="utf-8"))
        self.assertEqual(contract["browser"]["remote_debugging_port"], 9222)
        self.assertEqual(contract["browser"]["cdp_url"], "http://127.0.0.1:9222")
        self.assertIn(9223, contract["browser"]["forbidden_ports"])
        self.assertEqual(contract["opencli"]["profile"], "integrated-scraper-9222")
        self.assertEqual(contract["opencli"]["daemon_port"], 19825)
        self.assertEqual(contract["cloakbrowser"]["remote_debugging_port"], 9242)
        self.assertEqual(contract["execution"]["routing_mode"], "atomic-best-tool")
        self.assertFalse(contract["execution"]["default_duplicate_execution"])
        self.assertNotIn("rounds", contract["execution"])
        self.assertEqual(sum(contract["tool_routing"]["weights"].values()), 100)
        self.assertEqual(
            set(contract["tool_routing"]["tools"]),
            {"scrapling", "opencli", "browser-harness", "last30days", "last30days-cn", "cloakbrowser"},
        )

    def test_fixed_runtime_entrypoints_exist(self):
        scripts = ROOT / ".agents" / "skills" / "integrated-scraper" / "scripts"
        for name in (
            "set_runtime_env.ps1",
            "start_project_chrome.ps1",
            "start_runtime.ps1",
            "invoke_opencli.ps1",
            "invoke_browser_harness.ps1",
            "invoke_project_python.ps1",
            "plan_run.py",
        ):
            self.assertTrue((scripts / name).is_file(), name)

    def test_explicit_invocation_stays_enabled(self):
        text = OPENAI_YAML.read_text(encoding="utf-8")
        self.assertIn('display_name: "综合抓取"', text)
        self.assertIn("$integrated-scraper", text)
        self.assertNotIn("Magewell", text)
        self.assertNotIn("Douyin", text)
        self.assertIn("allow_implicit_invocation: false", text)


if __name__ == "__main__":
    unittest.main()
