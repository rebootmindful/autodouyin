<!--
[INPUT]: 依赖 {当前计划状态与本轮输出} 的 {当前阶段、阻塞与下一步}
[OUTPUT]: 对外提供 {恢复会话所需的操作性状态}
[POS]: {autodouyin-skill plan root} 的 {handoff/status 文件}
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
-->

# Implementation Status

Date: 2026-06-20

## Current Phase

最小闭环已经落地，且已达到 GitHub 发布门槛。当前进入“人工审核后手动发布”的稳定化阶段。当前架构是：

```
Layer 1: Python 结构层 (compile_skeleton.py) -> skeleton.json
Layer 2: Python 内容编译层 (compiler_content.py) -> review package
Layer 3: Python 校验/执行/组装层 -> validate / execute / assemble
```

当前主链：

- `run_pipeline.py --brief ... --output-dir ...`
- `run_pipeline.py --dir ... --approve`
- `run_pipeline.py --dir ... --generate [--execute]`
- `run_pipeline.py --dir ... --assemble`
- `run_pipeline.py --dir ... --prepare-publish`

## Active TODO

- 补全发布成功自动确认逻辑（当前推荐人工点发布）。
- 视需要把 prepare-only 结果写入更多发布审计信息。
- 把 `identity_strategy` 真正下沉到执行层（如 first-block-anchor / derived-stills）。
- 视需要把 `template_confidence` / `identity_risk` 接入更多自动校验。
- 仓库公开后，把 README 安装命令切到远程 URL。
- 视外部受众补 `README.en.md`。

## Done This Phase

- `compile_pipeline.py` 现已直接产出完整 review package
- 新增 `compiler_content.py`，用确定性模板替代会话内 enrichment
- 新增 `review-decision.schema.json`
- `validate_artifacts.py` 现已接入 JSON Schema 并统一 `4-15s` 规则
- 新增 `run_pipeline.py`
- 新增 `assemble_video.py`
- README 与根 / scripts / schemas 的 `CLAUDE.md` 已同步
- README / SKILL / `test-prompts.json` / `examples` 的公开展示口径已同步
- 新增 `scripts/build_showcase_assets.py`
- 新增 `assets/showcase-review-package.png`
- 新增 `assets/showcase-dry-run.png`
- 新增 `assets/showcase-scorecard.png`
- 新增 `assets/showcase-flow.gif`
- 新增 `.codex-plugin/plugin.json` 并通过验证器
- `npx skills add . --skill autodouyin -y` 已在临时副本中验证通过
- 已清理 `douyin-upload-vendor/node_modules/`、`temp/` 与二维码残留
- 已初始化 `.git/`
- 已新增 bootstrap / doctor / requirements / `.env.example`
- 已验证 `bootstrap.ps1 -Profile core`
- 已验证 `bootstrap.ps1 -Profile publish -SkipSmoke`
- 已验证 `doctor.py --profile publish`
- 已验证 `doctor.py --profile all`
- README 安装章节已去掉重复与占位式远程安装命令
- 已新增 `README.en.md`，并与中文 README 互链
- 已验证：
  - 短视频审核包生成通过
  - 短视频批准后 dry-run 通过
  - 长视频审核包生成通过
  - 长视频批准后 dry-run 通过
  - 本地假片段组装通过，产出 `assembled-video.mp4`
  - `prepare-publish` 已能上传视频、填写标题和简介并停在发布前
  - 开放 brief 已能落到 `fallback-atmosphere` 等兜底模板族
  - 招聘口播样例已写入 `identity_strategy = first-block-anchor`
  - `asset-manifest.json` 已增加 `identity_lock` 与 `continuity_priority`
  - `review-summary.md` 已输出 `template_mode` / `template_confidence` / `identity_risk`
  - 已能从首个成功视频块抽取 `derived/C01_anchor_*.png`
  - 2.0 CLI 路径在存在 `derived/C01_anchor_*.png` 时，后续 dry-run 已确认会自动回注这些锚图
  - `brief.source_material_files -> asset-manifest.resolved_path -> execute` 契约链已打通

## Blockers

- 自动“发布成功确认”仍不稳定，当前推荐人工在页面最后确认并点击发布

## Next Commit Target

下一步有两个清晰方向：

1. 发布链路：
   - 增强“发布成功确认”
2. 出品质量：
   - 让官方 API 路径在新编译样例上验证 `input_image` 回注行为
   - 让 review 风险信号反向影响执行路径
3. 公开发布：
   - 仓库 URL 可用后切换 README 安装命令
   - 视需要补双语 README
4. 安装体验：
   - 如需覆盖更多平台，再补 Linux / macOS 实测结果

## Reboot Resume

机器重启后不要回到旧的 skeleton/enrichment 思路。

直接从这里继续：

1. 先读 `SKILL.md` 和 `README.md`
2. 准备 `seedance` CLI 与 `ARK_API_KEY`
3. 放入 `C01 / S01 / P01` 素材
4. 用 `run_pipeline.py` 走短视频真实执行

## Last Verified Commands

- `python scripts/run_pipeline.py --brief examples/brief/minimal-douyin-video.json --output-dir <tmp>` 通过
- `python scripts/run_pipeline.py --dir <tmp> --approve` 通过
- `python scripts/run_pipeline.py --dir <tmp> --generate` 通过
- `python scripts/run_pipeline.py --brief examples/brief/ultra-long-workflow.json --output-dir <tmp>` 通过
- `python scripts/run_pipeline.py --dir <tmp> --assemble` 通过
- `python scripts/run_pipeline.py --dir <tmp> --prepare-publish` 通过
- `python scripts/build_showcase_assets.py` 通过
- `python C:\Users\hooji\.codex\skills\.system\plugin-creator\scripts\validate_plugin.py D:\skills\autodouyin` 通过
- `npx skills add . --skill autodouyin -y` 通过（临时副本）
- `git init` 通过
- `powershell -ExecutionPolicy Bypass -File scripts/bootstrap.ps1 -Profile core` 通过
- `powershell -ExecutionPolicy Bypass -File scripts/bootstrap.ps1 -Profile publish -SkipSmoke` 通过
- `python scripts/doctor.py --profile all --json` 通过
- README 安装文案扫描通过（无占位式远程安装命令）
- README 中英文互链已补齐

## Handoff Notes

- 当前最小闭环已可用。
- 当前推荐生产方式是：生成 -> 组装 -> prepare-publish -> 人工点发布。
- 抖音上传页的标题、简介和封面自动填写已可用。
- 当前内容质量层面的下一个重点，不是再加零散模板，而是做 fallback family 和 identity lock stack。
- 当前公开资产层已经可本地安装、可展示、可验证，并已满足 GitHub 发布门槛；剩余外部动作主要是远程仓库 URL 与双语文档。
- 当前仓库已具备“下载后执行一条 bootstrap 命令即可跑通 core / publish / all profile”的自举能力。
