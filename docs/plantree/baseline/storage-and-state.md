<!--
[INPUT]: 依赖 {当前仓库事实与目标产物链路} 的 {状态存储需求}
[OUTPUT]: 对外提供 {当前无状态、计划状态与产物边界}
[POS]: {baseline} 的 {状态与存储地图}，指导后续目录设计
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
-->

# Storage And State

Date: 2026-06-19

## Current

- 当前仅有 Markdown 规划状态。
- 没有运行时数据库、缓存或产物目录。

## Planned State

建议把状态分成三类：

1. Durable planning state
   - `docs/plantree/`
2. Skill source
   - skill 定义、参考资料、脚本
3. Run artifacts
   - 输入 brief
   - 结构化脚本/分镜
   - 素材清单
   - Seedance 任务规格
   - 生成视频路径 / 发布结果
   - 审计日志

## Boundary

- 运行产物不应混入根目录。
- 用户密钥、cookie、登录态不进 Git 跟踪目录。
- 平台登录态与浏览器 profile 必须交由适配器管理，不写入 Skill 文档层。
