<!--
[INPUT]: 依赖 {brief、脚本主链与展示需求} 的 {真实样例输入与产物}
[OUTPUT]: 对外提供 {可验证样例、showcase 样例与对应说明}
[POS]: {examples} 的 {样例层}，连接 README 展示、测试口径与真实产物
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
-->

# CLAUDE.md

## Scope

`examples/` 保存两类正式样例：

- `brief/`：输入样例
- `showcase-*` 与其他 `outputs*`：真实运行产物样例

## Rules

- 示例目录中的内容必须能被 README、测试或展示资产引用。
- 新样例优先服务当前公开主链，不再为历史 skeleton/enrichment 流程补样例。
- 若样例由脚本重建，保留对应命令或说明文件，避免样例失去来源。
