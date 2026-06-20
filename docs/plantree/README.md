<!--
[INPUT]: 依赖 {baseline 与 plans} 的 {事实基线、计划根与索引链接}
[OUTPUT]: 对外提供 {plantree 入口、权威顺序、活跃计划注册}
[POS]: {docs/plantree} 的 {规划总索引}，是跨会话恢复与导航的第一入口
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
-->

# Plan Tree

## Purpose

这里保存 `autodouyin` 的规划权威状态。当前仓库仍处于规划阶段，尚未进入正式实现。

## Authority Order

1. 根目录 `CLAUDE.md`
2. 本文件
3. `baseline/` 当前事实
4. `plans/autodouyin-skill/` 当前方案的 README、roadmap、decisions、open questions

## Read Path

1. 先读 [baseline/README.md](./baseline/README.md)
2. 再读 [plans/autodouyin-skill/README.md](./plans/autodouyin-skill/README.md)
3. 恢复会话时补读：
   - [plans/autodouyin-skill/implementation-status.md](./plans/autodouyin-skill/implementation-status.md)
   - [plans/autodouyin-skill/roadmap.md](./plans/autodouyin-skill/roadmap.md)

## Baseline

- [baseline/module-map.md](./baseline/module-map.md)
- [baseline/runtime-flows.md](./baseline/runtime-flows.md)
- [baseline/storage-and-state.md](./baseline/storage-and-state.md)
- [baseline/test-and-release-gates.md](./baseline/test-and-release-gates.md)
- [baseline/risk-hotspots.md](./baseline/risk-hotspots.md)

## Active Plans

| Plan | Status | Scope | Entry |
|---|---|---|---|
| `autodouyin-skill` | In Progress | 通用 Skill 的 PRD、架构边界、执行路径 | [plans/autodouyin-skill/README.md](./plans/autodouyin-skill/README.md) |

## Ideas Inbox

- [ideas/inbox.md](./ideas/inbox.md)
