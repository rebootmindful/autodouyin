<!--
[INPUT]: 依赖 {docs/plantree} 的 {规划入口、基线与决策记录}
[OUTPUT]: 对外提供 {项目宪法、全局地图、当前阶段约束}
[POS]: {仓库根目录} 的 {L1 全局地图}，统领实现前的规划与后续执行
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
-->

# CLAUDE.md

## Purpose

本仓库用于孵化一个可发布的通用 Skill：接收用户给定目标，自动产出视频脚本与分镜，生成 Seedance 2.0 可执行的提示词/任务规格，并在具备外部适配器时完成视频生成与抖音发布。

当前阶段已进入实现与闭环打通期。主目标是把“输入视频目标 -> 生成审核包 -> 用户批准 -> Seedance 生成 -> 长视频组装”收敛成稳定主链。

## Authority

1. 根目录 `CLAUDE.md` 是项目宪法和全局地图。
2. `docs/plantree/README.md` 是规划入口与状态登记处。
3. `docs/plantree/plans/autodouyin-skill/` 是当前工作流的唯一活动计划根。

当规划文件与实现不一致时，以最新代码为事实源，再回写文档。

## Current State

- 仓库已完成三层架构重构。
- 当前主链已收敛为：Python 结构层 -> Python 确定性内容编译 -> Python 校验/执行/组装层
- 已存在：
  - `SKILL.md` -- Skill 主入口
  - `scripts/` -- 结构层 (`compile_skeleton.py`) + 内容编译层 (`compiler_content.py`) + 校验层 (`validate_artifacts.py`) + 执行层 (`execute_seedance.py`) + 组装层 (`assemble_video.py`) + 主入口 (`run_pipeline.py`)
  - `references/` -- 知识层 + content-patterns/ + aesthetic-presets.json
  - `schemas/` -- 8 份 JSON Schema 契约（含 `review-decision`）
  - `examples/` -- 7 个 brief + 9 套完整产物 + skeleton 样例
  - `adapters/` -- Seedance executor 契约 (含 Dreamina CLI 映射) + Douyin publisher
- 已确认外部参考源：
  - `WJZ-P/douyin-upload-mcp-skill`
  - `liangdabiao/Seedance2-Storyboard-Generator`
  - `MapleShaw/seedance2.0-prompt-skill`
  - `op7418/Seedance-Product-Video` (美学预设系统)
- 美学预设：Apple Cupertino / Microsoft Fluent / Bauhaus Zen / Vercel Dark
- Dreamina CLI 首选集成路径：`seedance` npm 包 (MIT, Rust, Ark API)
- 身份一致性：锚图自动检测 + AI 闭环 (见 `references/content-patterns/anchor-image-strategy.md`)。无产品图时自动调用图片生成 API 生成定妆照 → 注册 C01 → [Image1] I2V 锚定

## Planned Deliverable Shape

当前实现和后续目标均以以下结构为准：

- Skill 主体：`SKILL.md`（含三层架构指令）、`agents/openai.yaml`
- 主链脚本：`scripts/`（`compile_pipeline.py` / `run_pipeline.py` / `validate_artifacts.py` / `execute_seedance.py` / `execute_official_video.py` / `compile_from_prompts.py` / `assemble_video.py`）
- 知识层：`references/`（含 content-patterns/ + aesthetic-presets.json）
- 结构化契约：`schemas/`（8 份 JSON Schema）
- 样例：`examples/`（brief + skeleton + 完整产物）
- 中间产物契约：brief -> script/storyboard/assets/seedance-job/publish-job/review-decision/run-ledger
- 外部适配器：Seedance/Dreamina 执行适配器、Douyin 发布适配器

## Working Rules

- 规划相关内容全部落在 `docs/plantree/`。
- 当前实现优先级：减少链路、减少状态漂移、减少临时产物。
- 任一结构性决策变化，都要同步更新：
  - 本文件
  - `docs/plantree/README.md`
  - 当前 plan 根的 README / roadmap / decisions

## Licensing

本仓库采用分层许可证策略：

1. **核心 Skill（根目录、`scripts/`、`schemas/`、`references/`、`examples/`、`docs/`）**：MIT License。可自由使用、修改、分发，无需保留相同许可证。

2. **外部适配器边界（`adapters/`）**：
   - `adapters/douyin-upload-vendor/` 引入自 `WJZ-P/douyin-upload-mcp-skill`，采用 **AGPL-3.0**。
   - 此目录与核心 Skill 隔离，不承担脚本/分镜编译职责。
   - 分发时需保留上游 LICENSE 和 NOTICE.md。

3. **分发规则**：
   - 核心 Skill 可独立于 AGPL 组件分发。
   - 若将 `adapters/douyin-upload-vendor/` 与核心 Skill 一起分发，整体需遵守 AGPL-3.0 条款。
   - 修改 vendor 代码时，需在 NOTICE.md 中记录变更。
