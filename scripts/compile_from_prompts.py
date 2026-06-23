"""
/**
 * [INPUT]: 依赖 {shot_prompts.json + brief.json} 的 {LLM 直出的 Seedance 分镜提示词}
 * [OUTPUT]: 对外提供 {完整 review package — seedance-job/storyboard/script/assets/publish}
 * [POS]: {scripts} 的 {反向编译器}，LLM 写 prompt → 编译器做结构化和补全
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 *
 * 设计原则:
 *   LLM 负责想象力 — 用 Seedance 原生语言写分镜提示词，零约束
 *   编译器负责结构化 — schema 映射、技术补全、校验、产物生成
 *
 * 流程: shot_prompts.json + brief.json → 完整 review package
 */
"""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ── 常量 ──

NEGATIVE_CONSTRAINTS = [
    "禁止风格漂移", "禁止角色变脸或换人", "禁止突然偏色",
    "禁止新增无关人物", "禁止光线突变",
    "禁止出现文字、字幕、LOGO、水印",
]

CONTINUITY_LOCKS = [
    "统一视觉风格，画面干净，避免风格漂移",
    "同一角色保持一致五官、身份、服装和发型，不变脸、不换人。",
    "同一场景保持一致环境、光线、背景与空间关系，不突然切换。",
]


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_presets() -> dict:
    path = ROOT / "references" / "aesthetic-presets.json"
    return json.loads(path.read_text(encoding="utf-8"))["presets"]


# ──────────────────────────────────────────────
# Seedance job 构建
# ──────────────────────────────────────────────

def build_seedance_job(brief: dict, shot_prompts: dict) -> dict:
    """从 shot_prompts 构建 seedance-job.json."""
    preset_id = brief.get("aesthetic_preset", "microsoft-fluent")
    presets = load_presets()
    preset = presets.get(preset_id, presets.get("microsoft-fluent", {}))

    style_anchor = preset.get("seedance_style_anchor", "")
    if not style_anchor:
        # fallback: 从 visual_keywords 构建
        kw = preset.get("visual_keywords", [])
        style_anchor = ", ".join(kw[:5]) if kw else "clean commercial aesthetic"
    negative_additions = preset.get("seedance_negative_additions", [])
    all_negatives = NEGATIVE_CONSTRAINTS + negative_additions

    prompt_blocks = []
    for shot in shot_prompts["shots"]:
        start = shot["start_second"]
        end = shot["end_second"]
        dur = int(end - start)
        prompt_text = shot["prompt"]
        # 追加技术指令
        directives = f"--dur {dur}"
        resolution = brief.get("resolution", "720p")
        if resolution:
            directives += f" --rs {resolution}"
        ratio = brief.get("aspect_ratio", "9:16")
        if ratio:
            directives += f" --rt {ratio}"
        full_prompt = f"{prompt_text} {directives}"
        is_first = (start == 0)

        block = {
            "block_id": f"pb-{shot['shot_id'][-2:]}",
            "scene_id": "scene-01",
            "mode": "segment-base" if is_first else "segment-extension",
            "start_second": start,
            "end_second": end,
            "duration_seconds": dur,
            "prompt": full_prompt,
            "image_refs": [],
            "video_refs": [],
            "audio_refs": [],
        }
        # extension blocks reference the first block's video for continuity
        if not is_first and len(prompt_blocks) > 0:
            block["video_refs"] = ["@视频1"]
        prompt_blocks.append(block)

    # slot_plan from shot_prompts hints
    slot_plan = [
        {"ref": "@图片1", "asset_id": "C01", "usage": "主体一致性参考"},
        {"ref": "@图片2", "asset_id": "S01", "usage": "场景或空间背景参考"},
    ]

    multi_block = len(prompt_blocks) > 1
    if multi_block and brief["duration_seconds"] > 15:
        job_mode = "segmented-extension"
    elif multi_block:
        job_mode = "multi-shot-sequence"
    else:
        job_mode = "single-sequence"
    return {
        "id": f"seedance-job-{brief['id']}",
        "storyboard_id": f"storyboard-{brief['id']}",
        "duration_seconds": brief["duration_seconds"],
        "aspect_ratio": brief["aspect_ratio"],
        "mode": job_mode,
        "global_style_anchor": style_anchor,
        "continuity_locks": CONTINUITY_LOCKS + [style_anchor] if style_anchor else CONTINUITY_LOCKS,
        "negative_constraints": all_negatives,
        "slot_plan": slot_plan,
        "video_type": brief.get("video_type", "product-demo"),
        "strategy": "five-beat-short-video" if len(prompt_blocks) <= 5 else "three-phase-segmented-video",
        "identity_strategy": "first-block-anchor" if multi_block else "text-only",
        "execution_recommendation": {
            "video_type": brief.get("video_type", "product-demo"),
            "hard_single_generation_range_seconds": [4, 15],
            "official_ui_recommended_range_seconds": [5, 12],
            "fastest_test_window_seconds": [4, 5],
            "fastest_practical_window_seconds": [5, 8],
            "stable_expression_window_seconds": [6, 10],
            "default_duration_seconds_for_type": 10,
            "max_single_generation_seconds": 15,
            "scene_split_recommended_after_seconds": 60,
            "suggested_split_strategy": f"{len(prompt_blocks)} segments preferred",
            "requested_duration_seconds": brief["duration_seconds"],
        },
        "scene_plan": [],
        "prompt_blocks": prompt_blocks,
    }


# ──────────────────────────────────────────────
# Storyboard 构建
# ──────────────────────────────────────────────

def _parse_camera_hint(hint: str) -> dict:
    """从 LLM 的 camera_hint 提取 camera_codec 字段."""
    import re
    codec = {"z": "Z5", "y": "Y4", "x": "X2", "focal_length_mm": 50, "depth": "medium"}
    if not hint:
        return codec
    # 尝试匹配 Z\d Y\d X\d
    zm = re.search(r'Z(\d)', hint)
    ym = re.search(r'Y(\d)', hint)
    xm = re.search(r'X(\d)', hint)
    fm = re.search(r'(\d{2,3})\s*mm', hint)
    if zm: codec["z"] = f"Z{zm.group(1)}"
    if ym: codec["y"] = f"Y{ym.group(1)}"
    if xm: codec["x"] = f"X{xm.group(1)}"
    if fm: codec["focal_length_mm"] = int(fm.group(1))
    if "shallow" in hint.lower(): codec["depth"] = "shallow"
    elif "deep" in hint.lower(): codec["depth"] = "deep"
    return codec


def build_storyboard(brief: dict, shot_prompts: dict) -> dict:
    """从 shot_prompts 构建 storyboard.json."""
    shots = []
    for sp in shot_prompts["shots"]:
        camera_hint = sp.get("camera_hint", "")
        codec = _parse_camera_hint(camera_hint)
        shots.append({
            "shot_id": sp["shot_id"],
            "scene_id": "scene-01",
            "segment_mode": "segment-base" if sp["start_second"] == 0 else "segment-extension",
            "purpose": "hook" if sp["start_second"] == 0 else (
                "close" if sp["shot_id"] == shot_prompts["shots"][-1]["shot_id"] else "turn"
            ),
            "start_second": sp["start_second"],
            "end_second": sp["end_second"],
            "visual": sp["prompt"],
            "camera": camera_hint or "镜头语言简洁稳定，优先保证主体可读。",
            "camera_codec": codec,
            "action": "按分镜节奏推进。",
            "audio": "配乐与节奏同步，环境音轻量存在。",
            "assets": ["C01", "S01"],
            "continuity_note": "保持主体、空间和光线连续。" if sp["start_second"] == 0
                else "接续上一段最后一帧的构图与角色状态。",
        })
    return {
        "id": f"storyboard-{brief['id']}",
        "script_id": f"script-{brief['id']}",
        "shots": shots,
    }


# ──────────────────────────────────────────────
# Script 构建
# ──────────────────────────────────────────────

def build_script(brief: dict, shot_prompts: dict) -> dict:
    """从 shot_prompts 构建 script.json."""
    shots = shot_prompts["shots"]
    segments = []
    for i, shot in enumerate(shots):
        seg_id = f"seg-{i+1:02d}"
        dur = int(shot["end_second"] - shot["start_second"])
        segments.append({
            "segment_id": seg_id,
            "purpose": "hook" if i == 0 else ("close" if i == len(shots) - 1 else "turn"),
            "summary": f"分镜 {i+1}/{len(shots)}: {shot['prompt'][:80]}...",
            "emotion": "active",
            "estimated_seconds": dur,
        })
    return {
        "id": f"script-{brief['id']}",
        "brief_id": brief["id"],
        "video_type": brief.get("video_type", "product-demo"),
        "strategy": "five-beat-short-video" if len(shots) <= 5 else "three-phase-segmented-video",
        "title": brief["goal"][:40].rstrip(" ，,。"),
        "logline": f"围绕“{brief['goal']}”生成，LLM 直出 Seedance 分镜提示词。",
        "segments": segments,
        "template_mode": "llm-direct",
        "template_confidence": "high",
    }


# ──────────────────────────────────────────────
# Assets 构建
# ──────────────────────────────────────────────

def build_assets(brief: dict, shot_prompts: dict) -> dict:
    """构建 asset-manifest.json — 基础占位，LLM 直出模式不需要详细 asset 描述."""
    return {
        "id": f"assets-{brief['id']}",
        "storyboard_id": f"storyboard-{brief['id']}",
        "items": [
            {
                "asset_id": "C01",
                "type": "character",
                "name": "视频主体",
                "description": brief["goal"][:60],
                "prompt": f"围绕“{brief['goal']}”的视频主体设计。",
                "required": True,
                "continuity_priority": "high",
            },
            {
                "asset_id": "S01",
                "type": "scene",
                "name": "视频场景",
                "description": brief["goal"][:60],
                "prompt": f"围绕“{brief['goal']}”的场景设计。",
                "required": True,
                "continuity_priority": "medium",
            },
        ],
    }


# ──────────────────────────────────────────────
# Publish 构建
# ──────────────────────────────────────────────

def build_publish(brief: dict) -> dict:
    """构建 publish-job.json."""
    return {
        "id": f"publish-job-{brief['id']}",
        "platform": "douyin",
        "video_path": f"pb-01.mp4",
        "title": brief["goal"][:30].rstrip(" ，,。"),
        "description": f"{brief['goal']}\n\n#短视频",
        "hashtags": ["#短视频"],
        "visibility": "public",
    }


# ──────────────────────────────────────────────
# Review / Ledger
# ──────────────────────────────────────────────

def build_review_decision() -> dict:
    return {"status": "pending-review", "reviewer": "", "approved_at": "", "selected_model": "", "notes": "LLM 直出分镜提示词模式。等待审核。"}


def build_ledger(brief: dict) -> dict:
    ts = now_iso()
    return {
        "id": f"run-{brief['id']}",
        "brief_id": brief["id"],
        "mode": brief.get("mode", "plan-only"),
        "status": "pending-review",
        "current_stage": "pending-review",
        "artifacts": [
            "brief.json", "shot_prompts.json", "script.json", "storyboard.json",
            "asset-manifest.json", "seedance-job.json", "publish-job.json",
            "review-decision.json",
        ],
        "steps": [
            {"name": "llm-shot-prompts", "status": "success", "started_at": ts, "ended_at": ts,
             "artifacts": ["shot_prompts.json"], "notes": "LLM 直出 Seedance 分镜提示词。"},
            {"name": "compile-from-prompts", "status": "success", "started_at": ts, "ended_at": ts,
             "artifacts": ["script.json", "storyboard.json", "asset-manifest.json", "seedance-job.json", "publish-job.json"],
             "notes": "编译器从 shot_prompts 反向编译完整 review package。"},
        ],
    }


def build_review_summary(brief: dict, shot_prompts: dict, seedance: dict) -> str:
    lines = [
        "# Review Summary",
        "",
        "## 当前状态",
        "- 状态：pending-review",
        "- 模式：LLM 直出 Seedance 分镜提示词（llm-direct）",
        "- 说明：LLM 直接写了 Seedance 分镜提示词，编译器负责结构化。",
        "",
        "## Brief",
        f"- 目标：{brief['goal']}",
        f"- 时长：{brief['duration_seconds']}s",
        f"- 比例：{brief['aspect_ratio']}",
        "",
        f"## 分镜提示词 ({len(shot_prompts['shots'])} shots)",
    ]
    for shot in shot_prompts["shots"]:
        lines.append(f"- **{shot['shot_id']}** {shot['start_second']}-{shot['end_second']}s: {shot['prompt'][:120]}...")

    lines += [
        "",
        "## 执行方式",
        "- 批准并选模型：`python scripts/run_pipeline.py --dir <dir> --approve --model doubao-seedance-1-5-pro-251215`",
        "- 批准后生成：`python scripts/run_pipeline.py --dir <dir> --generate --execute`",
    ]
    return "\n".join(lines)


# ──────────────────────────────────────────────
# 主入口
# ──────────────────────────────────────────────

def build_review_package_from_prompts(brief: dict, shot_prompts: dict) -> dict:
    """从 LLM 直出的 shot_prompts 构建完整 review package."""
    seedance = build_seedance_job(brief, shot_prompts)
    storyboard = build_storyboard(brief, shot_prompts)
    script = build_script(brief, shot_prompts)
    assets = build_assets(brief, shot_prompts)
    publish = build_publish(brief)
    review_decision = build_review_decision()
    review_summary = build_review_summary(brief, shot_prompts, seedance)
    ledger = build_ledger(brief)

    return {
        "brief": brief,
        "script": script,
        "storyboard": storyboard,
        "assets": assets,
        "seedance": seedance,
        "publish": publish,
        "review_decision": review_decision,
        "review_summary": review_summary,
        "ledger": ledger,
    }


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Compile review package from LLM shot prompts")
    parser.add_argument("--brief", required=True, help="path to brief.json")
    parser.add_argument("--shot-prompts", required=True, help="path to shot_prompts.json (LLM output)")
    parser.add_argument("--output-dir", required=True, help="output directory")
    args = parser.parse_args()

    brief = load_json(Path(args.brief))
    shot_prompts = load_json(Path(args.shot_prompts))

    # 验证时长一致性
    total = sum(s["end_second"] - s["start_second"] for s in shot_prompts["shots"])
    if abs(total - brief["duration_seconds"]) > 1:
        print(f"WARNING: shot_prompts total duration ({total}s) != brief ({brief['duration_seconds']}s)")

    package = build_review_package_from_prompts(brief, shot_prompts)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    from compiler_render import render_script_md, render_storyboard_md
    package["script_md"] = render_script_md(package["script"], brief)
    package["storyboard_md"] = render_storyboard_md(package["storyboard"], package["seedance"])

    from compile_pipeline import write_json as wj
    wj(output_dir / "brief.json", brief)
    wj(output_dir / "shot_prompts.json", shot_prompts)
    wj(output_dir / "script.json", package["script"])
    wj(output_dir / "storyboard.json", package["storyboard"])
    wj(output_dir / "asset-manifest.json", package["assets"])
    wj(output_dir / "seedance-job.json", package["seedance"])
    wj(output_dir / "publish-job.json", package["publish"])
    wj(output_dir / "review-decision.json", package["review_decision"])
    wj(output_dir / "run-ledger.json", package["ledger"])
    (output_dir / "script.md").write_text(package["script_md"], encoding="utf-8")
    (output_dir / "storyboard.md").write_text(package["storyboard_md"], encoding="utf-8")
    (output_dir / "review-summary.md").write_text(package["review_summary"], encoding="utf-8")

    from validate_artifacts import validate_directory
    issues = validate_directory(output_dir)
    if issues:
        raise SystemExit("\n".join(issues))
    print(f"review package -> {output_dir}")
    print("status: pending-review (llm-direct mode)")


if __name__ == "__main__":
    main()
