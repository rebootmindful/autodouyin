<!--
[INPUT]: 依赖 {仓库现状与外部调研} 的 {当前事实、未知项与边界}
[OUTPUT]: 对外提供 {baseline 读取入口与事实范围}
[POS]: {docs/plantree/baseline} 的 {基线索引}，定义当前仓库“是什么”
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
-->

# Baseline

## Current Truth

- 获取时间：2026-06-19
- 当前仓库为空工作区，尚无实现代码。
- 当前可靠资产是规划文档与外部仓库调研结果。

## Files

- [module-map.md](./module-map.md)：当前模块现状
- [runtime-flows.md](./runtime-flows.md)：当前/计划流程边界
- [storage-and-state.md](./storage-and-state.md)：当前/计划状态存储
- [test-and-release-gates.md](./test-and-release-gates.md)：验证与发布门槛
- [risk-hotspots.md](./risk-hotspots.md)：高风险项

## Evidence Boundary

未来任何实现判断都应先回到代码事实；若仓库仍未实现，则以本基线记录的“Unknown / Planned”状态为准。
