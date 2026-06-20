<!--
[INPUT]: 依赖 {plugin.json、assets 与 skills/} 的 {Codex 插件展示与入口配置}
[OUTPUT]: 对外提供 {插件元数据、图标与截图约束}
[POS]: {.codex-plugin} 的 {插件清单层}，让 skill 仓库可被 Codex 插件体系识别
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
-->

# CLAUDE.md

## Scope

`.codex-plugin/` 保存 Codex 插件元数据。

## Rules

- `plugin.json` 必须只声明仓库里真实存在的 `skills/` 与 `assets/`。
- 不写占位 URL，不写仓库里不存在的 companion 文件。
- 图标、截图替换后要重新跑插件验证器。
