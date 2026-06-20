"""
/**
 * [INPUT]: 依赖 {仓库工作树与常见凭据模式} 的 {推送前 secret 检查需求}
 * [OUTPUT]: 对外提供 {命中文件、行号与阻断式检查结果}
 * [POS]: {scripts} 的 {轻量 secret 守门器}，用于 commit/push 前发现明显私密信息
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {
    ".git",
    ".venv",
    "node_modules",
    ".codegraph",
    ".omx",
}
SKIP_FILES = {
    ".env.example",
}

PATTERNS = [
    ("ark_api_key_assignment", re.compile(r"ARK_API_KEY\s*=\s*\S+")),
    ("generic_api_key_assignment", re.compile(r"(?i)\b(api[_-]?key|token|secret)\b\s*[:=]\s*[\"']?[A-Za-z0-9_\-]{12,}")),
    ("bearer_token", re.compile(r"Bearer\s+[A-Za-z0-9_\-\.]{12,}")),
    ("openai_like_key", re.compile(r"\bsk-[A-Za-z0-9_\-]{10,}\b")),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scan the repo for obvious secret leaks")
    parser.add_argument(
        "--path",
        default=str(ROOT),
        help="repository root to scan",
    )
    return parser.parse_args()


def should_skip(path: Path) -> bool:
    if path.name in SKIP_FILES:
        return True
    return any(part in SKIP_DIRS for part in path.parts)


def scan_file(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []
    hits: list[str] = []
    for index, line in enumerate(text.splitlines(), start=1):
        for label, pattern in PATTERNS:
            if pattern.search(line):
                hits.append(f"{path}:{index}: {label}: {line.strip()}")
    return hits


def main() -> None:
    args = parse_args()
    root = Path(args.path).resolve()
    hits: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if should_skip(path.relative_to(root)):
            continue
        hits.extend(scan_file(path))
    if hits:
        print("Potential secrets found:")
        for hit in hits:
            print(hit)
        raise SystemExit(1)
    print("No obvious secrets found.")


if __name__ == "__main__":
    main()
