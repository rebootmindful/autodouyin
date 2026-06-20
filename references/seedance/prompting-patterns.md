<!--
[INPUT]: 依赖 {分镜对象与 Seedance 任务需求} 的 {提示词组织模式}
[OUTPUT]: 对外提供 {短视频、连续视频与多段任务的编译模式}
[POS]: {references/seedance} 的 {提示词结构参考}
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
-->

# Seedance Prompting Patterns

## <= 15s

优先用时间轴块：

- `0-3s`
- `3-6s`
- `6-9s`
- `9-12s`
- `12-15s`

每块写四件事：

1. 画面
2. 动作
3. 镜头
4. 音效 / 对白

## > 15s

不要直接拉长 prompt。要拆成：

1. 段落目标
2. 连续性锁定
3. 分段生成 / 延长策略

## Prompt Compilation Rule

从 `storyboard.shots[]` 编译 `prompt_blocks[]` 时：

- `visual` 变成画面主句
- `camera` 变成运镜句
- `action` 变成动作句
- `audio` 变成声音句
- `assets` 变成 `@图片/@视频/@音频` 引用表

## Continuity Lock

连续片段至少锁定三类信息：

1. 风格
2. 主角外观
3. 场景关系
