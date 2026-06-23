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
    parser.add_argument("--creative", action="store_true", help="generate creative_content.json template for LLM")
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


def compile_outputs(brief: dict, output_dir: Path | None = None) -> dict:
    # 优先检测 shot_prompts.json (LLM 直出 Seedance 分镜提示词)
    shot_prompts_path = (output_dir / "shot_prompts.json") if output_dir else None
    if shot_prompts_path and shot_prompts_path.exists():
        from compile_from_prompts import build_review_package_from_prompts
        shot_prompts = json.loads(shot_prompts_path.read_text(encoding="utf-8"))
        # 检查是否已填充 (非空模板)
        has_content = any(s.get("prompt", "").strip() for s in shot_prompts.get("shots", []))
        if has_content:
            outputs = build_review_package_from_prompts(brief, shot_prompts)
            outputs["script_md"] = render_script_md(outputs["script"], brief)
            outputs["storyboard_md"] = render_storyboard_md(outputs["storyboard"], outputs["seedance"])
            return outputs
    # fallback: 原有编译路径 (含 creative_content.json 检测)
    skeleton = build_skeleton(brief)
    outputs = build_review_package(brief, skeleton, output_dir)
    outputs["script_md"] = render_script_md(outputs["script"], outputs["brief"])
    outputs["storyboard_md"] = render_storyboard_md(outputs["storyboard"], outputs["seedance"])
    return outputs


def compile_to_directory(brief: dict, output_dir: Path, creative: bool = False) -> list[str]:
    if creative:
        # 生成 shot_prompts.json 模板 (LLM 直出模式)
        from creative_writer import generate_shot_prompts_template as gen_shot_template
        gen_shot_template(brief, str(output_dir / "shot_prompts.json"))
    outputs = compile_outputs(brief, output_dir)
    write_outputs(output_dir, outputs)
    return validate_directory(output_dir)


def main() -> None:
    args = parse_args()
    brief = load_brief(args.brief)
    output_dir = ensure_dir(args.output_dir)
    issues = compile_to_directory(brief, output_dir, creative=args.creative)
    if issues:
        raise SystemExit("\n".join(issues))
    print(f"review package written to {output_dir}")
    print("status: pending-review")


if __name__ == "__main__":
    main()
