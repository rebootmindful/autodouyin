<!--
[INPUT]: 依赖 {根目录 CLAUDE.md} 的 {项目目标与规划治理}
[OUTPUT]: 对外提供 {plantree 子树的局部地图与维护规则}
[POS]: {docs/plantree} 的 {L2 规划模块地图}，连接基线、计划与索引
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
-->

# CLAUDE.md

## Scope

`docs/plantree/` 保存本仓库的规划状态、基线、决策、开放问题和执行准备度。

## Structure

- `README.md`：规划入口、注册表、读取顺序
- `baseline/`：当前仓库事实与高风险边界
- `plans/`：具体计划根
- `ideas/`：低承诺想法池

## Rules

- 只把 durable planning state 放在这里。
- `baseline/` 记录事实；未来设计要明确标注为 `Planned`。
- 活跃方案统一登记到根 `README.md`。
- 新增计划根时必须补对应 `CLAUDE.md` 或由上级覆盖解释。
