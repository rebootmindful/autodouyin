"""
/**
 * [INPUT]: 依赖 {skeleton、brief 与 references} 的 {内容填充需求}
 * [OUTPUT]: 对外提供 {完整 review package 的确定性内容编译}
 * [POS]: {scripts} 的 {内容编译模块}，用稳定模板替代易漂移的会话内 enrichment
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */
"""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime
from pathlib import Path


TYPE_INTROS = {
    "workflow-explainer": "工作流演示视频，强调信息清晰、结果可见、过程有节奏。",
    "product-demo": "商业产品演示视频，强调卖点直给、UI 清晰、动作利落。",
    "narrative-story": "剧情短片风格，强调情绪起伏、人物状态变化和结果反转。",
    "character-action": "角色动作展示，强调姿态建立、动作升级和高潮定格。",
    "space-tour": "沉浸式空间漫游，强调路径、空间关系和节点展示。",
}

TYPE_TAGS = {
    "workflow-explainer": "信息层级清楚，结果面板可读，过程到结果连续",
    "product-demo": "商业广告节奏，卖点一眼可见，界面与动效高级干净",
    "narrative-story": "人物情绪递进，压力到释放，剧情反转明确",
    "character-action": "动作动势连续，角色姿态强，高潮击中感明确",
    "space-tour": "空间路径稳定，节点切换自然，光线与材质层次清晰",
}

PURPOSE_SUMMARIES = {
    "hook": ("开场先给结果感，第一秒说明视频主题。", "urgent"),
    "setup": ("交代主体、场景和工作流背景。", "focused"),
    "turn": ("推进变化，让信息密度逐步上升。", "active"),
    "payoff": ("集中展示结果，让价值清楚落地。", "confident"),
    "close": ("留在可执行状态，形成清晰收束。", "resolved"),
    "world-build": ("建立世界与空间关系，让观众先看懂环境。", "calm"),
    "setup-flow": ("把主要流程展开，让结构进入视野。", "focused"),
    "change-push": ("把变化推起来，让系统、动作和信息同步升级。", "active"),
    "peak-moment": ("把高潮结果推到最强，形成强记忆点。", "intense"),
    "emotional-close": ("把节奏收回来，让画面与情绪落点稳定。", "resolved"),
}

CAMERA_TEXT = {
    "hook": "快速推近，第一眼抓人，强调结果先行。",
    "setup": "中景稳定推进，交代空间和主体位置。",
    "turn": "轻微横移配合推进，展示变化升级。",
    "payoff": "由中景推到近景，强调结果与完成状态。",
    "close": "缓慢拉远，形成收束和留白。",
    "world-build": "稳定机位为主，先远后中，让空间关系可读。",
    "setup-flow": "中景稳定推进，让主要流程逐步展开。",
    "change-push": "由中景推进到近景，局部横移辅助变化。",
    "peak-moment": "近景强化高潮主体，镜头更聚焦更有冲击。",
    "emotional-close": "从近景回到中远景，轻微拉远完成收束。",
}

ACTION_TEXT = {
    "hook": "主体或结果卡片立即出现，不做长铺垫。",
    "setup": "主体进入场景，流程入口和核心信息被清楚揭示。",
    "turn": "系统编译、面板切换和主体操作联动推进。",
    "payoff": "结果面板依次亮起，核心成果集中呈现。",
    "close": "主体停留在确认前一刻，保留继续执行的余量。",
    "world-build": "主体进入场景，工作流逐步展开，但不急于爆发变化。",
    "setup-flow": "流程节点按顺序进入视野，形成稳定的操作节奏。",
    "change-push": "主体操作与系统反馈联动，结果持续堆叠。",
    "peak-moment": "动作和结果到达最高点，信息密度与情绪同步抬升。",
    "emotional-close": "主体确认结果，系统停在待执行或待发布状态。",
}

BASE_NEGATIVES = [
    "禁止风格漂移",
    "禁止角色变脸或换人",
    "禁止突然偏色",
    "禁止新增无关人物",
    "禁止光线突变",
    "禁止出现文字、字幕、LOGO、水印",
]

RECRUIT_KEYWORDS = ["招聘", "岗位", "JD", "jd", "投递", "候选人", "电商运营"]
ATMOSPHERE_KEYWORDS = ["氛围", "质感", "情绪", "梦境", "抽象", "诗意", "意识流", "感觉", "片段", "意境"]
SELL_KEYWORDS = ["卖点", "转化", "下单", "商品", "产品", "功能", "广告", "介绍"]
CHARACTER_KEYWORDS = ["人物", "主角", "女生", "男生", "角色", "口播", "面对镜头"]

# 含创作元素的 recruiting brief：有具体角色/剧情/场景/动物/喜剧元素
CREATIVE_CONTENT_SIGNALS = [
    "宠物", "猫", "狗", "动物", "对话", "搞笑", "反转", "反差", "爆点",
    "剧情", "角色扮演", "剧场", "小剧场", "喜剧", "段子",
    "办公室", "工位", "摸鱼", "训话", "简历",
]


def is_creative_recruiting(brief: dict) -> bool:
    """recruiting brief 是否包含创作内容（角色/剧情/场景），需要保留创作主链"""
    if not is_recruiting_video(brief):
        return False
    creative_types = {"character-action", "narrative-story"}
    if brief.get("video_type") in creative_types:
        return True
    text = " ".join(
        [
            str(brief.get("goal", "")),
            str(brief.get("style", "")),
            str(brief.get("tone", "")),
            " ".join(brief.get("must_include", [])),
        ]
    )
    return any(signal in text for signal in CREATIVE_CONTENT_SIGNALS)


# ──────────────────────────────────────────────
# Creative Content — LLM 创作层接入
# ──────────────────────────────────────────────

def load_creative_content(output_dir: Path) -> dict | None:
    """加载 LLM 创作的 creative_content.json。若不存在或未被 LLM 填充则返回 None。

    判定"已填充"的条件：至少一个角色有名字 + 至少一个镜头有 visual_core。
    仅有空模板占位符视为未填充。
    """
    path = output_dir / "creative_content.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    # 检查是否已被 LLM 填充（不是空模板）
    chars = data.get("characters", [])
    shots = data.get("shots", [])
    has_char = any(c.get("name", "").strip() for c in chars)
    has_visual = any(s.get("visual_core", "").strip() for s in shots)
    if not has_char or not has_visual:
        return None  # 空模板，未填充
    return data


def has_creative_content(output_dir: Path) -> bool:
    return load_creative_content(output_dir) is not None


def _creative_char(creative: dict, asset_id: str) -> dict | None:
    for c in creative.get("characters", []):
        if c["asset_id"] == asset_id:
            return c
    return None


def _creative_scene(creative: dict, asset_id: str) -> dict | None:
    for s in creative.get("scenes", []):
        if s["asset_id"] == asset_id:
            return s
    return None


def _creative_segment(creative: dict, seg_id: str) -> dict | None:
    for seg in creative.get("segments", []):
        if seg["segment_id"] == seg_id:
            return seg
    return None


def _creative_shot(creative: dict, shot_id: str) -> dict | None:
    for sh in creative.get("shots", []):
        if sh["shot_id"] == shot_id:
            return sh
    return None


# ──────────────────────────────────────────────

def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def load_presets() -> dict:
    path = Path(__file__).parent.parent / "references" / "aesthetic-presets.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["presets"]


def pick_preset(brief: dict) -> dict:
    presets = load_presets()
    return presets[brief["aesthetic_preset"]]


def concise_title(goal: str, limit: int = 30) -> str:
    text = " ".join(str(goal).split())
    return text[:limit].rstrip(" ，,。")


def keyword_text(preset: dict) -> str:
    return "、".join(preset.get("visual_keywords", [])[:3])


def is_recruiting_video(brief: dict) -> bool:
    override = brief.get("template_override")
    if override == "none":
        return False
    if override == "recruit-exact":
        return True
    text = " ".join(
        [
            str(brief.get("goal", "")),
            str(brief.get("audience", "")),
            " ".join(brief.get("must_include", [])),
        ]
    )
    return any(keyword in text for keyword in RECRUIT_KEYWORDS)


def source_file_bindings(brief: dict) -> dict[str, dict]:
    files = brief.get("source_material_files") or []
    character = next((item for item in files if item.get("role") == "character"), None)
    scene = next((item for item in files if item.get("role") == "scene"), None)
    prop = next((item for item in files if item.get("role") == "prop"), None)
    reference = [item for item in files if item.get("role") == "reference"]
    bindings = {}
    if character:
        bindings["C01"] = character
    elif reference:
        bindings["C01"] = reference[0]
    if scene:
        bindings["S01"] = scene
    elif len(reference) > 1:
        bindings["S01"] = reference[1]
    if prop:
        bindings["P01"] = prop
    elif len(reference) > 2:
        bindings["P01"] = reference[2]
    return bindings


def active_asset_ids(brief: dict) -> list[str]:
    bindings = source_file_bindings(brief)
    active = ["C01", "S01"]
    if "P01" in bindings:
        active.append("P01")
    return active


def has_character_reference(brief: dict) -> bool:
    return "C01" in source_file_bindings(brief)


def infer_intent_family(brief: dict) -> str:
    text = " ".join(
        [
            str(brief.get("goal", "")),
            str(brief.get("audience", "")),
            str(brief.get("style", "")),
            " ".join(brief.get("must_include", [])),
        ]
    )
    if is_recruiting_video(brief):
        return "recruit"
    if any(keyword in text for keyword in SELL_KEYWORDS):
        return "sell"
    if any(keyword in text for keyword in ATMOSPHERE_KEYWORDS):
        return "atmosphere"
    if any(keyword in text for keyword in CHARACTER_KEYWORDS):
        return "showcase-character"
    if brief.get("video_type") == "space-tour":
        return "tour-space"
    if brief.get("video_type") == "narrative-story":
        return "narrate"
    return "explain"


def fallback_family(intent: str) -> str:
    if intent in {"explain", "recruit"}:
        return "fallback-information"
    if intent in {"sell", "showcase-character", "tour-space"}:
        return "fallback-demonstration"
    if intent in {"atmosphere", "narrate"}:
        return "fallback-atmosphere"
    return "fallback-information"


def identity_strategy(brief: dict) -> str:
    if has_character_reference(brief):
        return "reference-image"
    if brief.get("duration_seconds", 0) > 60:
        return "derived-stills"
    if any(keyword in str(brief.get("goal", "")) for keyword in CHARACTER_KEYWORDS) or is_recruiting_video(brief):
        return "first-block-anchor"
    return "text-only"


def identity_risk(strategy: str) -> str:
    mapping = {
        "reference-image": "low",
        "first-block-anchor": "medium",
        "derived-stills": "medium",
        "text-only": "high",
    }
    return mapping.get(strategy, "high")


def recruiting_lines(brief: dict) -> list[str]:
    # NOTE: 品牌名称由用户 brief 提供，不使用硬编码占位。此处为通用模板默认措辞。
    return [
        "我们正在招聘电商运营，想找既懂平台节奏也能把执行落地的人加入团队。",
        "这个岗位会负责店铺日常运营、活动报名与执行、商品与页面优化，以及核心数据复盘和增长推进。",
        "如果你有电商运营经验，做事细致、沟通顺畅，也希望在业务里真正拿结果，欢迎投递电商运营岗位。",
    ]


def segment_copy(segment: dict, brief: dict) -> tuple[str, str]:
    summary, emotion = PURPOSE_SUMMARIES.get(segment["purpose"], ("围绕目标推进内容。", "steady"))
    goal = brief["goal"]
    return f"{summary} 主题围绕“{goal}”展开。", emotion


def fill_script(script: dict, brief: dict, output_dir: Path | None = None) -> dict:
    enriched = deepcopy(script)
    creative = load_creative_content(output_dir) if output_dir else None
    intent = infer_intent_family(brief)
    enriched["title"] = concise_title(brief["goal"], limit=40)
    enriched["logline"] = f"围绕“{brief['goal']}”生成一条可审核、可执行、可回放的视频方案。"
    creative_recruit = is_creative_recruiting(brief)
    pure_recruit = is_recruiting_video(brief) and not creative_recruit

    if creative:
        enriched["template_mode"] = "llm-creative"
        enriched["template_confidence"] = "high"
    elif pure_recruit:
        enriched["template_mode"] = "recruit-exact"
        enriched["template_confidence"] = "high"
    else:
        enriched["template_mode"] = fallback_family(intent)
        enriched["template_confidence"] = "medium" if intent != "explain" else "low"

    spoken_lines = recruiting_lines(brief) if pure_recruit else []
    for segment in enriched["segments"]:
        summary, emotion = segment_copy(segment, brief)
        segment["spoken_line"] = ""
        if creative:
            cseg = _creative_segment(creative, segment["segment_id"])
            if cseg:
                segment["summary"] = cseg.get("beat_name") or cseg["emotion_curve"]
                segment["emotion"] = cseg["emotion_curve"]
                dialogue_lines = cseg.get("dialogue", [])
                segment["spoken_line"] = " | ".join(
                    f"{d['speaker']}: {d['line']}" for d in dialogue_lines
                ) if dialogue_lines else ""
        elif pure_recruit:
            idx = int(segment["segment_id"][-2:]) - 1
            spoken = spoken_lines[min(idx, len(spoken_lines) - 1)]
            segment["summary"] = f"人物面对镜头讲解招聘信息：{summary}"
            segment["spoken_line"] = spoken
        elif creative_recruit:
            segment["summary"] = f"{summary} 主题围绕“{brief['goal']}”展开，在结尾自然引导至招聘行动号召。"
        else:
            if enriched["template_mode"] == "fallback-information":
                segment["summary"] = f"围绕目标分点说明：{summary}"
            elif enriched["template_mode"] == "fallback-demonstration":
                segment["summary"] = f"围绕主体与关键变化做展示：{summary}"
            else:
                segment["summary"] = f"围绕主视觉与情绪层次做推进：{summary}"
        segment["emotion"] = emotion
    return enriched


def shot_intro(brief: dict, preset: dict, shot: dict) -> str:
    keywords = keyword_text(preset)
    return f"{shot['purpose']} 段围绕“{brief['goal']}”展开，画面持续体现 {keywords}。"


def recruiting_visual(brief: dict, shot: dict) -> str:
    visuals = {
        "world-build": "人物站在整洁办公室或直播电商工作位前，面对镜头开场介绍品牌正在招聘电商运营，背景可见电脑、电商后台和团队办公氛围。",
        "change-push": "人物继续面对镜头讲解岗位 JD，旁侧穿插店铺后台、活动报名页面、商品链接和数据看板的特写，突出职责内容。",
        "emotional-close": "人物给出岗位亮点和投递邀请，镜头拉到中景，背景保持干净专业，画面收在品牌与岗位行动号召上。",
    }
    return visuals.get(shot["purpose"], shot_intro(brief, pick_preset(brief), shot))


def recruiting_action(shot: dict) -> str:
    actions = {
        "world-build": "人物正对镜头稳定开讲，手势克制，旁边屏幕或立牌同步出现岗位名称与公司信息。",
        "change-push": "人物继续口播岗位职责，镜头配合切入后台、活动、页面优化和数据复盘相关画面。",
        "emotional-close": "人物收束讲解，明确说出岗位亮点与欢迎投递，动作停在自信邀请的状态。",
    }
    return actions.get(shot["purpose"], ACTION_TEXT.get(shot["purpose"], "主体与系统围绕目标推进。"))


def recruiting_dialogue(shot: dict, script: dict) -> str:
    for segment in script["segments"]:
        expected = int(segment["segment_id"][-2:])
        actual = int(shot["shot_id"][-2:])
        if expected == actual and segment.get("spoken_line"):
            return segment["spoken_line"]
    lines = recruiting_lines({"goal": ""})
    return lines[min(int(shot["shot_id"][-2:]) - 1, len(lines) - 1)]


def recruiting_audio(dialogue: str, total: int) -> str:
    return f"人物同步口播：“{dialogue}” 背景配乐保持克制明快，办公环境音轻量存在，共 {total} 个镜头。"


def shot_audio(shot: dict, total: int) -> str:
    if total == 1:
        return "保持统一环境音和配乐，节奏稳定推进并自然收束。"
    return f"延续统一环境音与配乐层次。 当前镜头需与前后段落保持风格连续，共 {total} 个镜头。"


def shot_continuity(shot: dict) -> str:
    if shot["segment_mode"] in {"segment-extension", "scene-extension"}:
        return "接续上一段最后一帧的构图与角色状态，先保留微动作，再进入新动作。"
    if shot["segment_mode"] == "scene-base":
        return "作为独立 scene 的开场，结尾应留给后续 scene 后期拼接。"
    return "保持主体、空间和光线连续，后续镜头沿用同一视觉关系。"


def fill_storyboard(storyboard: dict, script: dict, brief: dict, preset: dict, output_dir: Path | None = None) -> dict:
    enriched = deepcopy(storyboard)
    total = len(enriched["shots"])
    creative = load_creative_content(output_dir) if output_dir else None
    pure_recruit = is_recruiting_video(brief) and not is_creative_recruiting(brief)
    creative_recruit = is_creative_recruiting(brief)
    strategy = identity_strategy(brief)
    asset_ids = active_asset_ids(brief)
    for i, shot in enumerate(enriched["shots"]):
        is_last_shot = (i == total - 1)
        camera = CAMERA_TEXT.get(shot["purpose"], "镜头语言简洁稳定，优先保证主体可读。")
        action = ACTION_TEXT.get(shot["purpose"], "主体与系统围绕目标推进。")
        shot["dialogue"] = ""
        if creative:
            cshot = _creative_shot(creative, shot["shot_id"])
            if cshot:
                shot["visual"] = cshot["visual_core"]
                shot["camera"] = cshot.get("camera_style", camera)
            # 从 creative segments 提取对白
            seg_id = f"seg-{shot['shot_id'][-2:]}"
            cseg = _creative_segment(creative, seg_id)
            if cseg:
                dialogue_lines = cseg.get("dialogue", [])
                shot["dialogue"] = " | ".join(
                    f"{d['speaker']}: {d['line']}" for d in dialogue_lines
                ) if dialogue_lines else ""
                shot["audio"] = recruiting_audio(shot["dialogue"], total) if dialogue_lines else shot_audio(shot, total)
            else:
                shot["audio"] = shot_audio(shot, total)
            shot["action"] = ACTION_TEXT.get(shot["purpose"], "角色按剧情节奏推进，动作与表情饱满。")
            if strategy in {"first-block-anchor", "derived-stills", "text-only"}:
                shot["action"] += " 保持同一人物发型、服装、年龄感和职业气质一致。"
        elif pure_recruit:
            dialogue = recruiting_dialogue(shot, script)
            shot["dialogue"] = dialogue
            shot["visual"] = recruiting_visual(brief, shot)
            shot["action"] = recruiting_action(shot)
            shot["audio"] = recruiting_audio(dialogue, total)
        elif creative_recruit:
            # 创作主链 + 招聘元素注入
            keywords = keyword_text(preset)
            shot["visual"] = f"围绕“{brief['goal']}”建立主视觉与角色互动，画面持续体现 {keywords}。"
            if is_last_shot:
                shot["visual"] += " 结尾画面自然过渡至招聘行动号召，出现品牌与投递引导元素。"
            shot["action"] = "角色按剧情节奏推进，动作与表情饱满。"
            if is_last_shot:
                shot["action"] += " 最后动作指向招聘信息或投递入口。"
            if shot.get("segment_mode") in {"segment-extension", "scene-extension"}:
                shot["action"] += " 保持同一人物发型、服装、年龄感和职业气质一致。"
            shot["audio"] = shot_audio(shot, total)
            # 末段注入招聘口播提示
            if is_last_shot and script.get("segments"):
                last_seg = script["segments"][-1]
                if last_seg.get("spoken_line"):
                    shot["dialogue"] = last_seg["spoken_line"]
                    shot["audio"] = f"人物同步口播：“{shot['dialogue']}” 背景配乐保持克制明快，共 {total} 个镜头。"
        else:
            if script.get("template_mode") == "fallback-information":
                shot["visual"] = f"人物或主体清楚出现在画面中，围绕“{brief['goal']}”逐步展开要点说明，画面持续体现 {keyword_text(preset)}。"
                shot["action"] = "主体保持稳定出现，按节奏分点说明信息，不突然切大动作。"
            elif script.get("template_mode") == "fallback-demonstration":
                shot["visual"] = f"主体与关键对象被清楚展示，围绕“{brief['goal']}”呈现前后变化或核心亮点，画面持续体现 {keyword_text(preset)}。"
                shot["action"] = "以展示主体、动作和结果为主，减少纯说明感。"
            else:
                shot["visual"] = f"围绕“{brief['goal']}”建立主视觉与情绪层次，画面持续体现 {keyword_text(preset)}，强调氛围和质感而不是解释。"
                shot["action"] = "主体动作克制，更多依靠镜头、光线和节奏推进情绪。"
            shot["audio"] = shot_audio(shot, total)
            if strategy in {"first-block-anchor", "derived-stills", "text-only"}:
                shot["action"] += " 保持同一人物发型、服装、年龄感和职业气质一致。"
        shot["camera"] = f"{camera} 镜头编码 {shot['camera_codec']['z']} {shot['camera_codec']['y']} {shot['camera_codec']['x']}，{shot['camera_codec']['focal_length_mm']}mm，{shot['camera_codec']['depth']}景深。"
        shot["continuity_note"] = shot_continuity(shot)
        shot["assets"] = asset_ids
    return enriched


def asset_item_text(asset_id: str, brief: dict, preset: dict, output_dir: Path | None = None) -> tuple[str, str, str]:
    goal = brief["goal"]
    style = preset["display_name"]
    creative = load_creative_content(output_dir) if output_dir else None
    pure_recruit = is_recruiting_video(brief) and not is_creative_recruiting(brief)
    creative_recruit = is_creative_recruiting(brief)

    if creative and asset_id.startswith("C"):
        ch = _creative_char(creative, asset_id)
        if ch:
            return (
                ch["name"],
                f"{ch['personality']} — {ch['appearance']}",
                f"{style} 风格，{ch['appearance']}。{ch.get('voice_style', '')}",
            )
    if creative and asset_id.startswith("S"):
        sc = _creative_scene(creative, asset_id)
        if sc:
            return (
                sc["name"],
                f"{sc['setting']} — 情绪: {sc['mood']}",
                f"{style} 风格，{sc['setting']}。关键道具: {', '.join(sc.get('key_props', []))}",
            )
    if pure_recruit and asset_id.startswith("C"):
        return (
            "招聘讲解人",
            f"品牌招聘宣传视频中的主讲人物，面对镜头讲解电商运营岗位 JD，风格对齐 {style}。",
            f"{style} 风格企业招聘讲解人，职业感强，面对镜头自然讲述电商运营岗位职责与亮点。",
        )
    if pure_recruit and asset_id.startswith("S"):
        return (
            "办公与后台场景",
            f"品牌办公区、电商后台或运营工作位，用来承接岗位说明，风格对齐 {style}。",
            f"{style} 风格企业办公场景，包含电脑屏幕、电商后台、数据看板和团队办公氛围，体现电商运营岗位真实环境。",
        )
    if pure_recruit and asset_id.startswith("P"):
        return (
            "JD信息卡",
            f"用于展示岗位职责、任职要求、投递行动号召的信息卡或屏幕内容，风格对齐 {style}。",
            f"{style} 风格岗位 JD 信息卡，简洁展示职责、亮点和投递提示，适合招聘宣传视频穿插使用。",
        )
    if creative_recruit and asset_id.startswith("C"):
        return (
            f"角色-{asset_id}",
            f"根据“{goal}”设计的视频角色，需保持外观一致贯穿全片，风格对齐 {style}。",
            f"{style} 风格角色设计，围绕“{goal}”展开，表情丰富、辨识度高，适合剧情推进。",
        )
    if creative_recruit and asset_id.startswith("S"):
        return (
            f"场景-{asset_id}",
            f"根据“{goal}”设计的视频场景，建立空间与氛围，风格对齐 {style}。",
            f"{style} 风格场景设计，围绕“{goal}”展开，空间关系清晰、光线与材质层次丰富。",
        )
    if asset_id.startswith("C"):
        return (
            "主体角色",
            f"承载“{goal}”的主要角色或操作主体，风格对齐 {style}。",
            f"{style} 风格主体角色，用于表现“{goal}”，服装、轮廓和身份稳定一致。",
        )
    if asset_id.startswith("S"):
        return (
            "主场景",
            f"承载“{goal}”的主要工作环境或展示空间，风格对齐 {style}。",
            f"{style} 风格主场景，用于表现“{goal}”的空间关系、光线与背景层次。",
        )
    return (
        "关键道具",
        f"帮助说明“{goal}”的关键道具、结果卡片或界面成果，风格对齐 {style}。",
        f"{style} 风格关键道具或结果卡片，用于强化“{goal}”的完成状态和记忆点。",
    )


def fill_assets(assets: dict, brief: dict, preset: dict, output_dir: Path | None = None) -> dict:
    enriched = deepcopy(assets)
    strategy = identity_strategy(brief)
    bindings = source_file_bindings(brief)
    keep_ids = set(active_asset_ids(brief))
    enriched["items"] = [item for item in enriched["items"] if item["asset_id"] in keep_ids]
    for item in enriched["items"]:
        name, description, prompt = asset_item_text(item["asset_id"], brief, preset, output_dir)
        item["name"] = name
        item["description"] = description
        item["prompt"] = prompt
        bound = bindings.get(item["asset_id"])
        if bound:
            item["source_ref"] = bound["id"]
            item["source_label"] = bound.get("label", "")
            item["resolved_path"] = bound.get("path", "")
        if item["asset_id"].startswith("C"):
            item["continuity_priority"] = "high"
            item["identity_lock"] = {
                "strategy": strategy,
                "gender_presentation": "not-specified",
                "approx_age_range": "adult",
                "hair": "保持前后统一，不随段落变化",
                "outfit": "保持同一套主服装",
                "accessories": "如出现配饰需保持不变",
                "persona": "保持同一人物职业气质与年龄感",
            }
        else:
            item["continuity_priority"] = "medium"
    return enriched


def continuity_locks(preset: dict) -> list[str]:
    return [
        f"{preset['seedance_style_anchor']}，统一视觉风格，画面干净，避免风格漂移",
        "同一角色保持一致五官、身份、服装和发型，不变脸、不换人。",
        "同一场景保持一致环境、光线、背景与空间关系，不突然切换。",
    ]


def negative_constraints(preset: dict) -> list[str]:
    return [*BASE_NEGATIVES, *preset.get("seedance_negative_additions", [])]


def block_prompt(block: dict, shot: dict, brief: dict, preset: dict, seedance: dict) -> str:
    duration = int(block["end_second"] - block["start_second"])
    opener = TYPE_INTROS[seedance["video_type"]]
    style = continuity_locks(preset)[0]
    visual = f"{int(block['start_second'])}-{int(block['end_second'])}秒画面：{shot['visual']}"
    camera = f"镜头：{shot['camera']}"
    action = f"动作：{shot['action']}"
    dialogue = f"人物口播：{shot['dialogue']}" if shot.get("dialogue") else ""
    audio = f"声音：{shot['audio']}"
    tags = f"额外要求：{TYPE_TAGS[seedance['video_type']]}"
    if block["video_refs"]:
        prefix = f"将@视频1延长{duration}秒，接续上一段最后一帧的构图与角色状态，前1秒仅保留微动作和环境流动。 "
        return " ".join([prefix + opener, f"风格锁定：{style}", visual, camera, action, dialogue, audio, tags])
    return " ".join([opener, f"风格锁定：{style}", visual, camera, action, dialogue, audio, tags])


def fill_seedance(seedance: dict, storyboard: dict, brief: dict, preset: dict) -> dict:
    enriched = deepcopy(seedance)
    shots = {shot["shot_id"]: shot for shot in storyboard["shots"]}
    ordered_shots = storyboard["shots"]
    enriched["global_style_anchor"] = preset["seedance_style_anchor"]
    enriched["continuity_locks"] = continuity_locks(preset)
    enriched["negative_constraints"] = negative_constraints(preset)
    enriched["identity_strategy"] = identity_strategy(brief)
    bindings = source_file_bindings(brief)
    enriched["slot_plan"] = [
        slot for slot in enriched["slot_plan"]
        if slot["asset_id"] in {"C01", "S01"} or slot["asset_id"] in bindings
    ]
    if enriched["identity_strategy"] in {"first-block-anchor", "derived-stills", "text-only"}:
        enriched["continuity_locks"].append("主角保持同一张脸、同一发型、同一服装、同一年龄感和同一职业气质，不切换人物设定。")
    for block, shot in zip(enriched["prompt_blocks"], ordered_shots):
        block["duration_seconds"] = int(block["end_second"] - block["start_second"])
        active_refs = {slot["ref"] for slot in enriched["slot_plan"]}
        block["image_refs"] = [ref for ref in block.get("image_refs", []) if ref in active_refs]
        block["prompt"] = block_prompt(block, shot, brief, preset, enriched)
    return enriched


def fill_publish(publish: dict, brief: dict, script: dict, output_dir: Path | None = None) -> dict:
    enriched = deepcopy(publish)
    creative = load_creative_content(output_dir) if output_dir else None
    title = concise_title(script["title"], limit=30)
    enriched["title"] = title or "短视频方案"
    if creative:
        cta = creative.get("cta_moment", {})
        enriched["description"] = (
            f"{creative.get('creative_direction', brief['goal'])}\n\n"
            f"品牌招聘电商运营。\n"
            f"如果你有电商运营经验，欢迎投递。"
        )
        enriched["hashtags"] = ["#招聘", "#电商运营", "#搞笑", "#求职"]
    elif is_creative_recruiting(brief):
        enriched["description"] = (
            f"{brief['goal']}\n\n"
            "品牌招聘电商运营。\n"
            "岗位方向：店铺运营、活动执行、商品与页面优化、数据复盘。\n"
            "如果你有电商运营经验，欢迎投递，一起把业务做出结果。"
        )
        enriched["hashtags"] = ["#招聘", "#电商运营", "#搞笑", "#求职"]
    elif is_recruiting_video(brief):
        enriched["description"] = (
            "品牌招聘电商运营。\n"
            "岗位方向：店铺运营、活动执行、商品与页面优化、数据复盘。\n"
            "如果你有电商运营经验，欢迎投递，一起把业务做出结果。"
        )
        enriched["hashtags"] = ["#招聘", "#电商运营", "#岗位招聘", "#求职"]
    else:
        enriched["description"] = f"{script['logline']} 主题：{brief['goal']}"
        enriched["hashtags"] = ["#AI视频", "#Seedance", "#Douyin"]
    return enriched


def build_review_decision() -> dict:
    return {
        "status": "pending-review",
        "reviewer": "",
        "approved_at": "",
        "selected_model": "",
        "notes": "等待用户审核。确认通过后再进入真实生成。",
    }


def build_review_summary(brief: dict, script: dict, seedance: dict) -> str:
    identity = identity_strategy(brief)
    risk = identity_risk(identity)
    bindings = source_file_bindings(brief)
    lines = [
        "# Review Summary",
        "",
        "## 当前状态",
        "- 状态：pending-review",
        "- 说明：请先审核方案，再批准执行 Seedance。",
        "- 生成前必须选择模型：`doubao-seedance-1-5-pro-251215` 或 `seedance-2.0-fast/standard`",
        "",
        "## Brief",
        f"- 目标：{brief['goal']}",
        f"- 时长：{brief['duration_seconds']}s",
        f"- 比例：{brief['aspect_ratio']}",
        f"- 视频类型：{script['video_type']}",
        f"- 策略：{script['strategy']}",
        f"- 模板模式：{script.get('template_mode', 'unknown')}",
        f"- 模板置信度：{script.get('template_confidence', 'unknown')}",
        f"- 人物一致性策略：{identity}",
        f"- 人物一致性风险：{risk}",
        "",
        "## 参考素材绑定",
    ]
    if bindings:
        for asset_id, bound in bindings.items():
            lines.append(f"- {asset_id} <- {bound.get('label') or bound.get('path')} ({bound.get('path')})")
    else:
        lines.append("- 未提供可直接消费的参考图文件，当前依赖文本锁定或后续抽帧锚图。")
    lines.extend([
        "",
        "## Script Segments",
    ])
    for segment in script["segments"]:
        lines.append(f"- {segment['segment_id']} {segment['purpose']} {segment['estimated_seconds']}s: {segment['summary']}")
        if segment.get("spoken_line"):
            lines.append(f"  口播：{segment['spoken_line']}")
    lines.extend(["", "## Prompt Blocks"])
    for block in seedance["prompt_blocks"]:
        duration = int(block["end_second"] - block["start_second"])
        lines.append(f"- {block['block_id']} {duration}s / mode={block['mode']}")
    lines.extend(
        [
            "",
            "## 执行建议",
            *(
                [
                    "- 当前未检测到人物参考图，建议先用首段建立主角，再复用续拍。",
                    "- 如果追求精修出品，建议从首段视频抽 1-3 张稳定帧回写为 C01 锚图。",
                ]
                if identity != "reference-image"
                else ["- 已有参考图，可优先复用同一角色锚图保证一致性。"] 
            ),
            "",
            "## 执行方式",
            "- 只批准并选模型：`python scripts/run_pipeline.py --dir <dir> --approve --model doubao-seedance-1-5-pro-251215`",
            "- 批准后生成：`python scripts/run_pipeline.py --dir <dir> --generate`",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def build_ledger(brief: dict) -> dict:
    timestamp = now_iso()
    steps = [
        ("normalize-brief", ["brief.json"], "输入标准化完成。"),
        ("compile-script", ["script.json", "script.md"], "脚本编译完成。"),
        ("compile-storyboard", ["storyboard.json", "storyboard.md"], "分镜编译完成。"),
        ("compile-assets", ["asset-manifest.json"], "素材清单编译完成。"),
        ("compile-seedance-job", ["seedance-job.json"], "Seedance 任务编译完成。"),
        ("compile-publish-job", ["publish-job.json"], "发布任务编译完成。"),
        ("prepare-review", ["review-summary.md", "review-decision.json"], "已进入待审核状态。"),
    ]
    return {
        "id": "run-local-001",
        "brief_id": brief["id"],
        "mode": brief["mode"],
        "status": "pending-review",
        "current_stage": "pending-review",
        "artifacts": [
            "brief.json",
            "script.json",
            "script.md",
            "storyboard.json",
            "storyboard.md",
            "asset-manifest.json",
            "seedance-job.json",
            "publish-job.json",
            "review-summary.md",
            "review-decision.json",
        ],
        "steps": [ledger_step(name, artifacts, note, timestamp) for name, artifacts, note in steps],
    }


def ledger_step(name: str, artifacts: list[str], note: str, timestamp: str) -> dict:
    return {
        "name": name,
        "status": "success",
        "started_at": timestamp,
        "ended_at": timestamp,
        "artifacts": artifacts,
        "notes": note,
    }


def build_review_package(brief: dict, skeleton: dict, output_dir: Path | None = None) -> dict:
    preset = pick_preset(brief)
    script = fill_script(skeleton["script"], brief, output_dir)
    storyboard = fill_storyboard(skeleton["storyboard"], script, brief, preset, output_dir)
    assets = fill_assets(skeleton["assets"], brief, preset, output_dir)
    seedance = fill_seedance(skeleton["seedance"], storyboard, brief, preset)
    publish = fill_publish(skeleton["publish"], brief, script, output_dir)
    review_decision = build_review_decision()
    review_summary = build_review_summary(brief, script, seedance)
    return {
        "brief": brief,
        "script": script,
        "storyboard": storyboard,
        "assets": assets,
        "seedance": seedance,
        "publish": publish,
        "review_decision": review_decision,
        "review_summary": review_summary,
        "ledger": build_ledger(brief),
    }
