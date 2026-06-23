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
## 导演引擎 — 先思考，再写提示词

你不是写 prompt，你是在导演一个镜头。不要把 brief 翻译成画面清单——先像一个导演那样读懂这个场景，再让每一句 prompt 都服务于一个明确的意图。

### 第一步: 导演之读 (Director's Read)

在写任何提示词之前，用大白话回答这 5 个问题。答案决定一切后续选择。

1. **功能**: 这个镜头在整个视频里做什么？引入/深化/转折/收尾？
2. **转折**: 观众从什么状态变到什么状态？用一个对子表达: ____ → ____
3. **视角**: 观众站在谁的体验里？身体位置在哪？
4. **力量**: 谁/什么掌控这个画面？力量在谁手里？
5. **潜台词**: 画面上没说出来的真话是什么？

### 第二步: 场景类型路由

根据功能选择一个场景类型。每个类型有一套连贯的默认设置。

| 场景功能 | 镜头 | 灯光 | 表演 | 拒绝什么 |
|---|---|---|---|---|
| 产品展示 | controlled move→detail | hero light on material | one honest use action | "动态产品镜头"和无目的漂移 |
| 揭示/发现 | withhold→disclose, 镜头与主体一同发现 | light tracks the change | 反应就是镜头内容 | 一次性展示所有 |
| 亲密对话 | MCU→CU, eye-level | soft motivated key | micro-behavior: 停顿的眼神, 吞咽, 手出卖平静 | 漫游镜头和大景别破坏亲密 |
| 决策/转折点 | push-in to isolate | light shifts on commit | one decisive physical action | 让台词替代身体动作 |
| 喜剧节拍 | locked frame, deadpan hold | clean, even | commitment+restraint, hold past comfort | 忙碌的镜头踩到笑点的节奏 |
| 情感低谷 | distance+stillness, cool soft light | negative space, near-silence | containment: 最小的真实手势 | 配乐驱动和多动的镜头 |
| 登场/建立 | wide→medium-wide, environmental light | places subject in space | 姿势和步速在远处就能读出状态 | 没有主体关系的漂亮空镜 |
| 追逐/动作 | tracking/handheld, screen-direction | contrast light | effort+consequence: weight, recovery | 叠太多动作变混沌 |
| 对抗/力量 | opposed angles, height encodes status | warm/cool split | stillness as dominance | 抹平力量差的对称中立 |
| 变身/特效 | locked camera, change is legible | light tracks change | subject responds, not narrates | 没有锚点和余波的奇观 |

### 第三步: 导演之声 (Voice)

{director_voice_section}

### 第四步: Director Formula

用这个 7 槽公式写每一镜的 prompt。Subject+Action 放最前面——Seedance 靠前几个词建立画面层级。不要强迫填满，如果参考图已经展示了信息就不重复。

| 槽位 | 填什么 | 模式 |
|---|---|---|
| **Subject** | 模型必须锁定的主体 | `白色陶瓷智能花盆, LED圆形屏幕😰表情` |
| **Action** | 可见的变化, 一个明确的物理动作 | `水柱倾斜落入土壤, LED😰闪烁渐变为😊绿光` |
| **Scene** | 参考图之外才需要补充的空间信息 | `titanium质感桌面, frosted glass背景虚化` |
| **Camera** | 一个主要运动+终点 | `远景缓推至中景` 或 `推进至LED屏特写, shallow景深` |
| **Light** | 物理光源+情绪 | `morning light从窗边斜入, LED绿光照亮周围空气` |
| **Audio** | 环境音/SFX/对白/静默 | `水滴声, 柔和的电子提示音` |
| **Constraints** | 保持不变的+排除的 | `不要文字/LOGO/字幕` `保持花盆形状和植物特征` |

### 第五步: 写完后自检 (Coherence Test)

每个镜头写完检查:

[ ] 能用一句话说清这个镜头的意图吗？如果说不清，回到第一步。
[ ] 镜头/灯光/表演/声音都指向同一个意图吗？任何不服务于意图的元素砍掉。
[ ] 表演是可见的动作，不是情绪词吗？("她很难过" → "她折好信纸, 双手压平, 没有抬头")
[ ] 灯光有可信的光源吗？镜头运动有理由吗？
[ ] 这个镜头的风格和全片一致吗？

### 完整示例

Brief: "15秒智能花盆产品演示。缺水😰→浇水→😊，展示产品魅力，让人想买。"

**导演之读**:
- 功能: 揭示产品魅力 (reveal)
- 转折: 普通物品 → 渴望之物
- 视角: 买家之眼——近距离观看这个美丽的小东西活过来
- 力量: 产品掌控画面——它是表演者, 手只是配角
- 潜台词: 拥有它 = 拥有一个会表达情感的小生命

**Voice**: 构图经典 (composed classicist) — 精确、均衡、clean

**Three shots**:

shot-01 (0-5s):
"9:16竖屏, apple-cupertino风格。白色陶瓷智能花盆居于构图中央, titanium质感桌面反射morning light。一株绿萝从盆沿垂下, 叶片微卷。花盆正面圆形LED屏显示😰表情, 红色脉冲光在frosted glass背景上投出呼吸般的光晕。镜头从远景以ease-in-out缓推至中景。"
→ 意图: 建立渴望——让观众先看到这个美丽的东西, 再发现它在"口渴"

shot-02 (5-11s):
"一只手从画外右侧优雅伸入, 透明玻璃水壶倾斜——水柱落入深褐色土壤。LED屏😰开始闪烁, 红光渐变为温暖的绿色, 😊表情缓缓浮现。绿萝叶片微微颤动展开。镜头推进至花盆LED屏特写, shallow景深让背景完全虚化, 观众的注意力被锁在变化本身。"
→ 意图: 展示转变——浇水的瞬间就是产品魔法的瞬间

shot-03 (11-15s):
"😊表情在LED屏上稳定亮起, 绿光照亮花盆周围的空气。镜头缓慢拉远——露出整张桌面构图, 花盆旁出现iPhone显示App界面(植物状态'已浇水')。画面定格在花盆😊与App的和谐构图。"
→ 意图: 完成渴望——观众现在想要这个能表达情感的花盆
"""


_VOICE_GUIDE = {
    "intimate-minimalist": "**导演之声: 亲密极简** — 近景、眼平、小运动、单一柔光、克制表演、缓慢剪辑。适合情感故事、个人时刻、孤独感。不要让镜头闯入角色的空间。",
    "composed-classicist": "**导演之声: 构图经典** — 精确、均衡、有分寸的运动、干净雕塑光、耐心节奏、精准表演。适合高端产品、商业广告、premium内容。每个画面都应该可以截图当海报。",
    "kinetic-visceral": "**导演之声: 动感本能** — 手持能量、追踪、近距、硬光高对比、快速打击感、高度用力表演。适合运动、动作、hype视频。让观众感觉到冲击。",
    "expressive-stylist": "**导演之声: 表现风格** — 大胆运镜、设计感构图、戏剧化但合理的光、饱和色彩、音乐性节奏、风格化肢体。适合音乐视频、时尚、幻想。画面本身就是表达。",
    "observational-naturalist": "**导演之声: 观察自然** — 隐形镜头、自然光驱动、柔和克制、长镜头晚剪辑、生活化表演。适合纪录片感、真实瞬间、接地气的内容。镜头不应该被注意到。",
    "graphic-formalist": "**导演之声: 图形形式** — 锁定或精确几何、硬光造型、有限色彩、精确冷面节奏、风格化或冷面表演。适合设计感品牌、冷面喜剧、视觉冲击型内容。",
}

_VOICE_DEFAULTS = {
    "intimate-minimalist": "近景眼平·小运动·单一柔光·微表情",
    "composed-classicist": "精确均衡·hero light·有分寸的运动·干净",
    "kinetic-visceral": "手持追踪·高对比·快速打击·高度用力",
    "expressive-stylist": "大胆运镜·饱和色彩·戏剧光·风格化",
    "observational-naturalist": "隐形镜头·自然光·长镜头·生活化",
    "graphic-formalist": "锁定几何·硬光·有限色彩·冷面节奏",
}


def build_direct_prompt(brief: dict) -> str:
    """生成 Seedance-native 导演级分镜提示词引导."""
    duration = brief["duration_seconds"]
    ratio = brief["aspect_ratio"]
    preset = brief.get("aesthetic_preset", "")
    voice = brief.get("director_voice", "")
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

    # Voice 指引
    if voice and voice in _VOICE_GUIDE:
        voice_section = _VOICE_GUIDE[voice]
        voice_default = _VOICE_DEFAULTS.get(voice, "")
        voice_section += f"\n\n默认倾向: {voice_default}。每个镜头的设置从这个默认出发，根据具体的场景功能微调。"
    else:
        voice_section = "**导演之声**: 未预设。根据内容推断——产品→构图经典, 情感→亲密极简, 动作→动感本能, 品牌→图形形式。选定后每个镜头保持一致。"
        voice_default = ""

    methodology = _DIRECT_METHODOLOGY.replace("{director_voice_section}", voice_section)

    return f"""# Seedance 导演级分镜提示词

## 技术约束
- 时长: {duration}s
- 比例: {ratio}
- 美学预设: {preset}
- 导演之声: {voice if voice else '(由你推断)'}
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

{methodology}

## 输出格式

请输出符合 `schemas/shot-prompts.schema.json` 的 JSON。写进 `shot_prompts.json`。

可选质量字段:
- `director_voice`: 你选择的导演之声
- `scene_function`: 场景功能类型
- `intention`: 一句话——这个视频要让观众感受到什么

分镜字段:
- `shots[].shot_id`: "shot-01", "shot-02"...
- `shots[].start_second` / `shots[].end_second`: 时间范围
- `shots[].prompt`: Seedance 提示词（Director Formula 7槽: Subject+Action+Scene+Camera+Light+Audio+Constraints）
- `shots[].camera_hint`: 可选镜头编码建议

记住: prompt 不只是描述画面——prompt 是一个导演的指令。每一句都应该能回答"为什么这样写"。
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
