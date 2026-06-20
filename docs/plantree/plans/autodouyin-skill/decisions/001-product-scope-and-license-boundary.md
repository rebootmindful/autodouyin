<!--
[INPUT]: 依赖 {用户目标与参考仓库风险} 的 {需要稳定下来的方向}
[OUTPUT]: 对外提供 {产品范围与许可证边界决策}
[POS]: {autodouyin-skill/decisions} 的 {稳定决策记录}
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
-->

# Product Scope And License Boundary

Date: 2026-06-19

## Context

目标产品需要同时覆盖：

- 内容规划
- Seedance 任务生成
- 视频生成执行
- 抖音发布自动化

参考仓库中，抖音上传能力对应的 `douyin-upload-mcp-skill` 明确采用 `AGPL-3.0`。如果把它的代码直接吸收到核心 Skill，会立刻引入许可证和分发策略问题。

## Decision

1. 核心产品定义为：
   - 通用 Skill 编排层
   - 负责 brief -> script -> storyboard -> jobs
2. 视频生成执行和抖音发布都定义为 adapter boundary。
3. `douyin-upload-mcp-skill` 只作为能力学习来源，不直接复制进核心 Skill。
4. MVP 必须支持 `plan-only`，不能把外部执行当成唯一模式。

## Consequences

### Positive

- 核心 Skill 可保持通用和可移植。
- 许可证风险被隔离在适配器决策之外。
- 平台漂移不会把整个 Skill 一起拖垮。

### Negative

- 首版端到端可用性会晚于“直接拼代码”。
- 需要额外定义 adapter contract 和中间 schema。

## Follow-up

- 用户确认后，下一步优先定义 schema 和 Skill 骨架。
