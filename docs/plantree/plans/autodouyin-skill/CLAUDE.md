<!--
[INPUT]: 依赖 {上级 plantree 与本计划文件} 的 {目标、状态、决策与问题}
[OUTPUT]: 对外提供 {autodouyin-skill 计划根的局部地图}
[POS]: {plans/autodouyin-skill} 的 {L2 计划地图}，协调 PRD、路线图与开放问题
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
-->

# CLAUDE.md

## Scope

本计划根负责 `autodouyin-skill` 的产品定义、实现准备度和执行状态。

## Files

- `README.md`：计划范围和读取顺序
- `roadmap.md`：Done / In Progress / Next / Deferred
- `implementation-status.md`：当前阶段与下一步
- `open-questions.md`：未决问题
- `topics/prd.md`：正式 PRD
- `topics/reference-repo-analysis.md`：参考仓库研究结果
- `decisions/`：稳定决策

## Rule

- 在 `open-questions.md` 的核心问题没有收敛前，不进入主实现。
