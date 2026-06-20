<!--
[INPUT]: 依赖 {核心 Skill 与外部执行层} 的 {责任边界}
[OUTPUT]: 对外提供 {哪些属于核心，哪些属于 adapter}
[POS]: {references/publishing} 的 {边界约束参考}
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
-->

# Adapter Boundary

## Core Skill Owns

- brief 规范化
- script / storyboard 生成
- asset manifest
- seedance-job
- publish-job
- run-ledger

## Adapter Owns

- 调 CLI / MCP
- 浏览器登录态
- 上传 / 发布动作
- 外部错误回传

## License Rule

抖音自动发布参考实现存在 `AGPL-3.0` 风险。

结论：

- 可以学习其接口与流程
- 不应把其代码无边界揉进核心 Skill
