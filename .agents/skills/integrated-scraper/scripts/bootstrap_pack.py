"""Preview or explicitly prepare local Python tools; never migrate account state."""
import argparse
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[4]


def wrappers():
    common = '@echo off\nsetlocal\nset "PLAYWRIGHT_BROWSERS_PATH=%~dp0..\\ms-playwright"\n'
    return {
        "scrapling-project.cmd": common + '"%~dp0..\\python-env\\Scripts\\scrapling.exe" %*\nexit /b %errorlevel%\n',
        "yt-dlp.cmd": common + '"%~dp0..\\python-env\\Scripts\\python.exe" -m yt_dlp %*\nexit /b %errorlevel%\n',
    }


def preview(root):
    contract = json.loads((root / "runtime.contract.json").read_text(encoding="utf-8"))
    versions = contract["tested_versions"]
    manifest = json.loads((root / "dependencies.manifest.json").read_text(encoding="utf-8"))
    development_packages = [item["package"] for item in manifest["development_dependencies"]]
    return {
        "status": "preview",
        "python_version": versions["python"],
        "venv": str(root / "runtime/python-env"),
        "packages": [f"scrapling[all]=={versions['scrapling']}", f"playwright=={versions['playwright']}", f"yt-dlp=={versions['yt_dlp']}", *development_packages],
        "wrappers": list(wrappers()),
        "manual": ["OpenCLI and BrowserHarness: follow the reviewed installation manifest", "Install upstream Skills only after confirmation", "Browser extension, login and CDP authorization remain local human steps"],
        "boundary": "Pinned direct packages only; not an offline dependency bundle or full transitive lock",
    }


def safe_target(root, path):
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"Path escapes project: {path}")
    current = path
    while current != root:
        if current.is_symlink() or (hasattr(current, "is_junction") and current.is_junction()):
            raise ValueError(f"Reparse target refused: {current}")
        current = current.parent


def prepare(root):
    """Offline only, preflight every target before writing. Existing differences stop."""
    root = root.resolve()
    planned = []
    for name, content in wrappers().items():
        path = root / "runtime/bin" / name
        safe_target(root, path)
        if path.exists():
            if not path.is_file() or path.read_text(encoding="utf-8") != content:
                raise ValueError(f"Existing wrapper differs; preserve and review manually: {path}")
        else:
            planned.append((path, content))
    for path, content in planned:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
    return {"status": "prepared", "created": [str(path) for path, _ in planned], "runtime_ready": False}


def run(command, **kwargs):
    subprocess.run(command, check=True, timeout=900, **kwargs)


def install(root, base_python, confirmed):
    if not confirmed:
        raise ValueError("External installation requires --confirm-install")
    if os.name != "nt":
        raise ValueError("This pack supports Windows only")
    plan = preview(root)
    base = Path(base_python).resolve(strict=True)
    observed = subprocess.check_output([str(base), "-c", "import platform; print(platform.python_version())"], text=True, timeout=20).strip()
    if observed != plan["python_version"]:
        raise ValueError(f"Base Python version mismatch: {observed}, expected {plan['python_version']}")
    venv = root / "runtime/python-env"
    safe_target(root, venv)
    executable = venv / "Scripts/python.exe"
    safe_target(root, executable)
    if venv.exists():
        # Never repair/recreate an existing environment implicitly.
        if not executable.is_file():
            raise ValueError("Existing incomplete venv; manual review required")
        observed = subprocess.check_output([str(executable), "-c", "import platform; print(platform.python_version())"], text=True, timeout=20).strip()
        if observed != plan["python_version"]:
            raise ValueError("Existing venv version mismatch; refusing to replace")
    else:
        run([str(base), "-m", "venv", str(venv)])
    browser_path = root / "runtime/ms-playwright"
    safe_target(root, browser_path)
    environment = dict(os.environ, PLAYWRIGHT_BROWSERS_PATH=str(browser_path), PYTHONNOUSERSITE="1")
    run([str(executable), "-m", "pip", "install", *plan["packages"]], env=environment)
    run([str(executable), "-m", "pip", "check"], env=environment)
    run([str(executable), "-m", "playwright", "install", "chromium"], env=environment)
    return {"status": "python_tools_installed", "runtime_ready": False, "next": "initialize.py --write-config, then task-scoped doctor"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Prepare missing wrappers without downloading anything")
    parser.add_argument("--install-python-tools", action="store_true")
    parser.add_argument("--base-python", type=Path)
    parser.add_argument("--confirm-install", action="store_true")
    args = parser.parse_args()
    try:
        if args.install_python_tools and (not args.apply or not args.base_python or not args.confirm_install):
            raise ValueError("Installation requires --apply --base-python <path> --confirm-install")
        result = preview(ROOT)
        if args.apply:
            result = prepare(ROOT)
        if args.install_python_tools:
            result = install(ROOT, args.base_python, args.confirm_install)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(json.dumps({"status": "blocked_dependency", "error": str(error)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
