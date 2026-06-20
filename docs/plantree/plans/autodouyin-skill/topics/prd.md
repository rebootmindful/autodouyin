<!--
[INPUT]: 依赖 {参考仓库研究、用户目标与当前决策} 的 {产品定义}
[OUTPUT]: 对外提供 {autodouyin-skill 的正式 PRD}
[POS]: {autodouyin-skill/topics} 的 {核心产品文档}，指导后续实现
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
-->

# PRD: autodouyin-skill

Date: 2026-06-19
Status: Draft / implementation-prep

## 1. Product Summary

`autodouyin-skill` 是一个可发布、可移植的通用 Skill。它接收用户给定目标或 brief，自动完成：

1. 生成视频脚本
2. 生成分镜
3. 生成 Seedance 2.0 可执行任务规格
4. 在外部执行适配器可用时触发视频生成
5. 在 Douyin 发布适配器可用时自动上传并发布

它不是单一平台脚本，也不是单一 Agent 的私有 prompt。它的核心是一个可被多种 AI 复用的内容生产与发布编排层。

## 2. Problem

现在的能力通常分散在三类资产里：

1. 提示词 Skill
   - 擅长写 prompt，不擅长产物编排和发布
2. 分镜方法论仓库
   - 擅长创作流程，不擅长执行自动化
3. 平台自动化仓库
   - 擅长发布，不擅长生成内容

用户需要的是一条端到端链路，而不是三套孤立能力。

## 3. Goals

### Primary Goals

1. 输入一句目标或一段 brief，输出可执行的视频生产方案。
2. 让脚本、分镜、素材清单、生成任务、发布任务之间有统一契约。
3. 允许“只生成方案”与“直接执行”两种模式共存。
4. 把 Douyin 发布能力做成可替换适配器，而不是绑定死在核心 Skill 里。
5. 让同一份产物可被多种 AI / Agent 消费。

### Success Criteria

1. 给定 brief，Skill 能稳定产出：
   - `script.md`
   - `storyboard.md`
   - `storyboard.json`
   - `asset-manifest.json`
   - `seedance-job.json`
   - `publish-job.json`
2. 在 `plan-only` 模式下，不依赖任何外部账户或算力即可完成方案产出。
3. 在适配器齐备时，可把 `seedance-job` 和 `publish-job` 跑通。
4. 失败信息能回传到具体阶段，而不是统一“执行失败”。

## 4. Non-Goals

1. 不做完整视频剪辑软件。
2. 不做通用社媒运营系统。
3. 不在 MVP 内覆盖 Douyin 以外的所有平台。
4. 不直接吸收 AGPL 仓库代码进入核心 Skill。
5. 不承诺绕过平台风控、版权审核或真人限制。

## 5. Target Users

### P0

- 会配置 CLI / MCP / 浏览器环境的 AI 工具高级用户
- 需要把内容策划、视频生成、发布串成一条链路的自动化使用者

### P1

- 有一定技术门槛承受能力的内容创作者团队

## 6. Core User Stories

1. 作为用户，我给一句“做一条关于 XX 的抖音视频”，希望得到可执行的脚本、分镜和生成任务。
2. 作为用户，我已经有图或故事，希望 Skill 只完成分镜和 Seedance 任务编译。
3. 作为用户，我已经有视频，希望 Skill 只完成抖音自动上传和发布。
4. 作为用户，我希望 Skill 支持 dry-run，先看方案和成本，再决定是否真的执行。

## 7. Modes

### Mode A: Plan Only

输入 brief，输出全部中间产物，不执行外部命令。

### Mode B: Generate Only

在已有脚本/分镜基础上，编译并执行 Seedance 任务，不负责发布。

### Mode C: Publish Only

在已有视频基础上，执行 Douyin 发布任务。

### Mode D: End-to-End

从 brief 一直跑到发布，但每一步都必须可中断、可确认、可回放。

## 8. Functional Requirements

### 8.1 Brief Intake

- 接收：
  - 目标
  - 主题
  - 视频时长
  - 比例
  - 风格
  - 素材条件
  - 是否立即执行
- 若信息不足，先补最小澄清，不直接空想实现。

### 8.2 Script Generation

- 将 brief 规范化为结构化故事框架。
- 支持短视频和连续剧情两种路径。

### 8.3 Storyboard Generation

- 产出按时间轴组织的分镜。
- 明确镜头内容、动作、运镜、情绪、音效。
- 对连续视频记录首尾衔接描述。

### 8.4 Asset Planning

- 生成角色 / 场景 / 道具清单。
- 使用稳定编号体系，如 `Cxx/Sxx/Pxx`。

### 8.5 Seedance Job Compilation

- 依据平台限制编译为 Seedance 任务规格：
  - 时长
  - 比例
  - `@图片/@视频/@音频` 引用
  - 分段 prompt
  - 连续性锁定语句

### 8.6 Execution Adapter Interface

- Skill 核心不直接假设某个 CLI 一定存在。
- 核心只生成标准任务；执行交给适配器。

### 8.7 Douyin Publish Adapter Interface

- 接收：
  - 视频路径
  - 标题
  - 简介
  - 标签
  - 发布时间
- 返回：
  - 登录状态
  - 发布状态
  - 页面截图或错误详情

### 8.8 Audit Trail

- 每次运行都要产出 run ledger：
  - 输入摘要
  - 产物路径
  - 执行步骤
  - 失败点
  - 外部结果

## 9. Intermediate Contract

核心不是 prompt，而是中间契约。

建议第一版采用 Markdown + JSON 双轨：

1. `brief.json`
2. `script.md`
3. `storyboard.md`
4. `storyboard.json`
5. `asset-manifest.json`
6. `seedance-job.json`
7. `publish-job.json`
8. `run-ledger.json`

原因：

- Markdown 适合人读和二次编辑。
- JSON 适合 Agent、脚本和适配器稳定消费。

## 10. Architecture Direction

### Core Principle

把系统拆成四层：

1. Knowledge Layer
   - 提示词规则、平台规格、样例、约束
2. Compilation Layer
   - brief -> script -> storyboard -> jobs
3. Execution Layer
   - Seedance / Dreamina adapter
4. Publishing Layer
   - Douyin adapter

### Why

这样做的好处是：

- 不把大 prompt 当系统
- 不把平台自动化和内容生成绑死
- 不把外部许可证污染核心 Skill

## 11. Recommended Package Shape

```text
<skill-root>/
  SKILL.md
  agents/
    openai.yaml
  references/
    seedance-platform.md
    storyboard-patterns.md
    douyin-publishing.md
  scripts/
    normalize_brief.*
    compile_storyboard.*
    validate_jobs.*
    run_ledger.*
  schemas/
    brief.schema.json
    storyboard.schema.json
    seedance-job.schema.json
    publish-job.schema.json
```

说明：

- `references/` 放可按需加载的知识，不把大段材料塞进 `SKILL.md`。
- `schemas/` 让 Skill 具备跨 AI 可移植性。
- 适配器若带许可证风险，放独立包或独立目录。

## 12. External Dependencies

### Required For Plan Only

- 无

### Required For Generation Execution

- Seedance / Dreamina 的可执行入口
- 可用账户与积分

### Required For Douyin Publishing

- 可控浏览器环境
- 登录态管理
- 账号人工验证能力

## 13. Reference-Derived Design Choices

1. 来自 `seedance2.0-prompt-skill`
   - Skill 应采用 references 分层，而不是单文件巨型说明。
   - 执行必须是可选步骤，不默认消耗外部资源。

2. 来自 `Seedance2-Storyboard-Generator`
   - 脚本、素材清单、分镜应当是独立产物。
   - 编号系统和尾帧衔接是必须项。

3. 来自 `douyin-upload-mcp-skill`
   - 发布自动化要有独立适配器边界。
   - 登录是多步状态机，不是一次性工具调用。

## 13.1 User Direction Confirmed

2026-06-19 用户明确表达：

- 希望新产品直接吸收三个参考源的现有能力，而不是完全从零实现。
- 接受“有 adapter”的产品形态。

这意味着实现策略应偏向“组合与裁剪”，而不是“纯原创重建”。
但组合不等于无边界拼接，仍需处理：

- 许可证边界
- 中间契约统一
- 运行入口统一
- 适配器与核心 Skill 的责任分离

## 14. Risks And Mitigations

### R1. AGPL License Contamination

- 风险：直接复用 `douyin-upload-mcp-skill` 代码会改变分发义务。
- 规避：只学接口与流程，不在核心 Skill 内直接吸收其代码。

### R2. Platform Drift

- 风险：抖音页面结构、Seedance CLI 参数都会变。
- 规避：把外部平台能力放适配层；核心 Skill 只持有稳定任务契约。

### R3. Execution Cost

- 风险：视频生成重试成本高。
- 规避：默认 `plan-only`；执行前展示成本和依赖。

### R4. False Portability

- 风险：名义上“通用”，实则只能被某个 Agent 使用。
- 规避：所有关键中间产物结构化，避免依赖单一会话内隐知识。

## 15. MVP Recommendation

### Phase 1

- 只做 Skill 核心
- 跑通：
  - brief intake
  - script/storyboard generation
  - asset manifest
  - seedance job
  - publish job
  - run ledger

### Phase 2

- 接 Seedance 执行适配器

### Phase 3

- 接 Douyin 发布适配器

### Phase 4

- 打磨发布形态、校验、样例和文档

## 16. Acceptance Criteria

满足以下条件，才算“可以进入实现”：

1. 范围明确：
   - 核心 Skill 做什么
   - 适配器做什么
2. 产物明确：
   - 中间文件有哪些
   - 每个文件给谁消费
3. 风险明确：
   - 许可证
   - 平台漂移
   - 登录交互
   - 成本
4. 验证路径明确：
   - 先 dry-run
   - 再单环节执行
   - 最后端到端

## 17. Key Judgment

这个产品的正确形态不是“一个会写 prompt 的 Skill”，而是“一个把内容规划、任务编译、外部执行和平台发布解耦的 Skill 编排层”。
