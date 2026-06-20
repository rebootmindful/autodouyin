<!--
[INPUT]: 依赖 {目标发布形态与外部平台约束} 的 {验证门槛与发布前条件}
[OUTPUT]: 对外提供 {测试、验收、发布门槛}
[POS]: {baseline} 的 {验证门}，定义“可发布”最低标准
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
-->

# Test And Release Gates

Date: 2026-06-19

## Current

- 当前没有可执行实现，因此没有自动化测试。

## Planned Minimum Gates

1. 结构正确
   - Skill 目录通过 `quick_validate.py`
   - `agents/openai.yaml` 与 `SKILL.md` 一致
2. 产物正确
   - 给定 brief 能稳定产出脚本、分镜、Seedance 任务规格
3. 模式正确
   - `plan-only` 不触发外部消耗
   - `execute` 前明确展示成本和外部依赖
4. 适配器正确
   - Seedance 执行适配器支持 dry-run
   - Douyin 发布适配器支持登录检查和失败回传
5. 文档正确
   - PRD、决策、开放问题与实现一致

## Release Bar

“可发布”至少意味着：

- 对外依赖写清楚
- 许可证边界写清楚
- 敏感操作需要显式确认
- 失败能回传，不是静默卡死
