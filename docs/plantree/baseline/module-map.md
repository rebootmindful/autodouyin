<!--
[INPUT]: 依赖 {当前仓库目录事实} 的 {已存在模块、缺失模块与计划模块}
[OUTPUT]: 对外提供 {模块现状清单与计划中的模块轮廓}
[POS]: {baseline} 的 {模块地图}，用于区分现状与未来设计
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
-->

# Module Map

Date: 2026-06-19

## Current

- 根目录：`CLAUDE.md`
- Skill 主入口：`SKILL.md`
- UI 配置：`agents/openai.yaml`
- 知识层：`references/`
- 编译脚本：`scripts/`
- 契约层：`schemas/`
- 示例层：`examples/`
- 适配器契约层：`adapters/`
- vendored 抖音 adapter：`adapters/douyin-upload-vendor/`
- 规划树：`docs/plantree/`
- 正式执行代码模块：`None`

## Planned

以下是 PRD 阶段拟定的目标模块，不代表已实现：

1. `skill/entry`
   - `SKILL.md`
   - `agents/openai.yaml`
2. `references`
   - Seedance 提示词规则
   - 分镜模板
   - 发布策略与合规约束
3. `scripts`
   - brief 规范化
   - 分镜/任务清单编译
   - 运行账本与 dry-run 校验
4. `adapters`
   - Seedance / Dreamina 执行适配器
   - Douyin 发布适配器
5. `artifacts`
   - 中间产物与运行日志的约定目录

## Unknown / Needs Inventory

- 最终是纯 Skill 还是 Skill + MCP/CLI 混合包，待实现决策确认。
