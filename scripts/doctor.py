"""
/**
 * [INPUT]: 依赖 {仓库根目录、环境变量与本机工具} 的 {安装体检需求}
 * [OUTPUT]: 对外提供 {profile 化依赖检查报告}
 * [POS]: {scripts} 的 {环境体检器}，在 bootstrap 和用户自检前确认工具链是否可用
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
VENDOR_DIR = ROOT / "adapters" / "douyin-upload-vendor"
VENV_PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"
if os.name != "nt":
    VENV_PYTHON = ROOT / ".venv" / "bin" / "python"


PROFILE_REQUIREMENTS = {
    "core": ["python", "python_deps"],
    "showcase": ["python", "python_deps"],
    "generate-cli": ["python", "python_deps", "seedance"],
    "generate-official": ["python", "python_deps", "seedance", "ark_api_key"],
    "assemble": ["python", "python_deps", "ffmpeg"],
    "publish": ["node", "vendor_install"],
    "all": ["python", "python_deps", "seedance", "ffmpeg", "node", "vendor_install"],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AutoDouyin environment doctor")
    parser.add_argument(
        "--profile",
        default="core",
        choices=sorted(PROFILE_REQUIREMENTS),
        help="dependency profile to check",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print machine-readable JSON report",
    )
    return parser.parse_args()


def run_python_probe(code: str) -> bool:
    python_exe = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable
    result = subprocess.run(
        [python_exe, "-c", code],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def check_python() -> dict:
    return {
        "name": "python",
        "ok": True,
        "detail": str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable,
    }


def check_python_deps() -> dict:
    missing = []
    for module in ("jsonschema", "PIL"):
        if not run_python_probe(f"import {module}"):
            missing.append(module)
    return {
        "name": "python_deps",
        "ok": not missing,
        "detail": "ok" if not missing else f"missing: {', '.join(missing)}",
    }


def check_binary(name: str) -> dict:
    path = shutil.which(name)
    return {
        "name": name,
        "ok": path is not None,
        "detail": path or "not found in PATH",
    }


def check_node() -> dict:
    node = shutil.which("node")
    npm = shutil.which("npm")
    ok = node is not None and npm is not None
    detail = {"node": node or "missing", "npm": npm or "missing"}
    return {"name": "node", "ok": ok, "detail": detail}


def check_vendor_install() -> dict:
    package_json = VENDOR_DIR / "package.json"
    marker = VENDOR_DIR / "node_modules"
    package_lock = VENDOR_DIR / "package-lock.json"
    ok = package_json.exists() and marker.exists() and package_lock.exists()
    return {
        "name": "vendor_install",
        "ok": ok,
        "detail": "installed" if ok else "run `npm install` in adapters/douyin-upload-vendor",
    }


def check_ark_api_key() -> dict:
    token = os.environ.get("ARK_API_KEY", "").strip()
    return {
        "name": "ark_api_key",
        "ok": bool(token),
        "detail": "set" if token else "missing ARK_API_KEY",
    }


def perform_check(name: str) -> dict:
    if name == "python":
        return check_python()
    if name == "python_deps":
        return check_python_deps()
    if name == "seedance":
        return check_binary("seedance")
    if name == "ffmpeg":
        return check_binary("ffmpeg")
    if name == "node":
        return check_node()
    if name == "vendor_install":
        return check_vendor_install()
    if name == "ark_api_key":
        return check_ark_api_key()
    raise ValueError(f"unknown check: {name}")


def report_for_profile(profile: str) -> dict:
    checks = [perform_check(name) for name in PROFILE_REQUIREMENTS[profile]]
    ok = all(item["ok"] for item in checks)
    return {
        "profile": profile,
        "ok": ok,
        "checks": checks,
    }


def print_human(report: dict) -> None:
    status = "OK" if report["ok"] else "FAIL"
    print(f"[{status}] profile={report['profile']}")
    for item in report["checks"]:
        prefix = "[OK]" if item["ok"] else "[FAIL]"
        print(f"{prefix} {item['name']}: {item['detail']}")


def main() -> None:
    args = parse_args()
    report = report_for_profile(args.profile)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_human(report)
    if not report["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
