<!--
[INPUT]: 依赖 {外部仓库文档与源码片段} 的 {事实提取与能力对比}
[OUTPUT]: 对外提供 {参考仓库能力矩阵、优点提炼与边界判断}
[POS]: {autodouyin-skill/topics} 的 {调研笔记}，为 PRD 提供证据
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
-->

# Reference Repo Analysis

Date: 2026-06-19

## Sources

1. `WJZ-P/douyin-upload-mcp-skill`
   - README: https://github.com/WJZ-P/douyin-upload-mcp-skill
   - `src/mcp-server.js`
   - `src/douyin-ops.js`
   - `package.json`
2. `liangdabiao/Seedance2-Storyboard-Generator`
   - README: https://github.com/liangdabiao/Seedance2-Storyboard-Generator
   - `CLAUDE.md`
   - `docs/流程.md`
   - `docs/剧本和分镜.md`
   - 示例项目文档
3. `MapleShaw/seedance2.0-prompt-skill`
   - README: https://github.com/MapleShaw/seedance2.0-prompt-skill
   - `SKILL.md`
   - `references/production-pipeline.md`
   - `references/platform-specs.md`
   - `references/cli-integration.md`
   - `references/examples.md`

## Facts

### A. douyin-upload-mcp-skill

Status: 已证实

- 提供 MCP 工具集，而不是单纯 prompt skill。
- 能力覆盖：视频发布、图文发布、登录检查、页面截图、导航、浏览器信息。
- 交互方式：通过 CDP + Puppeteer 操控抖音创作者平台网页。
- 架构清晰：`mcp-server -> index -> browser -> douyin-ops -> operator -> Chrome/CDP`。
- 登录是多步推进，不是单次同步调用。
- 许可证：`AGPL-3.0`。

优点：

- 把“发布自动化”做成了独立能力面。
- 业务层和原子操作层分离，适合学习其接口切面。
- 已经把登录态管理、二维码截图、短信验证推进考虑进去了。

不足 / 不可直接照搬点：

- 强绑定抖音创作者平台 DOM。
- 受前端页面漂移影响大。
- `AGPL-3.0` 让直接代码复用变成许可证风险。

### B. Seedance2-Storyboard-Generator

Status: 已证实

- 更像方法论仓库，不是工程化 Skill 包。
- 核心强项是把“故事 -> 剧本 -> 素材清单 -> 分镜 -> 连续视频”的生产链讲清楚。
- 对中间产物格式很有帮助：
  - `[标题]_剧本.md`
  - `[标题]_素材清单.md`
  - `[标题]_E[集数]_分镜.md`
- 对素材编号规范清晰：
  - `Cxx` 角色
  - `Sxx` 场景
  - `Pxx` 道具
- 强调尾帧描述和跨集延长衔接。

优点：

- 中间产物设计非常适合当作 schema 原型。
- 强调分镜是核心，且要求素材清单、连续性检查、首尾衔接。
- 证明了“内容规划层”必须独立出来。

不足：

- 缺少真正的自动执行代码。
- 更偏单一创作风格示例，通用性需要重新抽象。

### C. seedance2.0-prompt-skill

Status: 已证实

- 是真正的 Skill 形态，且引用型资料组织得很完整。
- 核心价值不是写一个超大 prompt，而是把知识拆成：
  - 平台规格
  - 生产流水线
  - 相机语言
  - 美学约束
  - CLI 集成
  - 实战样例
- 明确区分：
  - `<=15s` 的短视频路径
  - `>15s` 的长视频生产流水线
  - 图片驱动路径
  - 分镜板驱动路径

优点：

- Skill 组织方式成熟，适合直接借鉴目录与 progressive disclosure 结构。
- 对 Dreamina CLI 的执行边界写得清楚：先出提示词，再询问是否执行。
- 对平台参数、限制、失败场景、dry-run 思维都处理得较好。

不足：

- 能力重心仍是提示词与生成策略，不包含发布层。
- 内容量大，若不收敛 scope，容易把新 Skill 写成过重的知识库。

## Synthesis

三个仓库分别解决了不同层的问题：

1. `douyin-upload-mcp-skill`
   - 解决发布自动化
2. `Seedance2-Storyboard-Generator`
   - 解决故事到分镜的中间产物设计
3. `seedance2.0-prompt-skill`
   - 解决 Skill 包装、提示词知识组织与执行边界

因此新 Skill 的正确组合方式不是复制其中任何一个，而是：

- 以 `seedance2.0-prompt-skill` 学 Skill 结构
- 以 `Seedance2-Storyboard-Generator` 学中间产物与流程拆分
- 以 `douyin-upload-mcp-skill` 学发布适配器接口和登录/发布业务面

## Product Implication

新 Skill 应该是一个 orchestration skill，而不是：

- 只会写 prompt 的文档包
- 只会点页面的自动化脚本
- 只支持某一种故事风格的模板仓库

它必须把“知识层、编译层、执行层、发布层”拆开。
