<!--
[INPUT]: 依赖 {根目录 skill 与插件元数据} 的 {plugin-packaged 技能入口}
[OUTPUT]: 对外提供 {skills/ 下的可安装 skill 包装层}
[POS]: {skills} 的 {插件封装层}，服务 Codex plugin 入口而不替代根目录 skill
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
-->

# CLAUDE.md

## Scope

`skills/` 保存给 Codex 插件元数据使用的 skill 包装层。

## Rules

- 这里的 skill 是根目录 `SKILL.md` 的插件包装版，不另起业务分叉。
- 路径必须相对插件根正确指向 `../../scripts`、`../../references`、`../../adapters`。
- 如根目录主链变更，先改根目录 `SKILL.md`，再同步这里的包装版。
