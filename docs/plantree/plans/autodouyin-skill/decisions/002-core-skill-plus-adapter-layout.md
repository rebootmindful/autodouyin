<!--
[INPUT]: 依赖 {用户方向、PRD 与参考仓库职责差异} 的 {结构性实现选择}
[OUTPUT]: 对外提供 {核心 skill 与 adapter 的布局决策}
[POS]: {autodouyin-skill/decisions} 的 {稳定结构决策}
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
-->

# Core Skill Plus Adapter Layout

Date: 2026-06-19

## Context

用户已经确认新产品接受 adapter 形态，并倾向复用三个参考仓库的现有能力。

三个参考源分别属于：

- Skill/知识层
- 工作流/产物层
- 平台自动化适配层

如果直接把三者糊成一个平面目录，后续会出现：

- 许可证边界不清
- 平台漂移影响核心
- `SKILL.md` 失控膨胀

## Decision

采用：

- `core skill`
- `structured schemas`
- `optional adapters`

三层布局。

具体原则：

1. 核心 Skill 负责内容规划和任务编译。
2. 结构化 schema 负责通用可移植性。
3. 适配器负责对接外部平台执行与发布。
4. 抖音自动发布能力只以 adapter boundary 形式接入。

## Consequences

### Positive

- 可以最大化复用三份参考源的优点。
- 后续可以替换发布平台或视频执行平台。
- 核心 skill 可先发布，不被浏览器自动化阻塞。

### Negative

- 第一版端到端体验需要更多组装工作。
- 文档和契约设计工作量上升。

## Follow-up

- 先完成 `package-layout` 和 `contracts-and-schemas`。
- 再决定 skill 初始化位置与名称。
