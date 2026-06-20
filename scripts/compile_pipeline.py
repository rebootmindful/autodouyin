"""
/**
 * [INPUT]: 依赖 {标准化 brief} 的 {视频目标、时长、比例、风格与约束}
 * [OUTPUT]: 对外提供 {skeleton.json + brief.json 结构产物}
 * [POS]: {scripts} 的 {顶层编译入口}，协调结构层产出骨架
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 *
 * 内容填充由 Agent 层完成，见 SKILL.md Enrichment Workflow。
 */
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from compiler_content import build_review_package
from compiler_render import render_script_md, render_storyboard_md, write_outputs
from compile_skeleton import build_skeleton
from normalize_brief import merge_defaults
from validate_artifacts import validate_directory


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--brief", required=True, help="raw brief path")
    parser.add_argument("--output-dir", required=True, help="artifact output dir")
    return parser.parse_args()


def load_brief(path: str) -> dict:
    text = Path(path).read_text(encoding="utf-8")
    return merge_defaults(json.loads(text))


def ensure_dir(path: str) -> Path:
    output_dir = Path(path)
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def compile_outputs(brief: dict) -> dict:
    skeleton = build_skeleton(brief)
    outputs = build_review_package(brief, skeleton)
    outputs["script_md"] = render_script_md(outputs["script"], outputs["brief"])
    outputs["storyboard_md"] = render_storyboard_md(outputs["storyboard"], outputs["seedance"])
    return outputs


def compile_to_directory(brief: dict, output_dir: Path) -> list[str]:
    outputs = compile_outputs(brief)
    write_outputs(output_dir, outputs)
    return validate_directory(output_dir)


def main() -> None:
    args = parse_args()
    brief = load_brief(args.brief)
    output_dir = ensure_dir(args.output_dir)
    issues = compile_to_directory(brief, output_dir)
    if issues:
        raise SystemExit("\n".join(issues))
    print(f"review package written to {output_dir}")
    print("status: pending-review")


if __name__ == "__main__":
    main()
