<sub>🌐 <b>中文</b> · <a href="README.en.md">English</a></sub>

<div align="center">

# AutoDouyin

> *「别人在赌一段 prompt，你在走一条可审核的生产链。」*

[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-autodouyin-blueviolet)](SKILL.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Codex Plugin](https://img.shields.io/badge/Codex-Plugin%20Ready-171717)](.codex-plugin/plugin.json)

**把 brief 编译成可审核、可回放、可停手的短视频对象链，而不是直接赌一段 Seedance prompt。**

[看效果](#效果示例) · [安装](#快速开始) · [触发方式](#触发方式) · [它和同类有什么不同](#它和同类有什么不同) · [安全边界](#安全边界)

</div>

---

![AutoDouyin 审核包 Showcase](assets/showcase-review-package.png)

<sub>真实回放来自 `examples/showcase-plan-only/` 与 `examples/showcase-long-dry-run/`，由 `python scripts/build_showcase_assets.py` 生成。</sub>

---

## 它解决什么问题

你给 Seedance 2.0 写了一段 prompt，第一条风格漂了，第二条人物崩了，第三条想改标题时发现整条链没有一个能回退的中间态。

问题不在 prompt 写得不够努力，而在于**没有稳定对象**。brief、脚本、分镜、素材引用、生成任务、发布任务，全挤在一段自然语言里。你没法审核，没法 diff，没法停手，也没法把“生成”和“发布”拆成两个可信步骤。

AutoDouyin 换了路子：先把 brief 编译成完整审核包，再由你批准后推进 dry-run、真实生成、组装和发布准备。Seedance prompt 只是链路中的一个产物，不是整个系统。

## 效果示例

输入：

```text
做一条 15 秒 9:16 的抖音视频，主题是 AI 帮人自动生成短视频，先给我方案不要执行。
```

输出审核包：

| 产物 | 文件 | 说明 |
|---|---|---|
| brief | `brief.json` | 归一化后的目标：模式、时长、比例、风格预设 |
| script | `script.json` + `script.md` | 确定性编译出的结构化脚本 |
| storyboard | `storyboard.json` + `storyboard.md` | 按时间轴组织的分镜、镜头编码、动作、音频 |
| asset manifest | `asset-manifest.json` | C01/S01/P01 素材锚点与引用链 |
| seedance job | `seedance-job.json` | prompt blocks、时长边界、风格锁定、identity 策略 |
| publish job | `publish-job.json` | 抖音发布任务：标题、简介、视频路径 |
| review summary | `review-summary.md` | 给人看的审核摘要 |
| review decision | `review-decision.json` | 审核关口：`pending-review` / `approved` / `changes-requested` / `rejected` |
| run ledger | `run-ledger.json` | 当前阶段、执行状态、产物链与步骤记录 |

真实生成回放：

![AutoDouyin Dry Run Showcase](assets/showcase-dry-run.png)

如果你要一个能发群演示的结果卡，这里还有一张：

![AutoDouyin Scorecard](assets/showcase-scorecard.png)

## 快速开始

先把仓库拉到本地，然后在仓库根目录执行一条 bootstrap：

```bash
# Windows
powershell -ExecutionPolicy Bypass -File scripts/bootstrap.ps1 -Profile core

# macOS / Linux
bash scripts/bootstrap.sh core
```

这一步会：

- 创建仓库内 `.venv`
- 安装 Python 依赖：`jsonschema`、`Pillow`
- 跑一次最小 smoke：编译审核包 + 校验产物

推荐的下载后顺序：

```bash
# 1. 先跑 core bootstrap，确认仓库自身能编译和校验
powershell -ExecutionPolicy Bypass -File scripts/bootstrap.ps1 -Profile core

# 2. 如果要给 Agent 调用，再安装成 skill
npx skills add . --skill autodouyin -y
```

这条命令也已经在本地临时副本里实测通过。

当仓库发布到 GitHub 后，把这条本地安装命令替换成真实仓库 URL 版本即可。

如果你要“下载后把整条链全装齐”，直接跑：

```bash
powershell -ExecutionPolicy Bypass -File scripts/bootstrap.ps1 -Profile all
```

这会把以下依赖都检查到位：

- Python + `jsonschema` + `Pillow`
- `seedance` CLI
- `ffmpeg`
- Node / npm
- `adapters/douyin-upload-vendor/` 下的 `npm install`

其中官方 Ark API 路径还需要你自己提供 `ARK_API_KEY`。

## 安装 Profile

根据你想跑到哪一步，选择不同 profile：

| Profile | 会装什么 | 适合什么 |
|---|---|---|
| `core` | Python + `jsonschema` + `Pillow` | 编译审核包、校验产物 |
| `generate-cli` | `core` + 检查 `seedance` CLI | 跑 2.0 CLI 路径 |
| `generate-official` | `generate-cli` + `ARK_API_KEY` | 跑官方 Ark API |
| `assemble` | `core` + 检查 `ffmpeg` | 长视频组装 / 锚图抽帧 |
| `publish` | Node/npm + vendor `npm install` | 抖音发布准备页 |
| `all` | 上面全部检查 | 想把整条链一次装齐 |

示例：

```bash
# 只跑编译与校验
powershell -ExecutionPolicy Bypass -File scripts/bootstrap.ps1 -Profile core

# 连 vendor 依赖也一起装
powershell -ExecutionPolicy Bypass -File scripts/bootstrap.ps1 -Profile publish

# 做全量检查
powershell -ExecutionPolicy Bypass -File scripts/bootstrap.ps1 -Profile all
```

## 环境体检

不想立刻安装时，先跑 doctor：

```bash
python scripts/doctor.py --profile core
python scripts/doctor.py --profile publish
python scripts/doctor.py --profile all --json
```

环境变量模板见 [.env.example](.env.example)。

装完对 Agent 说：

```text
用 autodouyin 把这个 brief 编译成完整审核包：15 秒 9:16，主题是产品展示，先不要执行。
```

## 触发方式

- "帮我编译一条 Seedance 任务"
- "把这个 brief 转成分镜和 seedance job"
- "做一条 15 秒的抖音视频方案，不执行"
- "我已经有 storyboard 了，帮我补齐 seedance job"
- "生成一个 90 秒的长视频分镜方案"
- "帮我准备发布任务，视频已经生成好了"
- "先出审核包，过了我再批准执行"

## 能做什么 / 它会交付什么

| 模式 | 交付物 | 说明 |
|---|---|---|
| `plan-only` | 完整 review package | 只出方案，停在 `pending-review` |
| `generate-only` | `seedance-job.json` + `run-ledger.json` | 已有分镜或审核包，补齐生成任务并推进执行 |
| `publish-only` | `publish-job.json` + `run-ledger.json` | 已有最终视频，补齐发布任务 |
| `end-to-end` | 审核包 + 生成 + 组装 + 发布准备 | 仍然必须先过审核关口 |

## 它和同类有什么不同

| 维度 | 常见 Seedance Skill | AutoDouyin |
|---|---|---|
| 核心动作 | 写一段 prompt | 编译一条可审核的对象链 |
| 中间产物 | 少或没有 | brief / script / storyboard / assets / review / jobs / ledger |
| 可验证性 | 靠人眼看 | JSON Schema + `validate_artifacts.py` + `run-ledger.json` |
| 长视频 | 手动分段 | `scene-split-edit-pipeline` 自动拆分 |
| 审核关口 | 往往没有 | `review-decision.json` 未批准不能执行 |
| 发布边界 | 不涉及 | `--prepare-publish` 停在发布前，最后一步留给人确认 |

## 安全边界

- **不会**在 `review-decision.json` 未批准时执行 Seedance
- **不会**自动点击抖音发布按钮
- **不会**把 brief 内容偷偷发去第三方服务
- **不会**因为适配器缺失就中断审核包交付
- **会**先把生成与发布拆成两个阶段
- **会**在每步里记录 `run-ledger.json`，让链路能追溯

## 文件结构

```text
autodouyin/
├── SKILL.md                    # Skill 主入口：阶段判断、主链、失败模式
├── README.md                   # 公共安装页与展示页
├── agents/openai.yaml          # Skill UI 展示元数据
├── assets/                     # README 首屏图、GIF、插件图标
├── schemas/                    # 8 份 JSON Schema 契约
├── references/                 # Seedance / Storyboard / Publishing 规则与来源
├── scripts/                    # 编译、校验、执行、组装、showcase 生成器
├── examples/                   # brief 样例、showcase 样例、历史输出样例
├── adapters/                   # Seedance / Douyin 适配边界与 vendor 说明
├── .codex-plugin/              # Codex 插件元数据
├── .agents/plugins/            # 本地 marketplace 入口
└── docs/plantree/              # 规划与整改状态
```

## 验证与测试

最小审核包：

```bash
python scripts/run_pipeline.py --brief examples/brief/minimal-douyin-video.json --output-dir examples/showcase-plan-only
python scripts/validate_artifacts.py --dir examples/showcase-plan-only
```

长视频 dry-run：

```bash
python scripts/run_pipeline.py --brief examples/brief/ultra-long-workflow.json --output-dir examples/showcase-long-dry-run
python scripts/run_pipeline.py --dir examples/showcase-long-dry-run --approve --model seedance-2.0-fast
python scripts/run_pipeline.py --dir examples/showcase-long-dry-run --generate
```

展示资产重建：

```bash
python scripts/build_showcase_assets.py
```

合格表现：

- 编译阶段输出 `compiled review package`
- 审核阶段输出 `review status -> approved`
- dry-run 阶段输出 `generation-report.json`
- `assets/showcase-*.png` 与 `assets/showcase-flow.gif` 被重新生成

## 致谢

方法论与参考来源：

- [WJZ-P/douyin-upload-mcp-skill](https://github.com/WJZ-P/douyin-upload-mcp-skill)（抖音发布适配器边界）
- [liangdabiao/Seedance2-Storyboard-Generator](https://github.com/liangdabiao/Seedance2-Storyboard-Generator)（剧情到分镜工作流）
- [MapleShaw/seedance2.0-prompt-skill](https://github.com/MapleShaw/seedance2.0-prompt-skill)（Seedance 平台能力梳理）
- [op7418/Seedance-Product-Video](https://github.com/op7418/Seedance-Product-Video)（风格预设与产品视频提示体系）

## License

[MIT](LICENSE)（核心 Skill）；`adapters/douyin-upload-vendor/` 保持 AGPL-3.0 边界，详见 [adapters/douyin-upload-vendor/NOTICE.md](adapters/douyin-upload-vendor/NOTICE.md)。

---

<div align="center">

*brief 进去，审核包先出来。批准以后，执行才继续。*

</div>
