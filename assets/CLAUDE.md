<!--
[INPUT]: 依赖 {examples/showcase-* 与公开展示需求} 的 {首屏截图、GIF 与图标资产}
[OUTPUT]: 对外提供 {README 首屏展示图、插件/Agent 图标与可传播结果卡}
[POS]: {assets} 的 {展示资产层}，服务公开安装、传播与 UI 元数据
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
-->

# CLAUDE.md

## Scope

`assets/` 保存公开展示资产：

- README 首屏用的 PNG / GIF
- Agent / Plugin 图标
- 可传播的结果卡

## Rules

- 展示资产必须来自真实样例或真实命令回放，不做摆拍假图。
- 若资产由脚本生成，优先复用 `scripts/build_showcase_assets.py`。
- 任何新增或替换的展示资产，都要同步检查 README 引用是否仍然有效。
