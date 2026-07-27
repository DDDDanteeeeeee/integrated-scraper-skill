#!/usr/bin/env python3
"""Check local, non-secret prerequisites for the Magewell Douyin skill."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import urlopen

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
    candidate = Path(command)
    return candidate.is_file() if candidate.parent != Path(".") else shutil.which(command) is not None


def configured_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip()) and not value.strip().startswith("replace-with-")


def is_loopback_cdp_url(url: str) -> bool:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    return parsed.scheme == "http" and host in {"127.0.0.1", "::1", "localhost"}


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
) -> dict:
    sensitive_path = contains_sensitive_key(config)
    if sensitive_path:
        return {"status": "invalid_config", "error": f"本地配置不得包含敏感字段：{sensitive_path}", "checks": {}}

    checks: dict[str, dict[str, object]] = {}
    opencli = config.get("opencli", {})
    command = opencli.get("command") if isinstance(opencli, dict) else None
    profile = opencli.get("profile") if isinstance(opencli, dict) else None
    opencli_ready = configured_text(command) and command_checker(command) and configured_text(profile)
    checks["opencli"] = {
        "ready": opencli_ready,
        "detail": "已配置命令和 Profile" if opencli_ready else "需要可用的 opencli 命令和本机 Profile 名称（不能使用示例占位值）",
    }

    browser = config.get("browser_harness", {})
    cdp_url = browser.get("cdp_url") if isinstance(browser, dict) else None
    if isinstance(cdp_url, str) and cdp_url.startswith("http://"):
        ready, detail = cdp_probe(cdp_url)
        checks["browser"] = {"ready": ready, "detail": detail}
    else:
        checks["browser"] = {"ready": False, "detail": "未配置本机 CDP 地址"}

    scrapling = config.get("scrapling", {})
    executable = scrapling.get("executable") if isinstance(scrapling, dict) else None
    scrapling_ready = configured_text(executable) and command_checker(executable)
    checks["scrapling"] = {
        "ready": scrapling_ready,
        "detail": "可执行文件可用" if scrapling_ready else "未配置、示例占位值或找不到 Scrapling",
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
