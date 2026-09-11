import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from test_scripts import load_module, ROOT

bootstrap = load_module("bootstrap", "scripts/bootstrap_pack.py")


class BootstrapTests(unittest.TestCase):
    def test_preview_has_no_writes(self):
        self.assertEqual(bootstrap.preview(ROOT)["status"], "preview")

    def test_validation_dependency_in_install_plan(self):
        plan = bootstrap.preview(ROOT)
        self.assertIn('PyYAML==6.0.2', plan['packages'])
        self.assertEqual(Path(plan['venv']), ROOT / 'runtime/python-env')

    def test_clean_path_with_spaces_and_idempotence(self):
        with tempfile.TemporaryDirectory(prefix="skill pack ") as d:
            root = Path(d)
            result = bootstrap.prepare(root)
            self.assertEqual(len(result["created"]), 2)
            self.assertFalse(result["runtime_ready"])
            self.assertEqual(bootstrap.prepare(root)["created"], [])
            for content in bootstrap.wrappers().values():
                self.assertNotIn(str(root), content)
                self.assertIn('"%~dp0..\\', content)

    def test_different_existing_wrapper_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            bootstrap.prepare(root)
            target = root / "runtime/bin/yt-dlp.cmd"
            target.write_text("custom", encoding="utf-8")
            with self.assertRaises(ValueError):
                bootstrap.prepare(root)
            self.assertEqual(target.read_text(), "custom")

    def test_external_target_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with self.assertRaises(ValueError):
                bootstrap.safe_target(root, root / "../other")

    def test_no_install_without_confirmation(self):
        with patch.object(bootstrap.subprocess, "run") as run:
            with self.assertRaises(ValueError):
                bootstrap.install(ROOT, "unused", False)
            run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
