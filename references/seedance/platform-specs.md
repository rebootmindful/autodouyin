<!--
[INPUT]: 依赖 {Seedance 平台约束} 的 {输入输出限制与引用规则}
[OUTPUT]: 对外提供 {任务编译时必须遵守的平台规格}
[POS]: {references/seedance} 的 {平台规格参考}
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
-->

# Seedance Platform Specs

## Core Limits

- 单次视频时长：`4-15s`
- 图片输入：最多 `9` 张
- 视频输入：最多 `3` 个
- 音频输入：最多 `3` 个
- 图/视频/音频合计：最多 `12` 个文件

## Official Reference Names

- 图片：`@图片1` 到 `@图片9`
- 视频：`@视频1` 到 `@视频3`
- 音频：`@音频1` 到 `@音频3`

不要自造命名。

## Generation Entry Choices

1. 单图起步
   - 适合首帧明确、素材少的场景
2. 全能参考
   - 适合多图、多视频、连续剧情和风格锁定

## Hard Constraints

- prompt block 必须覆盖完整时长
- 连续视频要显式写 continuity lock
- 复杂长视频不要假装一条 prompt 能一步做完
