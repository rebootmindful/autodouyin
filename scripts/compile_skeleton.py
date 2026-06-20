"""
/**
 * [INPUT]: 依赖 {标准化 brief} 的 {视频类型、策略与时长规则}
 * [OUTPUT]: 对外提供 {skeleton.json 结构骨架，内容字段为空}
 * [POS]: {scripts} 的 {骨架生成器}，Layer 1 结构层的核心产出
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from compiler_types import (
    duration_mode,
    execution_recommendation,
    generation_block_lengths,
    infer_aesthetic_preset,
    infer_video_type,
    split_lengths,
    strategy_name,
)

CODEC_DEFAULTS = {
    "hook":            {"z": "Z4", "y": "Y4", "x": "X1", "focal_length_mm": 35, "depth": "shallow"},
    "setup":           {"z": "Z5", "y": "Y4", "x": "X2", "focal_length_mm": 50, "depth": "medium"},
    "turn":            {"z": "Z5", "y": "Y4", "x": "X2", "focal_length_mm": 50, "depth": "medium"},
    "payoff":          {"z": "Z3", "y": "Y4", "x": "X2", "focal_length_mm": 85, "depth": "shallow"},
    "close":           {"z": "Z6", "y": "Y4", "x": "X4", "focal_length_mm": 50, "depth": "medium"},
    "world-build":     {"z": "Z7", "y": "Y4", "x": "X2", "focal_length_mm": 50, "depth": "deep"},
    "change-push":     {"z": "Z5", "y": "Y4", "x": "X2", "focal_length_mm": 50, "depth": "medium"},
    "setup-flow":      {"z": "Z5", "y": "Y4", "x": "X2", "focal_length_mm": 50, "depth": "medium"},
    "peak-moment":     {"z": "Z3", "y": "Y4", "x": "X2", "focal_length_mm": 85, "depth": "shallow"},
    "emotional-close": {"z": "Z6", "y": "Y4", "x": "X4", "focal_length_mm": 50, "depth": "medium"},
}

SHORT_PURPOSES = ["hook", "setup", "turn", "payoff", "close"]

# Seedance 平台硬限制：每个 block 4-15s
MIN_BLOCK_DURATION = 4


def short_purposes(duration: int) -> list[str]:
    return ["hook", "payoff"] if duration <= 4 else SHORT_PURPOSES


def build_script_skeleton(brief: dict) -> dict:
    duration = brief["duration_seconds"]
    mode = duration_mode(brief)
    if mode == "short-single":
        purposes = short_purposes(duration)
        lengths = split_lengths(duration, len(purposes))
        segments = [
            {"segment_id": f"seg-{i+1:02d}", "purpose": p, "summary": "", "emotion": "", "estimated_seconds": s}
            for i, (p, s) in enumerate(zip(purposes, lengths))
        ]
    elif duration <= 60:
        phases = [("world-build", ""), ("change-push", ""), ("emotional-close", "")]
        lengths = split_lengths(duration, len(phases))
        segments = [
            {"segment_id": f"seg-{i+1:02d}", "purpose": p, "summary": "", "emotion": "", "estimated_seconds": s}
            for i, ((p, _), s) in enumerate(zip(phases, lengths))
        ]
    else:
        phases = [("world-build", ""), ("setup-flow", ""), ("change-push", ""), ("peak-moment", ""), ("emotional-close", "")]
        lengths = split_lengths(duration, len(phases))
        segments = [
            {"segment_id": f"seg-{i+1:02d}", "purpose": p, "summary": "", "emotion": "", "estimated_seconds": s}
            for i, ((p, _), s) in enumerate(zip(phases, lengths))
        ]
    return {
        "id": "script-local-001",
        "brief_id": brief["id"],
        "video_type": infer_video_type(brief),
        "strategy": strategy_name(brief),
        "title": brief["goal"][:40],
        "logline": "",
        "segments": segments,
    }


def segment_times(segments: list[dict]) -> list[tuple[int, int]]:
    start = 0
    result = []
    for seg in segments:
        end = start + seg["estimated_seconds"]
        result.append((start, end))
        start = end
    return result


def build_storyboard_skeleton(brief: dict, script: dict) -> dict:
    mode = duration_mode(brief)
    timings = segment_times(script["segments"])
    shots = []
    idx = 1
    for seg, (t0, t1) in zip(script["segments"], timings):
        scene_id = f"scene-{len(shots)+1:02d}"
        codec = CODEC_DEFAULTS.get(seg["purpose"], CODEC_DEFAULTS["setup"])
        if mode == "short-single":
            shots.append(_make_shot(idx, scene_id, "single-sequence", seg["purpose"], t0, t1, codec))
            idx += 1
        elif mode == "long-segmented":
            seg_mode = "segment-base" if idx == 1 else "segment-extension"
            shots.append(_make_shot(idx, scene_id, seg_mode, seg["purpose"], t0, t1, codec))
            idx += 1
        else:
            blocks = generation_block_lengths(seg["estimated_seconds"])
            cursor = t0
            for bi, bl in enumerate(blocks):
                sm = "scene-base" if bi == 0 else "scene-extension"
                shots.append(_make_shot(idx, scene_id, sm, seg["purpose"], cursor, cursor + bl, codec))
                cursor += bl
                idx += 1
    return {"id": "storyboard-local-001", "script_id": script["id"], "shots": shots}


def _make_shot(idx: int, scene_id: str, seg_mode: str, purpose: str,
               t0: int, t1: int, codec: dict) -> dict:
    return {
        "shot_id": f"shot-{idx:02d}",
        "scene_id": scene_id,
        "segment_mode": seg_mode,
        "purpose": purpose,
        "start_second": t0,
        "end_second": t1,
        "visual": "",
        "camera": "",
        "camera_codec": dict(codec),
        "action": "",
        "audio": "",
        "assets": ["C01", "S01", "P01"],
        "continuity_note": "",
    }


def build_assets_skeleton(brief: dict) -> dict:
    return {
        "id": "assets-local-001",
        "storyboard_id": "storyboard-local-001",
        "items": [
            {"asset_id": "C01", "type": "character", "name": "", "description": "", "prompt": "", "required": True},
            {"asset_id": "S01", "type": "scene",     "name": "", "description": "", "prompt": "", "required": True},
            {"asset_id": "P01", "type": "prop",      "name": "", "description": "", "prompt": "", "required": True},
        ],
    }


def build_seedance_skeleton(brief: dict, storyboard: dict) -> dict:
    mode = duration_mode(brief)
    blocks = []
    for i, shot in enumerate(storyboard["shots"]):
        video_refs = [] if shot["segment_mode"] in {"segment-base", "scene-base", "single-sequence"} else ["@视频1"]
        blocks.append({
            "block_id": f"pb-{i+1:02d}",
            "scene_id": shot["scene_id"],
            "mode": shot["segment_mode"],
            "start_second": shot["start_second"],
            "end_second": shot["end_second"],
            "prompt": "",
            "image_refs": ["@图片1", "@图片2", "@图片3"],
            "video_refs": video_refs,
            "audio_refs": [],
        })
    scene_plan = []
    if mode == "scene-split":
        seen = []
        for shot in storyboard["shots"]:
            if shot["scene_id"] not in seen:
                seen.append(shot["scene_id"])
        for sid in seen:
            ss = [s for s in storyboard["shots"] if s["scene_id"] == sid]
            scene_plan.append({"scene_id": sid, "start_second": ss[0]["start_second"], "end_second": ss[-1]["end_second"], "edit_join": "post-edit bridge"})
    mode_str = "text-image-video" if mode == "short-single" else ("segmented-extension" if mode == "long-segmented" else "scene-split-edit-pipeline")
    return {
        "id": "seedance-job-local-001",
        "storyboard_id": storyboard["id"],
        "duration_seconds": brief["duration_seconds"],
        "aspect_ratio": brief["aspect_ratio"],
        "mode": mode_str,
        "global_style_anchor": "",
        "continuity_locks": [],
        "negative_constraints": [],
        "slot_plan": [
            {"ref": "@图片1", "asset_id": "C01", "usage": "主体一致性参考"},
            {"ref": "@图片2", "asset_id": "S01", "usage": "场景或空间背景参考"},
            {"ref": "@图片3", "asset_id": "P01", "usage": "关键道具、结果卡片或动作强化参考"},
        ],
        "video_type": infer_video_type(brief),
        "strategy": strategy_name(brief),
        "execution_recommendation": execution_recommendation(brief),
        "scene_plan": scene_plan,
        "prompt_blocks": blocks,
    }


def build_publish_skeleton(script: dict) -> dict:
    return {
        "id": "publish-job-local-001",
        "platform": "douyin",
        "video_path": "artifacts/output-video.mp4",
        "title": "",
        "description": "",
        "hashtags": [],
        "visibility": "public",
    }


def merge_short_segments(segments: list[dict]) -> list[dict]:
    """Merge adjacent segments whose duration < MIN_BLOCK_DURATION.

    Repeatedly merge the first short segment into its right neighbor
    until all segments meet the minimum. Re-indexes after merging.
    """
    if not segments:
        return segments
    merged = [dict(s) for s in segments]
    changed = True
    while changed:
        changed = False
        new_merged = []
        i = 0
        while i < len(merged):
            dur = merged[i]["estimated_seconds"]
            if dur < MIN_BLOCK_DURATION and i + 1 < len(merged):
                combined = dict(merged[i + 1])
                combined["estimated_seconds"] = dur + merged[i + 1]["estimated_seconds"]
                new_merged.append(combined)
                changed = True
                i += 2
            else:
                new_merged.append(dict(merged[i]))
                i += 1
        merged = new_merged
    # Tail fix: if the last segment is still short, merge it leftward
    if len(merged) >= 2 and merged[-1]["estimated_seconds"] < MIN_BLOCK_DURATION:
        merged[-2]["estimated_seconds"] += merged[-1]["estimated_seconds"]
        merged.pop()
    for i, seg in enumerate(merged):
        seg["segment_id"] = f"seg-{i+1:02d}"
    return merged


def build_skeleton(brief: dict) -> dict:
    script = build_script_skeleton(brief)
    script["segments"] = merge_short_segments(script["segments"])
    storyboard = build_storyboard_skeleton(brief, script)
    return {
        "brief": brief,
        "script": script,
        "storyboard": storyboard,
        "assets": build_assets_skeleton(brief),
        "seedance": build_seedance_skeleton(brief, storyboard),
        "publish": build_publish_skeleton(script),
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--brief", required=True, help="normalized brief path")
    p.add_argument("--output-dir", required=True, help="skeleton output dir")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    brief = json.loads(Path(args.brief).read_text(encoding="utf-8"))
    skeleton = build_skeleton(brief)
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "skeleton.json").write_text(json.dumps(skeleton, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"skeleton written to {out / 'skeleton.json'}")


if __name__ == "__main__":
    main()
