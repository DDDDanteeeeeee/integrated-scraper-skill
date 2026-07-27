from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents" / "skills" / "magewell-douyin-intelligence" / "SKILL.md"
OPENAI_YAML = ROOT / ".agents" / "skills" / "magewell-douyin-intelligence" / "agents" / "openai.yaml"


class MetadataTests(unittest.TestCase):
    def test_skill_metadata_is_explicit_and_project_local(self):
        text = SKILL.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\nname: magewell-douyin-intelligence\n"))
        self.assertIn("dependencies.manifest.json", text)
        self.assertIn("pack_doctor.py", text)

    def test_manifest_replaces_misleading_lock_file(self):
        self.assertFalse((ROOT / "dependencies.lock.json").exists())
        manifest = json.loads((ROOT / "dependencies.manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["manifest_type"], "installation-manifest")

    def test_explicit_invocation_stays_enabled(self):
        text = OPENAI_YAML.read_text(encoding="utf-8")
        self.assertIn("allow_implicit_invocation: false", text)


if __name__ == "__main__":
    unittest.main()
