"""
/**
 * [INPUT]: 依赖 {brief 与脚本编译流程} 的 {视频类型、策略与时长规则}
 * [OUTPUT]: 对外提供 {视频类型推断、编译策略、执行时长建议}
 * [POS]: {scripts} 的 {类型与策略模块}，服务编译器拆分后的决策层
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */
"""

from __future__ import annotations


VIDEO_TYPES = [
    "workflow-explainer",
    "product-demo",
    "narrative-story",
    "character-action",
    "space-tour",
]


def duration_mode(brief: dict) -> str:
    duration = brief["duration_seconds"]
    if duration <= 15:
        return "short-single"
    if duration <= 60:
        return "long-segmented"
    return "scene-split"


def infer_video_type(brief: dict) -> str:
    if brief.get("video_type") in VIDEO_TYPES:
        return brief["video_type"]
    goal = brief["goal"]
    if any(word in goal for word in ["广告", "产品", "应用", "UI", "功能"]):
        return "product-demo"
    if any(word in goal for word in ["空间", "参观", "室内", "展厅", "样板间"]):
        return "space-tour"
    if any(word in goal for word in ["战斗", "打斗", "角色", "动作", "变身"]):
        return "character-action"
    if any(word in goal for word in ["故事", "剧情", "短剧", "冲突", "情节"]):
        return "narrative-story"
    return "workflow-explainer"


def strategy_name(brief: dict) -> str:
    mode = duration_mode(brief)
    if mode == "short-single":
        return "five-beat-short-video"
    if mode == "long-segmented":
        return "three-phase-segmented-video"
    return "scene-split-edit-pipeline"


def video_type_duration_profile(video_type: str) -> dict:
    profiles = {
        "workflow-explainer": {
            "default_duration_seconds": 15,
            "fastest_practical_window_seconds": [5, 8],
            "stable_expression_window_seconds": [8, 12],
        },
        "product-demo": {
            "default_duration_seconds": 8,
            "fastest_practical_window_seconds": [5, 8],
            "stable_expression_window_seconds": [6, 10],
        },
        "narrative-story": {
            "default_duration_seconds": 15,
            "fastest_practical_window_seconds": [6, 8],
            "stable_expression_window_seconds": [8, 12],
        },
        "character-action": {
            "default_duration_seconds": 10,
            "fastest_practical_window_seconds": [5, 8],
            "stable_expression_window_seconds": [6, 10],
        },
        "space-tour": {
            "default_duration_seconds": 12,
            "fastest_practical_window_seconds": [6, 8],
            "stable_expression_window_seconds": [8, 12],
        },
    }
    return profiles[video_type]


def execution_recommendation(brief: dict) -> dict:
    duration = brief["duration_seconds"]
    video_type = infer_video_type(brief)
    profile = video_type_duration_profile(video_type)
    if duration <= 15:
        split = "single-generation"
    elif duration <= 30:
        split = "2 segments preferred"
    elif duration <= 45:
        split = "3 segments preferred"
    elif duration <= 60:
        split = "4 segments preferred"
    else:
        split = "split into independent scenes, then edit"
    return {
        "video_type": video_type,
        "hard_single_generation_range_seconds": [4, 15],
        "official_ui_recommended_range_seconds": [5, 12],
        "fastest_test_window_seconds": [4, 5],
        "fastest_practical_window_seconds": profile["fastest_practical_window_seconds"],
        "stable_expression_window_seconds": profile["stable_expression_window_seconds"],
        "default_duration_seconds_for_type": profile["default_duration_seconds"],
        "max_single_generation_seconds": 15,
        "scene_split_recommended_after_seconds": 60,
        "suggested_split_strategy": split,
        "requested_duration_seconds": duration,
    }


def infer_aesthetic_preset(brief: dict) -> str:
    if brief.get("aesthetic_preset"):
        return brief["aesthetic_preset"]
    text = f"{brief.get('style', '')} {brief.get('goal', '')}"
    preset_keywords = {
        "apple-cupertino": ["旗舰", "高端", "apple", "苹果", "钛", "premium"],
        "microsoft-fluent": ["生产力", "办公", "microsoft", "微软", "协作", "SaaS", "效率"],
        "vercel-dark": ["开发者", "dev", "vercel", "暗色", "dark mode", "终端", "代码", "黑客"],
        "bauhaus-zen": ["极简", "禅", "bauhaus", "包豪斯", "留白", "功能"],
    }
    for preset, keywords in preset_keywords.items():
        if any(kw in text for kw in keywords):
            return preset
    video_type = infer_video_type(brief)
    type_default = {
        "product-demo": "apple-cupertino",
        "character-action": "vercel-dark",
        "space-tour": "bauhaus-zen",
    }
    return type_default.get(video_type, "bauhaus-zen")


def split_lengths(total: int, count: int) -> list[int]:
    base, extra = divmod(total, count)
    return [base + (1 if i < extra else 0) for i in range(count)]


def generation_block_lengths(total: int) -> list[int]:
    if total <= 15:
        return [total]
    count = -(-total // 15)
    blocks = split_lengths(total, count)
    while max(blocks) > 15:
        count += 1
        blocks = split_lengths(total, count)
    return blocks
