#!/usr/bin/env python3
"""Create a non-secret local configuration for the Douyin intelligence Skill Pack."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


DEFAULT_OUTPUT_ROOT = r"D:\douyin-intelligence-output"
DEFAULT_CDP_URL = "http://127.0.0.1:9222"
PROJECT_ROOT = Path(__file__).resolve().parents[4]
CONFIG_DIRECTORY = PROJECT_ROOT / "config"


def default_config_path() -> Path:
    return CONFIG_DIRECTORY / "collection.local.json"


def is_project_config_path(path: Path) -> bool:
    return path.resolve() == default_config_path().resolve()


def configured_text(value: str | None) -> bool:
    return bool(value and value.strip() and not value.strip().startswith("replace-with-"))


def build_config(
    *,
    output_root: str = DEFAULT_OUTPUT_ROOT,
    opencli_command: str = "opencli",
    opencli_profile: str,
    cdp_url: str = DEFAULT_CDP_URL,
    scrapling_executable: str = "scrapling",
) -> dict[str, object]:
    if not configured_text(opencli_profile):
        raise ValueError("需要用户确认本机 OpenCLI Profile 名称")
    return {
        "output_root": output_root,
        "opencli": {"command": opencli_command, "profile": opencli_profile},
        "browser_harness": {"python": "python", "cdp_url": cdp_url},
        "scrapling": {"executable": scrapling_executable},
    }


def write_config(path: Path, config: dict[str, object]) -> None:
    if path.exists():
        raise FileExistsError("本机配置已存在；初始化器不会覆盖它")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def status_payload(status: str, **extra: object) -> str:
    return json.dumps({"status": status, **extra}, ensure_ascii=False)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=default_config_path())
    parser.add_argument("--opencli-profile")
    parser.add_argument("--opencli-command", default="opencli")
    parser.add_argument("--cdp-url", default=DEFAULT_CDP_URL)
    parser.add_argument("--scrapling-executable", default="scrapling")
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--write-config", action="store_true")
    args = parser.parse_args()

    if not is_project_config_path(args.config):
        print(status_payload("invalid_config", error="初始化器只能写入项目内的 config/collection.local.json"))
        return 2

    if args.config.exists():
        print(status_payload("already_configured", config=str(args.config), next_action="运行 doctor.py 复检环境"))
        return 0

    if not configured_text(args.opencli_profile):
        print(
            status_payload(
                "awaiting_human",
                missing=["opencli.profile"],
                next_action="确认本机 OpenCLI Profile 名称后，以 --opencli-profile 重新运行",
            )
        )
        return 2

    config = build_config(
        output_root=args.output_root,
        opencli_command=args.opencli_command,
        opencli_profile=args.opencli_profile,
        cdp_url=args.cdp_url,
        scrapling_executable=args.scrapling_executable,
    )
    if not args.write_config:
        print(status_payload("ready_to_write", config=str(args.config), proposed=config))
        return 0

    try:
        write_config(args.config, config)
    except FileExistsError as error:
        print(status_payload("already_configured", config=str(args.config), detail=str(error)))
        return 0
    print(status_payload("configured", config=str(args.config), next_action="运行 doctor.py 复检环境"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
