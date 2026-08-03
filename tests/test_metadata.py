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
        self.assertIn("不固定目标来源", text)
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

    def test_explicit_invocation_stays_enabled(self):
        text = OPENAI_YAML.read_text(encoding="utf-8")
        self.assertIn('display_name: "综合抓取"', text)
        self.assertIn("$integrated-scraper", text)
        self.assertNotIn("Magewell", text)
        self.assertNotIn("Douyin", text)
        self.assertIn("allow_implicit_invocation: false", text)


if __name__ == "__main__":
    unittest.main()
