<!--
[INPUT]: 依赖 {README、SKILL、test-prompts、scripts 实跑结果与同行对标} 的 {公开发布就绪度证据}
[OUTPUT]: 对外提供 {公开发布差距、优先级与整改入口}
[POS]: {plans/autodouyin-skill/topics} 的 {发布准备审计主题}，承接鲁班审核结果并服务后续整改
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
-->

# Public Release Readiness

Date: 2026-06-20

## Purpose

记录一次基于 `luban` 方法的公开发布就绪度审计，聚焦：

- 这个 skill 现在是否已经适合公开发布
- 哪些差距会直接影响理解、安装、信任和传播
- 后续整改应先补什么，不先补什么

## Audit Snapshot

- 结论：已达到 GitHub 发布门槛。当前仓库已具备可本地安装、可展示、可验证、可初始化版本管理的公开发布最低标准。
- 审计范围：`SKILL.md`、`README.md`、`test-prompts.json`、`scripts/`、`examples/`、`schemas/`、`adapters/`、`assets/`、`.codex-plugin/`、`docs/plantree/`
- 活体验证：
  - `python scripts/run_pipeline.py --brief examples/brief/minimal-douyin-video.json --output-dir <tmp>` 通过
  - `python scripts/run_pipeline.py --brief examples/brief/ultra-long-workflow.json --output-dir <tmp>` 通过
  - `python scripts/run_pipeline.py --dir <tmp> --approve --model seedance-2.0-fast` 通过
  - `python scripts/run_pipeline.py --dir <tmp> --generate` dry-run 通过
  - `python scripts/build_showcase_assets.py` 通过
  - `npx skills add . --skill autodouyin -y` 在临时副本中通过
  - `python ...validate_plugin.py D:\skills\autodouyin` 通过
  - `git init` 已完成
- 同行基线：
  - `liangdabiao/Seedance2-Storyboard-Generator`
  - `MapleShaw/seedance2.0-prompt-skill`
  - `WJZ-P/douyin-upload-mcp-skill`
  - `op7418/Seedance-Product-Video`
  - 手艺同行：`alchaincyf/huashu-design`、`otter1101/blogger-distiller`、`alchaincyf/zhangxuefeng-skill`

## Main Gaps

### 已收敛

- README 安装命令已改为本地实测通过的 `npx skills add . --skill autodouyin -y`。
- 已补首屏 PNG、GIF、结果卡和可复现构建脚本 `scripts/build_showcase_assets.py`。
- README / SKILL / `test-prompts.json` / `examples` 已统一到 8 份 schema + review package 口径。
- 已补 `.codex-plugin/plugin.json`，并通过插件验证器。

### 仍待下一轮处理

- 公开仓库 URL 尚未存在，所以 README 目前提供的是本地已验证安装命令，并附远程 URL 模板说明。
- 仍未提供双语 README。

### 已新增资产

- `assets/showcase-review-package.png`
- `assets/showcase-dry-run.png`
- `assets/showcase-scorecard.png`
- `assets/showcase-flow.gif`
- `examples/showcase-plan-only/`
- `examples/showcase-long-dry-run/`
- `.git/` 已初始化

## Evidence Notes

- 当前 README 已把“审核包优先”“人工最终点发布”前置到首屏叙事。
- showcase 已经来自真实命令回放，而不是摆拍截图。
- 插件元数据现在只声明仓库里真实存在的 `skills/` 与 `assets/`。
- vendor 运行时目录与二维码残留已清理。

## Positioning Recommendation

不要把它讲成“另一个 Seedance prompt skill”。

更适合的公开定位是：

> 一个带审核关口、任务中间态和发布边界的短视频生产编排 Skill。

也就是卖“可验证编排链”，不是卖“再多一份 prompt 模板”。

## Recommended Repair Order

1. 仓库公开后，把 README 安装命令切到真实远程 URL。
2. 视外部受众补 `README.en.md`。

## Not Recommended This Round

- 仍不建议优先堆更多模板或多平台分支。
- 下一轮最值得做的不是加功能，而是把“真实公开发布”和“仓库轻量化”补完。
