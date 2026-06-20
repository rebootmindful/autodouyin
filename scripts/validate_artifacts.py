"""
/**
 * [INPUT]: 依赖 {编译产物目录} 的 {brief/script/storyboard/jobs JSON 文件}
 * [OUTPUT]: 对外提供 {最小本地校验结果}
 * [POS]: {scripts} 的 {契约校验脚本}，用于验证 schema 方向是否自洽
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import jsonschema


FILES = [
    "brief.json",
    "script.json",
    "storyboard.json",
    "asset-manifest.json",
    "seedance-job.json",
    "publish-job.json",
    "run-ledger.json",
]

SCHEMA_MAP = {
    "brief.json": "brief.schema.json",
    "script.json": "script.schema.json",
    "storyboard.json": "storyboard.schema.json",
    "asset-manifest.json": "asset-manifest.schema.json",
    "seedance-job.json": "seedance-job.schema.json",
    "publish-job.json": "publish-job.schema.json",
    "run-ledger.json": "run-ledger.schema.json",
    "review-decision.json": "review-decision.schema.json",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", required=True, help="artifact directory")
    return parser.parse_args()


def load_jsons(directory: Path) -> dict[str, dict]:
    return {
        name: json.loads((directory / name).read_text(encoding="utf-8"))
        for name in FILES
    }


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def schema_path(schema_name: str) -> Path:
    return Path(__file__).parent.parent / "schemas" / schema_name


def validate_json_schema(filename: str, data: dict) -> list[str]:
    schema = load_json(schema_path(SCHEMA_MAP[filename]))
    validator = jsonschema.Draft202012Validator(schema)
    issues = []
    for error in validator.iter_errors(data):
        location = ".".join(str(part) for part in error.absolute_path)
        where = f"{filename}:{location}" if location else filename
        issues.append(f"{where}: {error.message}")
    return issues


def require_keys(data: dict, keys: list[str], name: str) -> list[str]:
    return [f"{name}: missing {key}" for key in keys if key not in data]


def validate_brief(data: dict) -> list[str]:
    keys = ["id", "goal", "platform", "mode", "duration_seconds", "aspect_ratio"]
    issues = require_keys(data, keys, "brief.json")
    if data.get("platform") != "douyin":
        issues.append("brief.json: platform must be douyin")
    return issues


def validate_script(data: dict) -> list[str]:
    issues = require_keys(data, ["id", "brief_id", "video_type", "strategy", "title", "logline", "segments"], "script.json")
    if "template_mode" not in data:
        issues.append("script.json: missing template_mode")
    if "template_confidence" not in data:
        issues.append("script.json: missing template_confidence")
    if not data.get("segments"):
        issues.append("script.json: segments must not be empty")
    return issues


def validate_assets(data: dict) -> list[str]:
    issues = require_keys(data, ["id", "storyboard_id", "items"], "asset-manifest.json")
    asset_ids = [item.get("asset_id", "") for item in data.get("items", [])]
    if not all(asset_id[:1] in {"C", "S", "P"} for asset_id in asset_ids):
        issues.append("asset-manifest.json: asset ids must start with C/S/P")
    for item in data.get("items", []):
        if item.get("asset_id", "").startswith("C") and "continuity_priority" not in item:
            issues.append(f"asset-manifest.json: {item.get('asset_id')} missing continuity_priority")
    return issues


def validate_storyboard(data: dict, assets: dict, brief: dict) -> list[str]:
    issues = require_keys(data, ["id", "script_id", "shots"], "storyboard.json")
    known = {item["asset_id"] for item in assets.get("items", [])}
    total_duration = 0
    for shot in data.get("shots", []):
        if shot["end_second"] <= shot["start_second"]:
            issues.append(f"storyboard.json: {shot['shot_id']} has invalid timing")
        if "scene_id" not in shot:
            issues.append(f"storyboard.json: {shot['shot_id']} missing scene_id")
        if any(asset not in known for asset in shot.get("assets", [])):
            issues.append(f"storyboard.json: {shot['shot_id']} references unknown asset")
        codec = shot.get("camera_codec", {})
        if not all(key in codec for key in ["z", "y", "x", "focal_length_mm", "depth"]):
            issues.append(f"storyboard.json: {shot['shot_id']} camera_codec incomplete")
        total_duration += shot["end_second"] - shot["start_second"]
    expected_duration = brief.get("duration_seconds", 0)
    if expected_duration > 0 and abs(total_duration - expected_duration) > 1:
        issues.append(f"storyboard.json: total shot duration {total_duration}s does not match brief {expected_duration}s")
    return issues


def validate_seedance(data: dict) -> list[str]:
    issues = require_keys(
        data,
        [
            "id",
            "storyboard_id",
            "duration_seconds",
            "aspect_ratio",
            "mode",
            "global_style_anchor",
            "continuity_locks",
            "negative_constraints",
            "slot_plan",
            "video_type",
            "strategy",
            "execution_recommendation",
            "scene_plan",
            "prompt_blocks",
        ],
        "seedance-job.json",
    )
    if "identity_strategy" not in data:
        issues.append("seedance-job.json: missing identity_strategy")
    for block in data.get("prompt_blocks", []):
        duration = block.get("end_second", 0) - block.get("start_second", 0)
        if duration <= 0:
            issues.append(f"seedance-job.json: {block.get('block_id', 'unknown')} has invalid duration")
        if duration < 4:
            issues.append(f"seedance-job.json: {block.get('block_id', 'unknown')} below 4s minimum")
        if duration > 15:
            issues.append(f"seedance-job.json: {block.get('block_id', 'unknown')} exceeds 15s single-generation limit")
    blocks = data.get("prompt_blocks", [])
    if blocks:
        total_block_duration = sum(b.get("end_second", 0) - b.get("start_second", 0) for b in blocks)
        expected = data.get("duration_seconds", 0)
        if expected > 0 and abs(total_block_duration - expected) > 1:
            issues.append(f"seedance-job.json: prompt_blocks total {total_block_duration}s does not match duration_seconds {expected}s")
    if data.get("mode") == "text-image-video" and data.get("duration_seconds", 0) > 15:
        issues.append("seedance-job.json: duration exceeds 15s")
    if data.get("mode") == "segmented-extension":
        if data.get("duration_seconds", 0) <= 15:
            issues.append("seedance-job.json: segmented-extension should exceed 15s")
        if data.get("duration_seconds", 0) > 60:
            issues.append("seedance-job.json: segmented-extension should not be used beyond 60s")
    if data.get("mode") == "scene-split-edit-pipeline" and data.get("duration_seconds", 0) <= 60:
        issues.append("seedance-job.json: scene-split-edit-pipeline should only be used beyond 60s")
    if data.get("mode") == "segmented-extension":
        refs_after_first = [block.get("video_refs", []) for block in data.get("prompt_blocks", [])[1:]]
        if refs_after_first and not any("@视频1" in refs for refs in refs_after_first):
            issues.append("seedance-job.json: segmented-extension blocks should reference @视频1 after first block")
    if data.get("mode") == "scene-split-edit-pipeline":
        scene_plan = data.get("scene_plan", [])
        if not scene_plan:
            issues.append("seedance-job.json: scene-split-edit-pipeline requires scene_plan")
        by_scene = {}
        for block in data.get("prompt_blocks", []):
            scene_id = block.get("scene_id")
            if not scene_id:
                issues.append(f"seedance-job.json: {block.get('block_id', 'unknown')} missing scene_id")
                continue
            by_scene.setdefault(scene_id, []).append(block)
        for scene_id, blocks in by_scene.items():
            first = blocks[0]
            if first.get("video_refs"):
                issues.append(f"seedance-job.json: first block of {scene_id} should not reference @视频1")
            for block in blocks[1:]:
                if "@视频1" not in block.get("video_refs", []):
                    issues.append(f"seedance-job.json: continuation block in {scene_id} should reference @视频1")
    rec = data.get("execution_recommendation", {})
    if not all(key in rec for key in [
        "video_type",
        "hard_single_generation_range_seconds",
        "official_ui_recommended_range_seconds",
        "fastest_test_window_seconds",
        "fastest_practical_window_seconds",
        "stable_expression_window_seconds",
        "default_duration_seconds_for_type",
        "max_single_generation_seconds",
        "scene_split_recommended_after_seconds",
        "suggested_split_strategy",
        "requested_duration_seconds",
    ]):
        issues.append("seedance-job.json: execution_recommendation incomplete")
    return issues


def validate_publish(data: dict) -> list[str]:
    keys = ["id", "platform", "video_path", "title", "description"]
    issues = require_keys(data, keys, "publish-job.json")
    if data.get("platform") != "douyin":
        issues.append("publish-job.json: platform must be douyin")
    return issues


def validate_ledger(data: dict) -> list[str]:
    issues = require_keys(data, ["id", "brief_id", "mode", "steps", "status", "artifacts"], "run-ledger.json")
    if not data.get("steps"):
        issues.append("run-ledger.json: steps must not be empty")
    return issues


def validate_review_decision(data: dict) -> list[str]:
    issues = require_keys(data, ["status", "reviewer", "approved_at", "selected_model", "notes"], "review-decision.json")
    status = data.get("status")
    if status == "approved" and not data.get("approved_at"):
        issues.append("review-decision.json: approved status requires approved_at")
    if status == "approved" and not data.get("selected_model"):
        issues.append("review-decision.json: approved status requires selected_model")
    return issues


def validate_content_non_empty(data: dict) -> list[str]:
    issues = []
    script = data.get("script.json", {})
    if not script.get("logline"):
        issues.append("script.json: logline must not be empty")
    for seg in script.get("segments", []):
        if not seg.get("summary"):
            issues.append(f"script.json: {seg.get('segment_id', '?')} summary must not be empty")
    sb = data.get("storyboard.json", {})
    for shot in sb.get("shots", []):
        for field in ("visual", "camera", "action", "audio"):
            if not shot.get(field):
                issues.append(f"storyboard.json: {shot.get('shot_id', '?')} {field} must not be empty")
    assets = data.get("asset-manifest.json", {})
    for item in assets.get("items", []):
        for field in ("name", "description", "prompt"):
            if not item.get(field):
                issues.append(f"asset-manifest.json: {item.get('asset_id', '?')} {field} must not be empty")
    seedance = data.get("seedance-job.json", {})
    for block in seedance.get("prompt_blocks", []):
        if not block.get("prompt"):
            issues.append(f"seedance-job.json: {block.get('block_id', '?')} prompt must not be empty")
    return issues


def validate_timeline_continuity(data: dict) -> list[str]:
    issues = []
    sb = data.get("storyboard.json", {})
    shots = sb.get("shots", [])
    for i in range(1, len(shots)):
        prev_end = shots[i - 1]["end_second"]
        curr_start = shots[i]["start_second"]
        if curr_start < prev_end:
            issues.append(f"storyboard.json: {shots[i]['shot_id']} overlaps with previous shot")
        if curr_start > prev_end:
            issues.append(f"storyboard.json: gap between {shots[i-1]['shot_id']} and {shots[i]['shot_id']}")
    return issues


VALID_Z = {f"Z{i}" for i in range(1, 10)}
VALID_Y = {f"Y{i}" for i in range(1, 8)}
VALID_X = {f"X{i}" for i in range(1, 5)}
VALID_FOCAL = {18, 24, 35, 50, 85, 135}
VALID_DEPTH = {"shallow", "medium", "deep"}


def validate_camera_codec_values(data: dict) -> list[str]:
    issues = []
    for shot in data.get("storyboard.json", {}).get("shots", []):
        codec = shot.get("camera_codec", {})
        sid = shot.get("shot_id", "?")
        if codec.get("z") and codec["z"] not in VALID_Z:
            issues.append(f"storyboard.json: {sid} invalid z={codec['z']}")
        if codec.get("y") and codec["y"] not in VALID_Y:
            issues.append(f"storyboard.json: {sid} invalid y={codec['y']}")
        if codec.get("x") and codec["x"] not in VALID_X:
            issues.append(f"storyboard.json: {sid} invalid x={codec['x']}")
        fl = codec.get("focal_length_mm")
        if fl and fl not in VALID_FOCAL:
            issues.append(f"storyboard.json: {sid} non-standard focal_length_mm={fl}")
        d = codec.get("depth")
        if d and d not in VALID_DEPTH:
            issues.append(f"storyboard.json: {sid} invalid depth={d}")
    return issues


def validate_style_consistency(data: dict) -> list[str]:
    issues = []
    brief = data.get("brief.json", {})
    seedance = data.get("seedance-job.json", {})
    preset = brief.get("aesthetic_preset")
    if not preset:
        return issues
    anchor = seedance.get("global_style_anchor", "")
    if not anchor:
        issues.append("seedance-job.json: global_style_anchor is empty but aesthetic_preset is set")
    presets_path = Path(__file__).parent.parent / "references" / "aesthetic-presets.json"
    if not presets_path.exists():
        return issues
    presets = json.loads(presets_path.read_text(encoding="utf-8"))
    preset_data = presets.get("presets", {}).get(preset)
    if not preset_data:
        return issues
    keywords = preset_data.get("visual_keywords", [])
    if keywords and anchor and not any(kw.lower() in anchor.lower() for kw in keywords):
        issues.append(f"seedance-job.json: global_style_anchor does not reflect preset '{preset}' keywords")
    return issues


def validate_directory(directory: Path) -> list[str]:
    data = load_jsons(directory)
    review_path = directory / "review-decision.json"
    review_data = load_json(review_path) if review_path.exists() else None
    issues = []
    for filename, payload in data.items():
        issues.extend(validate_json_schema(filename, payload))
    if review_data is not None:
        issues.extend(validate_json_schema("review-decision.json", review_data))
    issues.extend(validate_brief(data["brief.json"]))
    issues.extend(validate_script(data["script.json"]))
    issues.extend(validate_assets(data["asset-manifest.json"]))
    issues.extend(validate_storyboard(data["storyboard.json"], data["asset-manifest.json"], data["brief.json"]))
    issues.extend(validate_seedance(data["seedance-job.json"]))
    issues.extend(validate_publish(data["publish-job.json"]))
    issues.extend(validate_ledger(data["run-ledger.json"]))
    if review_data is not None:
        issues.extend(validate_review_decision(review_data))
    issues.extend(validate_content_non_empty(data))
    issues.extend(validate_timeline_continuity(data))
    issues.extend(validate_camera_codec_values(data))
    issues.extend(validate_style_consistency(data))
    return issues


def main() -> None:
    directory = Path(parse_args().dir)
    issues = validate_directory(directory)
    if issues:
        raise SystemExit("\n".join(issues))
    print("artifacts are valid")


if __name__ == "__main__":
    main()
