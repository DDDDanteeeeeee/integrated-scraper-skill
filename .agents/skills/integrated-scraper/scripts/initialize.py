#!/usr/bin/env python3
"""Create a non-secret local configuration for the integrated scraper Skill Pack."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


DEFAULT_OUTPUT_ROOT = r"D:\integrated-scraper-output"
DEFAULT_CDP_URL = "http://127.0.0.1:9222"
PROJECT_ROOT = Path(__file__).resolve().parents[4]
CONFIG_DIRECTORY = PROJECT_ROOT / "config"
RUNTIME_CONTRACT_PATH = PROJECT_ROOT / "runtime.contract.json"


def read_runtime_contract() -> dict[str, object]:
    value = json.loads(RUNTIME_CONTRACT_PATH.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("runtime.contract.json 必须是 JSON 对象")
    return value


RUNTIME_CONTRACT = read_runtime_contract()
FIXED_OPENCLI_PROFILE = str(RUNTIME_CONTRACT["opencli"]["profile"])
FIXED_BROWSER_PORT = int(RUNTIME_CONTRACT["browser"]["remote_debugging_port"])
FIXED_PROFILE_DIRECTORY = PROJECT_ROOT / str(RUNTIME_CONTRACT["browser"]["profile_relative_path"])
FIXED_PYTHON_EXECUTABLE = PROJECT_ROOT / str(RUNTIME_CONTRACT["python"]["executable_relative_path"])
FIXED_PLAYWRIGHT_BROWSERS = PROJECT_ROOT / str(RUNTIME_CONTRACT["python"]["playwright_browsers_relative_path"])
FIXED_SCRAPLING_EXECUTABLE = PROJECT_ROOT / "runtime" / "bin" / "scrapling-project.cmd"
FIXED_YT_DLP_EXECUTABLE = PROJECT_ROOT / "runtime" / "bin" / "yt-dlp.cmd"


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
    opencli_profile: str = FIXED_OPENCLI_PROFILE,
    cdp_url: str = DEFAULT_CDP_URL,
    browser_harness_command: str = "browser-harness",
    chrome_executable: str | None = None,
    scrapling_executable: str = str(FIXED_SCRAPLING_EXECUTABLE),
    yt_dlp_executable: str = str(FIXED_YT_DLP_EXECUTABLE),
) -> dict[str, object]:
    if opencli_profile != FIXED_OPENCLI_PROFILE:
        raise ValueError(f"OpenCLI Profile 固定为 {FIXED_OPENCLI_PROFILE}")
    if cdp_url != DEFAULT_CDP_URL or FIXED_BROWSER_PORT != 9222:
        raise ValueError("综合抓取浏览器固定使用 http://127.0.0.1:9222")
    if output_root != DEFAULT_OUTPUT_ROOT:
        raise ValueError(f"输出目录固定为 {DEFAULT_OUTPUT_ROOT}")
    if chrome_executable is not None and (not Path(chrome_executable).is_absolute() or not Path(chrome_executable).is_file() or Path(chrome_executable).name.lower() != "chrome.exe"):
        raise ValueError("Chrome 必须指向本机已存在的 chrome.exe 绝对路径")
    return {
        "runtime_contract": str(RUNTIME_CONTRACT_PATH),
        "output_root": output_root,
        "opencli": {"command": opencli_command, "profile": opencli_profile},
        "browser_harness": {
            "command": browser_harness_command,
            "cdp_url": cdp_url,
            "remote_debugging_port": FIXED_BROWSER_PORT,
            "chrome_executable": chrome_executable or str(RUNTIME_CONTRACT["browser"]["executable_default"]),
            "user_data_dir": str(FIXED_PROFILE_DIRECTORY),
        },
        "python": {
            "executable": str(FIXED_PYTHON_EXECUTABLE),
            "playwright_browsers_path": str(FIXED_PLAYWRIGHT_BROWSERS),
        },
        "scrapling": {"executable": scrapling_executable},
        "yt_dlp": {"executable": yt_dlp_executable},
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
    parser.add_argument("--opencli-profile", default=FIXED_OPENCLI_PROFILE)
    parser.add_argument("--opencli-command", default="opencli")
    parser.add_argument("--cdp-url", default=DEFAULT_CDP_URL)
    parser.add_argument("--browser-harness-command", default="browser-harness")
    parser.add_argument("--chrome-executable", help="初始化时确认的本机Chrome绝对路径")
    parser.add_argument("--scrapling-executable", default=str(FIXED_SCRAPLING_EXECUTABLE))
    parser.add_argument("--yt-dlp-executable", default=str(FIXED_YT_DLP_EXECUTABLE))
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--write-config", action="store_true")
    args = parser.parse_args()

    if not is_project_config_path(args.config):
        print(status_payload("invalid_config", error="初始化器只能写入项目内的 config/collection.local.json"))
        return 2

    if args.config.exists():
        print(status_payload("already_configured", config=str(args.config), next_action="运行 doctor.py 复检环境"))
        return 0

    try:
        config = build_config(
            output_root=args.output_root,
            opencli_command=args.opencli_command,
            opencli_profile=args.opencli_profile,
            cdp_url=args.cdp_url,
            browser_harness_command=args.browser_harness_command,
            chrome_executable=args.chrome_executable,
            scrapling_executable=args.scrapling_executable,
            yt_dlp_executable=args.yt_dlp_executable,
        )
    except ValueError as error:
        print(status_payload("invalid_config", error=str(error)))
        return 2
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
