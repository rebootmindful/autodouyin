"""
/**
 * [INPUT]: 依赖 {generation-report.json 与输出视频块} 的 {角色锚图提取需求}
 * [OUTPUT]: 对外提供 {derived/C01_anchor_*.png}
 * [POS]: {scripts} 的 {人物锚图提取器}，为无参考图场景生成可复用角色参考帧
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from identity_stills import ensure_identity_stills


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract stills from generated blocks for identity anchoring")
    parser.add_argument("--dir", required=True, help="artifact directory containing generation-report.json")
    parser.add_argument("--count", type=int, default=3, help="number of anchor frames to extract")
    return parser.parse_args()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def first_available_block(report: dict) -> Path:
    for block in report.get("blocks", []):
        output_path = block.get("output_path")
        if output_path:
            return Path(output_path)
    raise SystemExit("generation-report.json has no successful block output_path")


def main() -> None:
    args = parse_args()
    directory = Path(args.dir)
    report = load_json(directory / "generation-report.json")
    video_path = first_available_block(report)
    if not video_path.is_absolute():
        video_path = directory / video_path
    if not video_path.exists():
        raise SystemExit(f"video block not found: {video_path}")

    outputs = ensure_identity_stills(directory, video_path, count=args.count)
    print(f"derived identity stills -> {directory / 'derived'}")


if __name__ == "__main__":
    main()
