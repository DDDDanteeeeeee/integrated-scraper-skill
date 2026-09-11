#!/usr/bin/env python3
"""Check local, non-secret prerequisites for the integrated scraper skill."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import urlopen


PROJECT_ROOT = Path(__file__).resolve().parents[4]
RUNTIME_CONTRACT_PATH = PROJECT_ROOT / "runtime.contract.json"

SENSITIVE_KEYWORDS = (
    "password",
    "passwd",
    "cookie",
    "session",
    "token",
    "secret",
    "api_key",
    "authorization",
    "credential",
    "otp",
    "mfa",
    "验证码",
    "口令",
)


def contains_sensitive_key(value: object, path: str = "config") -> str | None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if any(word in str(key).lower() for word in SENSITIVE_KEYWORDS):
                return f"{path}.{key}"
            found = contains_sensitive_key(nested, f"{path}.{key}")
            if found:
                return found
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            found = contains_sensitive_key(nested, f"{path}[{index}]")
            if found:
                return found
    return None


def command_available(command: str) -> bool:
    try:
        candidate = Path(command)
        return candidate.is_file() if candidate.parent != Path(".") else shutil.which(command) is not None
    except OSError:
        return False


def configured_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip()) and not value.strip().startswith("replace-with-")


def is_loopback_cdp_url(url: str) -> bool:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    return parsed.scheme == "http" and host in {"127.0.0.1", "::1", "localhost"}


def normalize_path(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        return ""
    return str(Path(value).resolve()).casefold()


def runtime_contract() -> dict:
    value = json.loads(RUNTIME_CONTRACT_PATH.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("runtime.contract.json 必须是 JSON 对象")
    return value


def fixed_runtime_error(config: dict) -> str | None:
    contract = runtime_contract()
    browser_contract = contract["browser"]
    opencli_contract = contract["opencli"]
    python_contract = contract["python"]
    browser = config.get("browser_harness", {})
    opencli = config.get("opencli", {})
    python_config = config.get("python", {})
    expected_profile_dir = PROJECT_ROOT / str(browser_contract["profile_relative_path"])
    expected_python = PROJECT_ROOT / str(python_contract["executable_relative_path"])
    expected_playwright = PROJECT_ROOT / str(python_contract["playwright_browsers_relative_path"])
    checks = (
        (normalize_path(config.get("runtime_contract")) == normalize_path(str(RUNTIME_CONTRACT_PATH)), "runtime_contract 路径不匹配"),
        (config.get("output_root") == r"D:\integrated-scraper-output", "output_root 必须固定为 D:\\integrated-scraper-output"),
        (isinstance(opencli, dict) and opencli.get("profile") == opencli_contract["profile"], f"OpenCLI Profile 必须固定为 {opencli_contract['profile']}"),
        (isinstance(browser, dict) and browser.get("cdp_url") == browser_contract["cdp_url"], "浏览器 CDP 必须固定为 http://127.0.0.1:9222"),
        (isinstance(browser, dict) and browser.get("remote_debugging_port") == 9222, "浏览器端口必须固定为 9222"),
        (isinstance(browser, dict) and normalize_path(browser.get("user_data_dir")) == normalize_path(str(expected_profile_dir)), "浏览器 Profile 必须使用项目 runtime/chrome-public-profile"),
        (isinstance(python_config, dict) and normalize_path(python_config.get("executable")) == normalize_path(str(expected_python)), "Python 必须使用项目 runtime/python-env"),
        (isinstance(python_config, dict) and normalize_path(python_config.get("playwright_browsers_path")) == normalize_path(str(expected_playwright)), "Playwright 浏览器必须保存在项目 runtime/ms-playwright"),
        (9223 in browser_contract.get("forbidden_ports", []), "runtime.contract.json 必须禁止端口 9223"),
    )
    for passed, message in checks:
        if not passed:
            return message
    return None


def probe_cdp(url: str) -> tuple[bool, str]:
    if not is_loopback_cdp_url(url):
        return False, "CDP 地址必须是本机 http://127.0.0.1、http://localhost 或 http://[::1]"
    try:
        with urlopen(f"{url.rstrip('/')}/json/version", timeout=3) as response:
            payload = json.load(response)
        return True, str(payload.get("Browser", "connected"))
    except (URLError, TimeoutError, ValueError, OSError) as error:
        return False, str(error)


def check(
    config: dict,
    *,
    command_checker=command_available,
    cdp_probe=probe_cdp,
    required_checks: set[str] | None = None,
) -> dict:
    sensitive_path = contains_sensitive_key(config)
    if sensitive_path:
        return {"status": "invalid_config", "error": f"本地配置不得包含敏感字段：{sensitive_path}", "checks": {}}
    try:
        runtime_error = fixed_runtime_error(config)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        return {"status": "invalid_config", "error": str(error), "checks": {}}
    if runtime_error:
        return {"status": "invalid_config", "error": runtime_error, "checks": {}}

    active = {"opencli", "browser", "scrapling", "yt-dlp", "python"} if required_checks is None else set(required_checks)
    checks: dict[str, dict[str, object]] = {}
    opencli = config.get("opencli", {})
    command = opencli.get("command") if isinstance(opencli, dict) else None
    profile = opencli.get("profile") if isinstance(opencli, dict) else None
    opencli_ready = configured_text(command) and command_checker(command) and configured_text(profile) if "opencli" in active else None
    checks["opencli"] = {
        "ready": opencli_ready,
        "detail": "本次未检查" if "opencli" not in active else ("已配置命令和 Profile" if opencli_ready else "需要可用的 opencli 命令和本机 Profile 名称（不能使用示例占位值）"),
    }

    browser = config.get("browser_harness", {})
    cdp_url = browser.get("cdp_url") if isinstance(browser, dict) else None
    if "browser" not in active:
        checks["browser"] = {"ready": None, "detail": "本次未检查"}
    elif isinstance(cdp_url, str) and cdp_url.startswith("http://"):
        ready, detail = cdp_probe(cdp_url)
        checks["browser"] = {"ready": ready, "detail": detail}
    else:
        checks["browser"] = {"ready": False, "detail": "未配置本机 CDP 地址"}

    scrapling = config.get("scrapling", {})
    executable = scrapling.get("executable") if isinstance(scrapling, dict) else None
    scrapling_ready = configured_text(executable) and command_checker(executable) if "scrapling" in active else None
    checks["scrapling"] = {
        "ready": scrapling_ready,
        "detail": "本次未检查" if "scrapling" not in active else ("可执行文件可用" if scrapling_ready else "未配置、示例占位值或找不到 Scrapling"),
    }
    yt_dlp = config.get("yt_dlp", {})
    yt_dlp_executable = yt_dlp.get("executable") if isinstance(yt_dlp, dict) else None
    yt_dlp_ready = configured_text(yt_dlp_executable) and command_checker(yt_dlp_executable) if "yt-dlp" in active else None
    checks["yt-dlp"] = {
        "ready": yt_dlp_ready,
        "detail": "本次未检查" if "yt-dlp" not in active else ("可执行文件可用" if yt_dlp_ready else "未配置、示例占位值或找不到 yt-dlp"),
    }
    python_config = config.get("python", {})
    python_executable = python_config.get("executable") if isinstance(python_config, dict) else None
    python_ready = configured_text(python_executable) and command_checker(python_executable) if "python" in active else None
    checks["python"] = {
        "ready": python_ready,
        "detail": "本次未检查" if "python" not in active else ("项目 Python 可执行文件可用" if python_ready else "找不到项目 runtime/python-env Python"),
    }
    return {"status": "checked", "checks": checks}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--require", action="append", choices=("opencli", "browser", "scrapling"), default=[])
    args = parser.parse_args()
    try:
        config = json.loads(args.config.read_text(encoding="utf-8"))
        if not isinstance(config, dict):
            raise ValueError("配置根节点必须是对象")
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"status": "invalid_config", "error": str(error)}, ensure_ascii=False))
        return 1
    result = check(config)
    missing = [name for name in args.require if not result.get("checks", {}).get(name, {}).get("ready")]
    if missing and result["status"] == "checked":
        result["status"] = "awaiting_human" if missing == ["browser"] else "blocked_dependency"
        result["missing"] = missing
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "checked" else 2


if __name__ == "__main__":
    raise SystemExit(main())
