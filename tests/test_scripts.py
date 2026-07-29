from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / ".agents" / "skills" / "magewell-douyin-intelligence"


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


class DoctorTests(unittest.TestCase):
    def test_rejects_sensitive_local_config(self):
        result = doctor.check({"opencli": {"session": "forbidden"}})
        self.assertEqual(result["status"], "invalid_config")

    def test_example_placeholders_are_not_ready(self):
        result = doctor.check(
            {
                "opencli": {"command": "replace-with-local-command", "profile": "replace-with-local-profile"},
                "scrapling": {"executable": "replace-with-local-command"},
            }
        )
        self.assertFalse(result["checks"]["opencli"]["ready"])
        self.assertFalse(result["checks"]["scrapling"]["ready"])

    def test_rejects_non_loopback_cdp_endpoint(self):
        ready, detail = doctor.probe_cdp("https://example.com")
        self.assertFalse(ready)
        self.assertIn("本机", detail)


class ValidatorTests(unittest.TestCase):
    def make_run(self, root: Path, status: str = "success", overall: str = "success") -> list[str]:
        rounds_dir = root / "rounds"
        for round_name in validator.ROUNDS:
            path = rounds_dir / round_name
            path.mkdir(parents=True)
            (path / "round_manifest.json").write_text(
                json.dumps(
                    {
                        "round": round_name,
                        "skill": round_name,
                        "status": status,
                        "timestamp": "2026-07-27T00:00:00+08:00",
                        "target": "美乐威 Magewell",
                        "result": {},
                        **({"recovery_condition": "install or configure"} if status != "success" else {}),
                    }
                ),
                encoding="utf-8",
            )
        summary = root / "summary.json"
        summary.write_text(
            json.dumps({"overall_status": overall, "current_douyin_primary_evidence": True}),
            encoding="utf-8",
        )
        return validator.validate(rounds_dir, summary)

    def test_accepts_complete_truthful_run(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(self.make_run(Path(directory)), [])

    def test_rejects_success_after_blocked_round(self):
        with tempfile.TemporaryDirectory() as directory:
            errors = self.make_run(Path(directory), status="blocked_dependency", overall="success")
        self.assertIn("存在部分成功、阻塞或失败轮次时总体状态不得为 success", errors)

    def test_rejects_success_after_partial_round(self):
        with tempfile.TemporaryDirectory() as directory:
            errors = self.make_run(Path(directory), status="partial_success", overall="success")
        self.assertIn("存在部分成功、阻塞或失败轮次时总体状态不得为 success", errors)


class InitializerTests(unittest.TestCase):
    def test_requires_profile_for_config(self):
        with self.assertRaises(ValueError):
            initializer.build_config(opencli_profile="")

    def test_builds_non_secret_local_config(self):
        config = initializer.build_config(opencli_profile="douyin-work")
        self.assertEqual(config["opencli"]["profile"], "douyin-work")
        self.assertEqual(config["output_root"], r"D:\magewell-douyin-output")
        self.assertIsNone(doctor.contains_sensitive_key(config))

    def test_never_overwrites_existing_config(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "collection.local.json"
            path.write_text("{}", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                initializer.write_config(path, initializer.build_config(opencli_profile="douyin-work"))

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
        self.assertEqual(ids, ["opencli", "browser-harness", "last30days", "last30days-cn", "scrapling", "cloakbrowser"])
        self.assertTrue(all(item["confirmation_required_before_install"] for item in manifest["dependencies"]))
        self.assertTrue(all("version_policy" in item and "installation" in item for item in manifest["dependencies"]))


class PackDoctorTests(unittest.TestCase):
    def config(self):
        return {
            "output_root": r"D:\magewell-douyin-output",
            "opencli": {"command": "opencli", "profile": "douyin-work"},
            "browser_harness": {"python": "python", "cdp_url": "http://127.0.0.1:9222"},
            "scrapling": {"executable": "scrapling"},
        }

    def roots_with_skills(self, root: Path, missing: str | None = None):
        for skill_id in pack_doctor.SKILL_IDS:
            if skill_id == missing:
                continue
            path = root / skill_id
            path.mkdir(parents=True)
            (path / "SKILL.md").write_text("---\nname: test\ndescription: test\n---\n", encoding="utf-8")
        return [root]

    def test_requires_every_non_conditional_dependency(self):
        manifest = DependencyManifestTests().load_manifest()
        with tempfile.TemporaryDirectory() as directory:
            result = pack_doctor.check_pack(
                self.config(),
                manifest,
                self.roots_with_skills(Path(directory), missing="last30days"),
                command_checker=lambda _: True,
                cdp_probe=lambda _: (True, "Chrome"),
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
            )
        self.assertEqual(result["status"], "awaiting_human")
        self.assertEqual(result["checks"]["browser-harness"]["status"], "awaiting_human")

    def test_accepts_chrome_discovery_404_when_browser_harness_is_connected(self):
        manifest = DependencyManifestTests().load_manifest()
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(
                pack_doctor,
                "browser_harness_health",
                return_value=(True, "daemon 正常且存在 1 个活动连接"),
                create=True,
            ):
                result = pack_doctor.check_pack(
                    self.config(),
                    manifest,
                    self.roots_with_skills(Path(directory)),
                    command_checker=lambda _: True,
                    cdp_probe=lambda _: (False, "HTTP Error 404: Not Found"),
                )
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["checks"]["browser-harness"]["status"], "success")
        self.assertIn("Chrome 147+", result["checks"]["browser-harness"]["detail"])

    def test_keeps_chrome_discovery_404_blocked_without_browser_harness_connection(self):
        manifest = DependencyManifestTests().load_manifest()
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(
                pack_doctor,
                "browser_harness_health",
                return_value=(False, "没有活动浏览器连接"),
                create=True,
            ):
                result = pack_doctor.check_pack(
                    self.config(),
                    manifest,
                    self.roots_with_skills(Path(directory)),
                    command_checker=lambda _: True,
                    cdp_probe=lambda _: (False, "HTTP Error 404: Not Found"),
                )
        self.assertEqual(result["status"], "awaiting_human")
        self.assertEqual(result["checks"]["browser-harness"]["status"], "awaiting_human")

    def test_browser_harness_health_accepts_local_connection_with_optional_cloud_failure(self):
        completed = SimpleNamespace(
            stdout=(
                "browser-harness doctor\n"
                "  [ok  ] daemon alive\n"
                "  [ok  ] active browser connections — 1\n"
                "  [FAIL] Browser Use cloud auth — optional\n"
            ),
            stderr="",
            returncode=0,
        )
        ready, detail = pack_doctor.browser_harness_health(
            runner=lambda *args, **kwargs: completed
        )
        self.assertTrue(ready)
        self.assertIn("活动浏览器连接", detail)

    def test_browser_harness_health_rejects_zero_active_connections(self):
        completed = SimpleNamespace(
            stdout=(
                "browser-harness doctor\n"
                "  [ok  ] daemon alive\n"
                "  [FAIL] active browser connections — 0\n"
            ),
            stderr="",
            returncode=1,
        )
        ready, detail = pack_doctor.browser_harness_health(
            runner=lambda *args, **kwargs: completed
        )
        self.assertFalse(ready)
        self.assertIn("没有活动浏览器连接", detail)

    def test_reports_success_only_when_all_required_dependencies_are_ready(self):
        manifest = DependencyManifestTests().load_manifest()
        with tempfile.TemporaryDirectory() as directory:
            result = pack_doctor.check_pack(
                self.config(),
                manifest,
                self.roots_with_skills(Path(directory)),
                command_checker=lambda _: True,
                cdp_probe=lambda _: (True, "Chrome"),
            )
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["checks"]["cloakbrowser"]["status"], "compliant_skip")


if __name__ == "__main__":
    unittest.main()
