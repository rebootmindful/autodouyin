<!--
[INPUT]: 依赖 {PRD、决策与开放问题} 的 {阶段状态}
[OUTPUT]: 对外提供 {Done/In Progress/Next/Deferred 路线图}
[POS]: {autodouyin-skill plan root} 的 {阶段看板}
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
-->

# Roadmap

## Done

- 建立 `docs/plantree/` 作为规划权威树。
- 完成三份参考仓库的首轮能力抽取与对比。
- 识别关键许可证边界：Douyin 上传参考仓库为 `AGPL-3.0`。
- 在当前目录完成 Skill 骨架初始化。
- 建立首版 references、schemas、examples 与 adapter 契约。
- 实现最小本地编译脚本：
  - `normalize_brief.py`
  - `compile_pipeline.py`
  - `validate_artifacts.py`
- 跑通 `examples/brief -> examples/outputs` 的最小产物链路。
- 通过 skill 官方快速校验。
- 直接引入 Seedance / Storyboard 参考源文档到 `references/*-source.md`。
- vendored 引入 `douyin-upload-mcp-skill` 代码并补桥接脚本。
- 安装 vendored Douyin adapter 依赖。
- 跑通 Douyin login smoke test，确认当前 skill 能触发二维码登录阶段。
- 为编译器加入视频类型推断：
  - `workflow-explainer`
  - `product-demo`
  - `narrative-story`
  - `character-action`
  - `space-tour`
- 为编译器加入两套正式方法论：
  - `five-beat-short-video`
  - `three-phase-segmented-video`
- 为 `storyboard` 加入 `camera_codec`
- 为 `seedance-job` 加入：
  - `global_style_anchor`
  - `continuity_locks`
  - `negative_constraints`
  - `slot_plan`
  - `video_type`
  - `strategy`
  - `execution_recommendation`
- 跑通短视频样例与长视频样例的本地编译和校验。
- 固化 Seedance 时长边界策略：
  - 单段硬上限 `4-15s`
  - 官方当前推荐窗口 `5-12s`
  - 最快试片窗口 `4-5s`
  - 最快实用窗口 `5-8s`
  - 稳定表达窗口 `8-12s`
  - `>60s` 改为 scene 拆分 + 后期拼接
- 按职责拆分 `compile_pipeline.py`：
  - `compiler_types.py`
  - `compiler_story.py`
  - `compiler_seedance.py`
  - `compiler_render.py`
- 为不同视频类型固化默认时长偏好。
- 按视频类型深化模板并跑通样例：
  - `product-demo`
  - `narrative-story`
  - `character-action`
- 让三类重点视频在 storyboard / asset-manifest / seedance-job 层面明显分化。
- **三层架构重构**：
  - 架构定型：Python 结构层 -> Agent(LLM) 内容层 -> Python 校验层
  - `compile_skeleton.py` (239 行) 作为结构层核心，产出空槽位 skeleton.json
  - `compiler_story.py` (29 行) 和 `compiler_seedance.py` (22 行) 瘦身为纯算术工具
  - 创建 `references/aesthetic-presets.json`：4 种美学预设 (Cupertino / Fluent / Bauhaus Zen / Vercel Dark)
  - 创建 `references/content-patterns/`：camera-presets / purpose-guide / seedance-templates
  - `validate_artifacts.py` 增强 4 项校验：内容非空、时间轴连续、风格一致、相机编码合法
  - `SKILL.md` 更新为 Enrichment Workflow (8 步指令)
  - 7 份 brief 生成骨架通过 + 9 套已有产物通过增强校验
  - 完整 Agent enrichment 测试通过全部校验
- **Seedance 执行器**：
  - `execute_seedance.py` (170 行)：seedance-job.json -> seedance CLI -> generation-report.json
  - 支持 dry-run / execute 两种模式
  - 自动校验 block 时长 (4-15s)、Rule of 12、素材可用性
  - 支持 segmented-extension 顺序续拍
  - recruit-ops 样例 dry-run 通过
- **发布前人工确认链路**：
  - `doubao-seedance-1-5-pro-251215` 官方 API 路径可真实生成视频
  - `scripts/douyin_publish_job.mjs --prepare-only` 已可上传视频、选择封面、填写标题与简介并停在发布前
  - `run_pipeline.py --prepare-publish` 已接入 `run-ledger.json`
  - 标题写入逻辑已改为受控 input 兼容写法，页面状态可见标题
- **公开发布就绪度首轮整改**：
  - README 安装命令改为本地实测可执行的 `npx skills add . --skill autodouyin -y`
  - 新增 `scripts/build_showcase_assets.py`，可重建 README 首屏 PNG / GIF / 结果卡
  - 新增 `examples/showcase-plan-only/` 与 `examples/showcase-long-dry-run/`
  - 统一 README / SKILL / `test-prompts.json` / `examples` 的 review package 口径
  - 新增 `.codex-plugin/plugin.json` 并通过插件验证器
  - 清理 `douyin-upload-vendor/node_modules/`、`temp/` 与二维码残留
  - 初始化 `.git/`，达到 GitHub 发布门槛
  - 新增 `requirements.txt`、`.env.example`、`scripts/bootstrap.ps1`、`scripts/bootstrap.sh`、`scripts/doctor.py`
  - 验证 `core` / `publish` / `all` profile 的自举和体检链路

## In Progress

- 发布成功自动确认仍不稳定，当前推荐人工在发布页最后确认并点击发布。
- 为开放 brief 增加通用兜底模板族，避免内容完全回落到单一 workflow-explainer。
- 为多段视频增加人物身份锁定方案，降低样貌和衣着漂移。
- 消除参考图输入断点，让 brief 能直接绑定真实文件而不是只写文本描述。

## Next

- 公开发布剩余动作：
  - 仓库公开后把 README 安装命令切到远程 URL
  - 视外部受众补双语 README
- 设计“发布成功自动确认”的更稳判据：
  - 发布前作品列表快照
  - 点击发布后跳作品管理页
  - 轮询增量作品确认
- 为 `asset-manifest.json` 增加角色身份锚点字段
- 为 `review-summary.md` 增加 `template_confidence` 和 `identity_risk`
- 为 `brief` / `asset-manifest` 增加 `source_material_files` -> `resolved_path` 的契约链

## Deferred

- 多平台发布（小红书、TikTok、YouTube）
- 自动剪辑 / 后期精修
- 素材生成质量评分器
