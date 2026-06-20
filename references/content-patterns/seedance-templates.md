# Seedance Prompt Templates

prompt 组装模式与长视频续拍规则。

## Prompt 组装公式

```
[type_intro] [style_lock] [time_range+visual] [camera] [action] [audio] [extra_tags]
```

## Type Intro 模式

| video_type         | 开头语                                           |
|--------------------|--------------------------------------------------|
| workflow-explainer | 工作流演示视频，强调信息清晰、结果可见、过程有节奏 |
| product-demo       | 商业产品演示视频，强调卖点直给、UI清晰、动作利落   |
| narrative-story    | 剧情短片风格，强调情绪起伏、人物状态变化和结果反转 |
| character-action   | 角色动作展示，强调姿态建立、动作升级和高潮定格     |
| space-tour         | 沉浸式空间漫游，强调路径、空间关系和节点展示       |

## Style Lock 组装

1. 从 `references/aesthetic-presets.json` 取当前预设的 `seedance_style_anchor` 作为基底
2. 追加: "统一视觉风格，画面干净，避免风格漂移"
3. 追加: 角色一致性锁定（同一角色不换人不变脸）
4. 追加: 场景一致性锁定（同一场景不突然切换）

## Negative Constraints 组装

通用（始终包含）:
- 禁止风格漂移
- 禁止角色变脸或换人
- 禁止突然偏色
- 禁止新增无关人物
- 禁止光线突变
- 禁止出现文字、字幕、LOGO、水印

预设特有（从 `aesthetic-presets.json` 的 `seedance_negative_additions` 取）

## Type Prompt Tags

| video_type         | 标签                                   |
|--------------------|----------------------------------------|
| workflow-explainer | 信息层级清楚, 结果面板可读, 过程到结果连续 |
| product-demo       | 商业广告节奏, 卖点一眼可见, 界面与动效高级干净 |
| narrative-story    | 人物情绪递进, 压力到释放, 剧情反转明确   |
| character-action   | 动作动势连续, 角色姿态强, 高潮击中感明确 |
| space-tour         | 空间路径稳定, 节点切换自然, 光线与材质层次清晰 |

## Slot Plan

固定映射:
- @图片1 -> C01 (主体一致性参考)
- @图片2 -> S01 (场景或空间背景参考)
- @图片3 -> P01 (关键道具/结果卡片参考)

## 长视频续拍模式

### segmented-extension (16-60s)

首段 (segment-base): 正常生成，无 @视频1 引用。
后续段 (segment-extension):
- 开头: "将@视频1延长{N}秒，接续上一段最后一帧的构图与角色状态，前1秒仅保留微动作和环境流动。"
- video_refs 包含 "@视频1"
- 每段重复风格锁定 + 角色锁定 + 场景锁定

### scene-split-edit-pipeline (>60s)

按 scene_id 分组:
- 每个 scene 的首段 (scene-base): 正常生成
- 每个 scene 的后续段 (scene-extension): 用 @视频1 续拍
- scene 之间用后期拼接，不跨 scene 延长
- seedance-job 需包含 scene_plan

## 平台约束提醒

- 单次生成: 4-15秒
- 图片 <= 9, 视频 <= 3, 音频 <= 3, 合计 <= 12
- @命名: @图片1-9, @视频1-3, @音频1-3
