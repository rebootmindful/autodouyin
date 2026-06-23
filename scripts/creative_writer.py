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

# ── 创作方法论文本，注入 prompt ──

CREATIVE_METHODOLOGY = """
## 创作方法论

你是短视频编剧+导演。你的任务不是"写一条招聘广告"，而是——
用30秒讲一个让人看完想转发的小故事。

### 规则

1. **角色先行，不是信息先行**
   - 先创造 1-2 个有辨识度的角色。谁？什么性格？什么关系？
   - 观众因为喜欢角色而看完，不是因为听完 JD 信息。
   - 角色必须有缺陷或欲望——完美角色无趣。

2. **情绪曲线驱动，不是信息清单驱动**
   - 不要按"第一段介绍、第二段讲解、第三段号召"来结构。
   - 按"建立→冲突→反转→释放"来结构。
   - 每个 segment 标注情绪曲线：从 X 情绪 → Y 情绪。

3. **视觉即叙事**
   - 不要写"人物在办公室讲解JD"。
   - 写"金毛犬的爪子从手机滑落，屏幕还亮着抖音界面。英短猫的影子从门口投进来。"
   - 用 Seedance 能理解的视觉语言：空间、光线、材质、动作。

4. **对白要有节奏**
   - 每句对白不超过 15 字（字幕友好）。
   - 对白之间留停顿空间（让画面呼吸）。
   - 用对白揭示角色，而不是解释信息。

5. **CTA 是故事的终点，不是贴上去的广告**
   - 不要让角色突然面对镜头说"快来投简历"。
   - 让 CTA 成为剧情反转的自然结果。
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Creative writing prompt generator")
    parser.add_argument("--brief", help="path to brief.json")
    parser.add_argument("--prompt", action="store_true", help="output creative writing prompt")
    parser.add_argument("--template", action="store_true", help="output creative_content.json template")
    parser.add_argument("--output", help="write creative_content.json template to file")
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

{CREATIVE_METHODOLOGY}

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

记住: 你的首要任务是讲一个让人看完的小故事。招聘信息是故事的副产品。
"""


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

    if args.prompt:
        print(build_prompt(brief))
    elif args.template or args.output:
        template = generate_template(brief, args.output)
        if args.template:
            print(json.dumps(template, ensure_ascii=False, indent=2))
    else:
        # 默认输出 prompt
        print(build_prompt(brief))


if __name__ == "__main__":
    main()
