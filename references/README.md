<!--
[INPUT]: 依赖 {各子目录参考材料} 的 {来源、职责与读取路径}
[OUTPUT]: 对外提供 {references 总索引}
[POS]: {references} 的 {知识库入口}，避免资料散乱难检索
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
-->

# References

## Structure

- `seedance/` -- 平台规格、提示词模式、时长策略
- `storyboard/` -- 叙事结构、素材编号、连续性规则
- `publishing/` -- 抖音发布流程、适配器边界
- `content-patterns/` -- Agent 内容层指南（相机/叙事/prompt 组装）
- `aesthetic-presets.json` -- 4 种美学预设定义

## Agent 内容层必读

Agent 填充骨架时，按 SKILL.md Enrichment Workflow 读取：

- `aesthetic-presets.json` -- 当前美学预设的视觉关键词、风格锚点、负面约束
- `content-patterns/camera-presets.md` -- purpose -> codec 默认映射
- `content-patterns/purpose-guide.md` -- 每个叙事目的的视觉/动作/音频指导
- `content-patterns/seedance-templates.md` -- prompt 组装公式与长视频续拍模式

## Imported Source Files

以下文件直接来自参考仓库，作为吸收和改造基底保留：

### From `MapleShaw/seedance2.0-prompt-skill`

- `seedance/production-pipeline-source.md`
- `seedance/long-video-strategy-source.md`
- `seedance/camera-codec-source.md`

### From `liangdabiao/Seedance2-Storyboard-Generator`

- `storyboard/structured-prompt-source.md`
- `storyboard/storyboard-workflow-source.md`

## Usage Rule

优先读取当前 skill 自己整理过的：

- `platform-specs.md`
- `prompting-patterns.md`
- `duration-boundaries.md`
- `video-type-duration-profiles.md`
- `story-structure.md`
- `asset-numbering.md`
- `continuity-rules.md`

只有在需要细节、模板或进一步吸收时，再读 `*-source.md`。
