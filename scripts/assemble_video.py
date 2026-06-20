"""
/**
 * [INPUT]: 依赖 {generation-report.json 与生成片段} 的 {长视频组装需求}
 * [OUTPUT]: 对外提供 {assembled-video.mp4 + assembly-report.json}
 * [POS]: {scripts} 的 {后处理组装器}，负责把多段输出合成为最终视频
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Assemble multiple generated blocks into one video")
    parser.add_argument("--dir", required=True, help="artifact directory containing generation-report.json")
    parser.add_argument("--output", default="assembled-video.mp4", help="final assembled filename")
    return parser.parse_args()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def generated_paths(directory: Path, report: dict) -> list[Path]:
    paths = []
    blocks = report.get("blocks", [])
    if not blocks and report.get("commands"):
        for command in report["commands"]:
            blocks.append({
                "block_id": command["block_id"],
                "output_path": str(directory / f"{command['block_id']}.mp4"),
            })
    for block in blocks:
        output_path = block.get("output_path") or str(directory / f"{block['block_id']}.mp4")
        path = Path(output_path)
        if not path.is_absolute():
            path = directory / path
        paths.append(path)
    return paths


def write_concat_list(directory: Path, paths: list[Path]) -> Path:
    concat_path = directory / "assembly-inputs.txt"
    lines = [f"file '{path.as_posix()}'" for path in paths]
    concat_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return concat_path


def ffmpeg_concat(concat_path: Path, output_path: Path) -> None:
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_path),
        "-c",
        "copy",
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        raise SystemExit(result.stderr[:1000] or "ffmpeg concat failed")


def main() -> None:
    args = parse_args()
    directory = Path(args.dir)
    report_path = directory / "generation-report.json"
    if not report_path.exists():
        raise SystemExit(f"missing {report_path}")

    report = load_json(report_path)
    blocks = report.get("blocks", [])
    if not blocks and not report.get("commands"):
        raise SystemExit("generation-report.json has no executable blocks")

    paths = generated_paths(directory, report)
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        raise SystemExit("missing generated blocks:\n" + "\n".join(missing))

    if len(paths) == 1:
        output_path = directory / args.output
        output_path.write_bytes(paths[0].read_bytes())
        status = "copied-single-block"
    else:
        concat_path = write_concat_list(directory, paths)
        output_path = directory / args.output
        ffmpeg_concat(concat_path, output_path)
        concat_path.unlink(missing_ok=True)
        status = "assembled"

    assembly_report = {
        "status": status,
        "input_blocks": [path.name for path in paths],
        "output_path": str(output_path),
    }
    (directory / "assembly-report.json").write_text(
        json.dumps(assembly_report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"assembled -> {output_path}")


if __name__ == "__main__":
    main()
