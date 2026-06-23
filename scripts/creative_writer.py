"""
/**
 * [INPUT]: 依赖 {brief.json 与 creative-content.schema.json} 的 {创作需求}
 * [OUTPUT]: 对外提供 {creative writing prompt + creative_content.json 模板}
 * [POS]: {scripts} 的 {LLM 创作层入口}，桥接确定性结构与 LLM 想象力
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 *
 * 两种模式:
 *   --prompt   → 输出结构化创作提示，引导 LLM 发挥想象力
 *   --template → 输出 creative_content.json 空模板，供 LLM 填充
 *
 * 设计原则:
 *   1. 角色先行 — 先创造角色（谁、什么性格、什么关系），剧情自然生长
 *   2. 约束即燃料 — 用 brief 的具体约束聚焦创作，不是限制
 *   3. 情绪曲线 — 给情绪变化，不给信息清单
 *   4. 视觉语言 — 用 Seedance 可理解的视觉描述，不是抽象概念
 *   5. Few-shot — 模板本身即是范例，展示"好的创作长什么样"
 */
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "schemas" / "creative-content.schema.json"

# ── 按视频类型的创作方法论 ──

_METHODOLOGY_COMMON = """
## 创作方法论

你是短视频编剧+导演。不要翻译 brief 为画面清单——用 {duration} 秒讲一个让人看完想行动的小故事。

### 通用规则

- **情绪曲线驱动，不是信息清单驱动**：按"建立→冲突→反转→释放"结构，每段标注 X→Y 情绪变化。
- **视觉即叙事**：用 Seedance 可理解的视觉语言——空间、光线、材质、动作、色彩。不写抽象概念。
- **约束即燃料**：brief 里的限制越具体，创作越聚焦。空白画布产出陈词滥调。
"""

_METHODOLOGY_PRODUCT_DEMO = """
### 产品演示专属

- **产品是主角，赋予它性格**：花盆不只是花盆——它是一个会饿、会渴、会开心的小东西。找到产品的"人格"。
- **展示变化，不是展示功能**：不要列"材质陶瓷、LED屏幕、蓝牙连接"。展示"从😰到😊的那一瞬间"。
- **让观众渴望那个变化**：看完视频，观众应该想"我也想让我的植物这么开心"，而不是"这个产品有LED屏"。
- **slogan 是情绪的落点**：让 slogan 出现在情绪最高点，不是在黑屏上飘一行字。
"""

_METHODOLOGY_CHARACTER_ACTION = """
### 角色驱动专属

- **角色先行，不是信息先行**：先创造 1-2 个有辨识度的角色。谁？什么性格？什么关系？角色必须有缺陷或欲望。
- **对白揭示角色，不是解释信息**：每句 ≤15 字，留停顿空间让画面呼吸。用角色的嘴说出故事，不是用旁白。
- **反转是高潮，不是附录**：最好的 3 秒放在最后——那个让人想转发、想评论、想@好友的瞬间。
"""

_METHODOLOGY_NARRATIVE = """
### 剧情叙事专属

- **情绪弧线是第一结构**：从什么状态开始 → 经历什么转折 → 落到什么新状态。不是三段式，是抛物线。
- **留白比填满更有力**：不解释每一个变化。让镜头、光线、表情说话。
- **结尾是释放，不是总结**：不要"这个故事告诉我们……"。停在最有张力的那一帧。
"""

_METHODOLOGY_WORKFLOW = """
### 信息演示专属

- **结果先行**：第一秒就让观众看到最终效果，再倒推展示过程。
- **信息层次，不是信息堆砌**：每个镜头只传达一个关键变化。before/after 的对比比文字更有力。
- **节奏 = 信任**：快不等于有信息量。关键帧留 0.5s 让眼睛注册。
"""

_METHODOLOGY_SPACE_TOUR = """
### 空间漫游专属

- **路径即叙事**：观众跟着镜头走一条有情绪起伏的路线，不是随机漫游。
- **材质和光线是主角**：frosted glass 的散射、titanium 的反光、morning light 的角度——这些比"空间很大"重要 100 倍。
- **停在有呼吸感的地方**：最后一个镜头应该是让人想截图的画面。
"""

_CTA_CLOSING = """
### 收尾

- 让 CTA 成为故事的自然落点，不是贴上去的按钮。
- 最后一个镜头留 2-3 秒给观众反应——然后才出现行动号召。
"""


def _methodology_for(brief: dict) -> str:
    """根据 video_type 返回对应的方法论."""
    vt = brief.get("video_type", "")
    duration = brief.get("duration_seconds", 15)
    common = _METHODOLOGY_COMMON.format(duration=duration)

    if vt == "product-demo":
        return common + _METHODOLOGY_PRODUCT_DEMO + _CTA_CLOSING
    elif vt == "character-action":
        return common + _METHODOLOGY_CHARACTER_ACTION + _CTA_CLOSING
    elif vt == "narrative-story":
        return common + _METHODOLOGY_NARRATIVE + _CTA_CLOSING
    elif vt == "workflow-explainer":
        return common + _METHODOLOGY_WORKFLOW + _CTA_CLOSING
    elif vt == "space-tour":
        return common + _METHODOLOGY_SPACE_TOUR + _CTA_CLOSING
    else:
        return common + _CTA_CLOSING


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Creative writing prompt generator")
    parser.add_argument("--brief", help="path to brief.json")
    parser.add_argument("--prompt", action="store_true", help="output creative writing prompt")
    parser.add_argument("--direct", action="store_true", help="output Seedance-native shot prompt guide (LLM writes prompts directly)")
    parser.add_argument("--template", action="store_true", help="output creative_content.json template")
    parser.add_argument("--output", help="write shot_prompts.json template to file")
    return parser.parse_args()


def load_brief(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def build_prompt(brief: dict) -> str:
    """生成激发 LLM 想象力的创作提示."""
    goal = brief["goal"]
    duration = brief["duration_seconds"]
    ratio = brief["aspect_ratio"]
    audience = brief.get("audience", "广泛受众")
    style = brief.get("style", "")
    tone = brief.get("tone", "")
    video_type = brief.get("video_type", "")
    must_include = brief.get("must_include", [])
    must_avoid = brief.get("must_avoid", [])
    preset = brief.get("aesthetic_preset", "")

    include_lines = "\n".join(f"  - {item}" for item in must_include) if must_include else "  - (无特殊要求)"
    avoid_lines = "\n".join(f"  - {item}" for item in must_avoid) if must_avoid else "  - (无特殊限制)"

    return f"""# 短视频创作任务

## 技术约束
- 时长: {duration}s
- 比例: {ratio}
- 类型: {video_type}
- 美学预设: {preset}
- 目标受众: {audience}

## 创作目标
{goal}

## 风格基调
- 风格: {style}
- 语调: {tone}

## 必须包含
{include_lines}

## 必须避免
{avoid_lines}

{_methodology_for(brief)}

## 输出格式

请输出符合 `schemas/creative-content.schema.json` 的 JSON。
写进 `creative_content.json`，放在产物目录里。

关键字段:
- `creative_direction`: 一句话，你给这条视频的创作方向是什么
- `characters[]`: 每个角色的名字、性格、外观、说话风格、角色弧线
- `scenes[]`: 每个场景的空间、情绪、关键道具
- `segments[]`: 每段的情绪曲线、节奏点名、对白（含表演提示）
- `shots[]`: 每个镜头的核心视觉描述和镜头建议
- `cta_moment`: CTA 如何作为剧情的自然终点出现
"""


_DIRECT_METHODOLOGY = """
## Seedance 分镜提示词写作指南

你是 Seedance 视频提示词专家。像豆包那样，直接写一镜一镜的提示词。不要翻译 brief —— 用 Seedance 的视觉语言创造画面。

### 写作规则

1. **每镜开头声明格式**: "{ratio}竖屏，{preset}风格。"
2. **描述画面里有什么**: 主体、空间、光线、色彩、材质。用名词和形容词，不用抽象概念。
3. **描述在发生什么**: 动作、变化、情绪。展示，不要说明。
4. **镜头运动**: 推/拉/摇/跟/固定。写进画面描述里，不要单独列。
5. **不要写的**: 字幕、LOGO、文字、UI 元素 — 这些后期叠加。
6. **每镜 80-200 字**: 足够让 Seedance 理解画面，但不过度约束。
7. **camera_hint 可选**: 如 "中景推进 Z5 Y4 X2 50mm"。不写也没关系，编译器补默认值。

### 示例 (product-demo, 15s, 3 shots)

shot-01 (0-5s):
"9:16竖屏，apple-cupertino风格。白色陶瓷智能花盆置于titanium质感桌面中央，一株绿萝从盆沿垂下。花盆正面圆形LED屏显示😰表情，柔和的红色脉冲光在frosted glass背景上投出微光。镜头从远景缓推至中景。"

shot-02 (5-10s):
"一只手从画外右侧伸入，修长手指握着透明玻璃水壶，倾斜——水柱落入深褐色土壤。LED屏的😰开始闪烁，红光渐变成温暖的绿色。绿萝叶片微微颤动，仿佛在呼吸。镜头推进至花盆LED屏特写，shallow景深。"

shot-03 (10-15s):
"😊表情在LED屏上稳定亮起，柔和的绿光照亮花盆周围的空气。镜头缓慢拉远——露出整张桌面，花盆旁出现手机屏幕（显示App界面，植物状态'已浇水'）。画面定格，留白空间供后期叠加slogan。"
"""


def build_direct_prompt(brief: dict) -> str:
    """生成 Seedance-native 分镜提示词引导."""
    duration = brief["duration_seconds"]
    ratio = brief["aspect_ratio"]
    preset = brief.get("aesthetic_preset", "")
    must_include = brief.get("must_include", [])
    must_avoid = brief.get("must_avoid", [])

    include_lines = "\n".join(f"  - {item}" for item in must_include) if must_include else "  - (无特殊要求)"
    avoid_lines = "\n".join(f"  - {item}" for item in must_avoid) if must_avoid else "  - (无特殊限制)"

    # 建议分镜数
    if duration <= 8:
        suggested_shots = "1-2"
    elif duration <= 15:
        suggested_shots = "2-3"
    else:
        suggested_shots = "3-5"

    return f"""# Seedance 分镜提示词写作

## 技术约束
- 时长: {duration}s
- 比例: {ratio}
- 美学预设: {preset}
- 建议分镜数: {suggested_shots} shots

## 创作目标
{brief['goal']}

## 风格基调
- 风格: {brief.get('style', '')}
- 语调: {brief.get('tone', '')}

## 必须包含
{include_lines}

## 必须避免
{avoid_lines}

{_DIRECT_METHODOLOGY}

## 输出格式

请输出符合 `schemas/shot-prompts.schema.json` 的 JSON。写进 `shot_prompts.json`。

字段:
- `creative_direction`: 一句话创作方向
- `shots[]`: 分镜数组
  - `shot_id`: "shot-01", "shot-02"...
  - `start_second` / `end_second`: 时间范围
  - `prompt`: Seedance 原生提示词（最重要！）
  - `camera_hint`: 可选镜头建议

注意: 你的 prompt 字段会直接喂给 Seedance API。写你最好的视觉语言。
"""


def generate_shot_prompts_template(brief: dict, output_path: str | None = None) -> dict:
    """生成 shot_prompts.json 空模板."""
    duration = brief["duration_seconds"]
    if duration <= 8:
        shot_count = 2
    elif duration <= 15:
        shot_count = 3
    else:
        shot_count = min(5, max(3, duration // 8))

    shot_dur = duration / shot_count
    shots = []
    for i in range(shot_count):
        start = round(i * shot_dur, 1)
        end = round((i + 1) * shot_dur, 1) if i < shot_count - 1 else duration
        shots.append({
            "shot_id": f"shot-{i+1:02d}",
            "start_second": start,
            "end_second": end,
            "prompt": "",
            "camera_hint": "",
        })

    template = {
        "id": f"shot-prompts-{brief['id']}",
        "brief_id": brief["id"],
        "generated_by": "",
        "creative_direction": "",
        "shots": shots,
    }

    if output_path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(template, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"shot_prompts template -> {path}")

    return template


def generate_template(brief: dict, output_path: str | None = None) -> dict:
    """生成 creative_content.json 空模板，引导 LLM 填入创意."""
    goal = brief["goal"]
    duration = brief["duration_seconds"]

    # 根据时长估计分段数
    if duration <= 15:
        seg_count = 2
    elif duration <= 30:
        seg_count = 3
    else:
        seg_count = max(3, duration // 15 + 1)

    seg_ids = [f"seg-{i+1:02d}" for i in range(seg_count)]
    shot_ids = [f"shot-{i+1:02d}" for i in range(seg_count)]
    char_ids = ["C01", "C02"]
    scene_ids = ["S01"]

    template = {
        "id": f"creative-{brief['id']}",
        "brief_id": brief["id"],
        "generated_by": "",  # LLM fills this
        "creative_direction": "",  # LLM fills: one-line creative vision
        "characters": [
            {
                "asset_id": char_ids[0],
                "name": "",
                "role": "",
                "personality": "",
                "appearance": "",
                "voice_style": "",
                "arc": "",
            },
            {
                "asset_id": char_ids[1],
                "name": "",
                "role": "",
                "personality": "",
                "appearance": "",
                "voice_style": "",
                "arc": "",
            },
        ],
        "scenes": [
            {
                "asset_id": scene_ids[0],
                "name": "",
                "setting": "",
                "mood": "",
                "key_props": [],
            }
        ],
        "segments": [
            {
                "segment_id": seg_ids[i],
                "emotion_curve": "",
                "beat_name": "",
                "dialogue": [],
            }
            for i in range(seg_count)
        ],
        "shots": [
            {
                "shot_id": shot_ids[i],
                "visual_core": "",
                "camera_style": "",
                "key_moment": "",
            }
            for i in range(seg_count)
        ],
        "cta_moment": {
            "timing_seconds": "",
            "visual": "",
            "text": "",
        },
    }

    if output_path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(template, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"template -> {path}")

    return template


def main() -> None:
    args = parse_args()
    if not args.brief:
        raise SystemExit("need --brief <brief.json>")

    brief = load_brief(args.brief)

    if args.direct:
        if args.output:
            generate_shot_prompts_template(brief, args.output)
        print(build_direct_prompt(brief))
    elif args.prompt:
        print(build_prompt(brief))
    elif args.template or args.output:
        template = generate_template(brief, args.output)
        if args.template:
            print(json.dumps(template, ensure_ascii=False, indent=2))
    else:
        print(build_prompt(brief))


if __name__ == "__main__":
    main()
