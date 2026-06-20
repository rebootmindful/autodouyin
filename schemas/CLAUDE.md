<!--
[INPUT]: 依赖 {根目录 CLAUDE.md 与当前契约实现} 的 {数据对象边界}
[OUTPUT]: 对外提供 {schemas 子树的局部地图与契约规则}
[POS]: {schemas} 的 {L2 局部地图}，统领 JSON 契约与校验入口
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
-->

# CLAUDE.md

## Scope

`schemas/` 保存当前闭环主路径的结构契约。

## Contracts

- `brief.schema.json`
- `script.schema.json`
- `storyboard.schema.json`
- `asset-manifest.schema.json`
- `seedance-job.schema.json`
- `publish-job.schema.json`
- `run-ledger.schema.json`
- `review-decision.schema.json`

## Rules

- schema 必须服务真实运行入口，而不是只服务历史样例。
- 任一字段新增、删除或状态枚举变化，都要同步：
  - 对应脚本实现
  - `validate_artifacts.py`
  - README / plan-tree 中的主路径描述
