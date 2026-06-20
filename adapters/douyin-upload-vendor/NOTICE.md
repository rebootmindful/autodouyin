<!--
[INPUT]: 依赖 {vendored adapter 源码与上游仓库信息} 的 {来源、许可证和使用边界}
[OUTPUT]: 对外提供 {vendor 来源说明与改造边界}
[POS]: {adapters/douyin-upload-vendor} 的 {来源声明}，防止许可证与职责混淆
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
-->

# Vendor Notice

本目录包含从下列上游仓库引入的抖音发布自动化实现：

- Repository: `WJZ-P/douyin-upload-mcp-skill`
- Source: https://github.com/WJZ-P/douyin-upload-mcp-skill
- License: `AGPL-3.0`

## Import Policy

- 当前采取 **vendored adapter** 方式引入。
- 保留上游 `LICENSE`。
- 不把这里的代码视作核心 Skill 自有实现。

## Intended Use

此目录只承担：

1. Douyin 发布自动化 adapter
2. MCP server / browser daemon / CDP workflow

不承担：

1. 脚本与分镜编译
2. Seedance 任务编译
3. 核心 Skill 的知识层

## Local Adaptation Rule

后续只做：

- 路径适配
- 运行说明适配
- 与当前 Skill 的 job contract 对齐

尽量不对其业务逻辑做无必要重写。
