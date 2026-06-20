<!--
[INPUT]: 依赖 {PRD、参考仓库能力与实现边界} 的 {包结构设计}
[OUTPUT]: 对外提供 {推荐目录结构、模块职责与依赖边界}
[POS]: {autodouyin-skill/topics} 的 {实现结构设计文档}，连接 PRD 与后续脚手架
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
-->

# Package Layout

Date: 2026-06-19
Status: Draft

## Goal

为新 Skill 设计一个能同时容纳：

- 核心 skill 文本能力
- 可执行脚本
- 结构化 schema
- 可选适配器入口

的最小目录结构。

## Design Principle

目录不是为了好看，而是为了把职责切开。

必须避免的坏味道：

1. 把全部知识写进一个巨型 `SKILL.md`
2. 把运行脚本、适配器、资料、样例揉在根目录
3. 把需要许可证隔离的适配器直接并入核心层

## Recommended Shape

```text
<skill-root>/
  SKILL.md
  agents/
    openai.yaml
  references/
    seedance/
      platform-specs.md
      prompting-patterns.md
      long-video-strategy.md
    storyboard/
      story-structure.md
      asset-numbering.md
      continuity-rules.md
    publishing/
      douyin-workflow.md
      adapter-boundary.md
  scripts/
    normalize-brief/
      README.md
      schema-notes.md
    compile-storyboard/
      README.md
      schema-notes.md
    validate-jobs/
      README.md
      schema-notes.md
  schemas/
    brief.schema.json
    script.schema.json
    storyboard.schema.json
    asset-manifest.schema.json
    seedance-job.schema.json
    publish-job.schema.json
    run-ledger.schema.json
  examples/
    brief/
    outputs/
  adapters/
    README.md
    seedance-executor.md
    douyin-publisher.md
```

## Why This Shape

### `SKILL.md`

只保留：

- 触发条件
- 工作流导航
- 何时读取哪个 references
- 何时调用哪个脚本 / 消费哪个 schema

不保留：

- 大量平台细节
- 长篇样例库
- 全部提示词知识

### `references/`

承担知识库角色，按职责拆三组：

1. `seedance/`
2. `storyboard/`
3. `publishing/`

这样能让另一个 AI 按需读取，不会一次吞下全部上下文。

### `schemas/`

这是“通用可被各种 AI 使用”的关键层。

如果没有 schema，这个 Skill 依旧会退化成“看上去能跑，其实只能在当前会话里跑”的半成品。

### `scripts/`

第一版建议只放可复用、可验证的编译脚本，不放平台自动化脚本。

原因：

- 平台自动化脚本更脆，变化更快
- 编译逻辑更稳定，更适合先固化

### `adapters/`

第一版不一定放真实代码，但至少要放：

- 适配器契约
- 运行入口约定
- 所需环境

如果之后决定接入真实实现，再把这里扩成独立子包或桥接说明。

## Recommended Minimal Publishable v1

如果目标是尽快做出“可发布 skill”，最小结构可以先缩成：

```text
<skill-root>/
  SKILL.md
  agents/openai.yaml
  references/
  schemas/
  examples/
```

然后把真正的执行层先留在 `adapters/README.md` 里说明，不急着把执行代码一口气并入。

## Merge Strategy For Three Reference Repos

### From `seedance2.0-prompt-skill`

优先吸收：

- `SKILL.md` 的分层思路
- `references/` 结构
- 平台约束整理方式

### From `Seedance2-Storyboard-Generator`

优先吸收：

- 故事到分镜的产物流
- 编号规范
- 连续性检查规则

### From `douyin-upload-mcp-skill`

优先吸收：

- adapter contract
- 登录状态机描述
- 发布输入输出定义

谨慎处理：

- 真实浏览器自动化代码
- MCP server 代码
- 许可证边界

## Implementation Notes

### Option A

Skill 仓库只放核心和契约，适配器作为外部依赖。

优点：

- 最干净
- 最容易发布
- 许可证风险最低

缺点：

- 端到端体验依赖外部安装

### Option B

Skill 仓库包含核心 + 自有适配器桥接代码。

优点：

- 用户体验更完整

缺点：

- 目录复杂度上升
- 许可证与平台漂移风险上升

当前推荐：**先走 Option A，再决定是否需要向 Option B 扩展。**
