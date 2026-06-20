"""
/**
 * [INPUT]: 依赖 {script、storyboard、seedance-job 与 brief} 的 {渲染需求}
 * [OUTPUT]: 对外提供 {markdown 渲染与产物写盘能力}
 * [POS]: {scripts} 的 {输出渲染模块}，承担文档相与文件写入层
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */
"""

from __future__ import annotations

import json
from pathlib import Path

from compiler_types import duration_mode


def render_script_md(script: dict, brief: dict) -> str:
    lines = [
        f"# {script['title']}",
        "",
        script["logline"],
        "",
        f"- 模式：{brief['mode']}",
        f"- 时长：{brief['duration_seconds']}s",
        f"- 比例：{brief['aspect_ratio']}",
        f"- 视频类型：{script['video_type']}",
        f"- 编译策略：{duration_mode(brief)}",
        f"- 方法论：{script['strategy']}",
        *([f"- 模板模式：{script['template_mode']}"] if script.get("template_mode") else []),
        *([f"- 模板置信度：{script['template_confidence']}"] if script.get("template_confidence") else []),
        "",
    ]
    for segment in script["segments"]:
        spoken_line = segment.get("spoken_line", "")
        lines.extend(
            [
                f"## {segment['segment_id']} {segment['purpose']}",
                f"- 时长：{segment['estimated_seconds']}s",
                f"- 情绪：{segment['emotion']}",
                f"- 摘要：{segment['summary']}",
                *([f"- 口播：{spoken_line}"] if spoken_line else []),
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def render_storyboard_md(storyboard: dict, seedance_job: dict) -> str:
    lines = [
        "# Storyboard",
        "",
        "## 全局锁定",
        *[f"- {item}" for item in seedance_job["continuity_locks"]],
        "",
        "## 负面约束",
        *[f"- {item}" for item in seedance_job["negative_constraints"]],
        "",
    ]
    for shot in storyboard["shots"]:
        lines.extend(
            [
                f"## {shot['shot_id']} {shot['start_second']}-{shot['end_second']}s",
                f"- Scene：{shot['scene_id']}",
                f"- 阶段：{shot['segment_mode']}",
                f"- 目的：{shot['purpose']}",
                f"- 画面：{shot['visual']}",
                f"- 镜头：{shot['camera']}",
                f"- 编码：{shot['camera_codec']['z']} {shot['camera_codec']['y']} {shot['camera_codec']['x']} / {shot['camera_codec']['focal_length_mm']}mm / {shot['camera_codec']['depth']}",
                f"- 动作：{shot['action']}",
                *([f"- 台词：{shot['dialogue']}"] if shot.get("dialogue") else []),
                f"- 音频：{shot['audio']}",
                f"- 素材：{', '.join(shot['assets'])}",
                f"- 衔接：{shot['continuity_note']}",
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_outputs(output_dir: Path, outputs: dict) -> None:
    write_json(output_dir / "brief.json", outputs["brief"])
    write_json(output_dir / "script.json", outputs["script"])
    write_json(output_dir / "storyboard.json", outputs["storyboard"])
    write_json(output_dir / "asset-manifest.json", outputs["assets"])
    write_json(output_dir / "seedance-job.json", outputs["seedance"])
    write_json(output_dir / "publish-job.json", outputs["publish"])
    write_json(output_dir / "run-ledger.json", outputs["ledger"])
    if "review_decision" in outputs:
        write_json(output_dir / "review-decision.json", outputs["review_decision"])
    (output_dir / "script.md").write_text(outputs["script_md"], encoding="utf-8")
    (output_dir / "storyboard.md").write_text(outputs["storyboard_md"], encoding="utf-8")
    if "review_summary" in outputs:
        (output_dir / "review-summary.md").write_text(outputs["review_summary"], encoding="utf-8")
