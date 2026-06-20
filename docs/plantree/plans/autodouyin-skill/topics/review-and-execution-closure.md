<!--
[INPUT]: 依赖 {PRD、现有脚本能力与用户目标} 的 {闭环执行需求}
[OUTPUT]: 对外提供 {从 brief 到审核再到 Seedance 生成与长视频组装的落地路径}
[POS]: {autodouyin-skill/topics} 的 {实现专题}，定义真正可跑通的主工作流
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
-->

# Review And Execution Closure

Date: 2026-06-20
Status: Active implementation guide

## Goal

把当前仓库从“能产出部分中间文件”推进到真正可跑通的闭环：

1. 用户输入视频目标或 brief
2. 系统生成结构化方案与 Seedance 提示词任务
3. 用户明确审核通过
4. 系统调用 Seedance 生成视频
5. 长视频按 scene / block 分段生成并组装
6. 输出最终视频与执行记录

## Current Gap

当前仓库已有：

- brief 标准化
- skeleton 结构层
- enriched examples
- 本地校验器
- Seedance dry-run / execute 执行器

当前仓库缺失的关键闭环：

1. **审核关口没有进入正式契约**
   - 现在只有 `plan-only` / `end-to-end` 这种粗模式
   - 没有 `pending_review -> approved -> generating -> assembled` 这类显式状态

2. **编译输出与校验输入不一致**
   - `compile_pipeline.py` 只写 `brief.json + skeleton.json`
   - `validate_artifacts.py` 却要求完整 enriched 产物

3. **校验规则与执行规则不一致**
   - 本地校验未严格卡住 `4-15s`
   - 执行器严格卡住 `4-15s`

4. **长视频只有分段策略，没有组装器**
   - 有 `scene_plan`
   - 没有真实 `assemble_video.py` 或等价脚本

5. **缺少一个统一运行入口**
   - 现在用户需要自己理解 compile / enrich / validate / execute 的阶段切换
   - 没有一个真正面向用户的 pipeline orchestrator

## Required End-to-End Flow

目标主路径应固定为：

### Phase 1. Intake

输入：

- 用户自然语言目标或 `brief.json`

输出：

- 标准化 `brief.json`

规则：

- 如果缺时长、比例、是否立即执行等最小必要字段，先补齐
- 这里不要直接生成视频

### Phase 2. Compile Review Package

输入：

- `brief.json`

输出：

- `script.json` + `script.md`
- `storyboard.json` + `storyboard.md`
- `asset-manifest.json`
- `seedance-job.json`
- `publish-job.json`
- `run-ledger.json`
- `review-summary.md`

规则：

- 这一阶段必须产出**可审核包**
- 用户审核前，不进入真实 Seedance 生成

### Phase 3. Human Review Gate

输入：

- review package

输出：

- `review-decision.json`

建议字段：

```json
{
  "status": "approved",
  "reviewer": "user",
  "approved_at": "2026-06-20T12:00:00+08:00",
  "notes": "通过，可执行"
}
```

允许状态：

- `pending-review`
- `changes-requested`
- `approved`
- `rejected`

规则：

- `approved` 之前，禁止进入 `execute_seedance`
- 用户的修改意见应回写到 `run-ledger.json`

### Phase 4. Seedance Generation

输入：

- `seedance-job.json`
- `review-decision.json`
- `assets/` 中的参考素材

输出：

- 分段视频文件
- `generation-report.json`

规则：

- 每个 block 必须满足 `4-15s`
- `text-image-video`：单段直接生成
- `segmented-extension`：首段生成，后续基于 `@视频1` 续拍
- `scene-split-edit-pipeline`：按 scene 分组生成

### Phase 5. Long Video Assembly

输入：

- `generation-report.json`
- 分段视频文件
- `scene_plan`

输出：

- `assembled-video.mp4`
- `assembly-report.json`

规则：

- `<=15s` 无需组装
- `16-60s` 默认按 sequential block 组装
- `>60s` 按 scene 组装，再输出 scene 级与全片级报告

### Phase 6. Optional Publishing

输入：

- `assembled-video.mp4` 或单段输出视频
- `publish-job.json`

输出：

- 发布结果

规则：

- 发布仍是可选层，不阻塞生成主路径闭环
- 当前推荐模式不是“自动点发布”，而是：
  1. 自动上传视频
  2. 自动填写标题 / 简介 / 封面
  3. 停在发布前，由用户人工确认并点击发布

## Minimal Implementation Needed

要让它“正常跑通”，最少要补这 6 件事：

### 1. 定义正式审核契约

新增：

- `review-decision.json` schema
- `review-summary.md` 渲染规则

没有这个对象，所谓“用户审核通过再执行”只是口头流程，不是系统行为。

### 2. 补一个真正的 enriched compile 入口

建议新增统一入口，例如：

- `scripts/run_pipeline.py`

职责：

1. 读 brief
2. 产 skeleton
3. 做内容填充
4. 写完整 artifacts
5. 跑校验
6. 停在 review gate

这一步是当前最大的缺口。

### 3. 统一时长契约

单一事实源必须变成：

- 所有 `prompt_block`：`4 <= duration <= 15`

需要同步：

- `compile_skeleton.py`
- `validate_artifacts.py`
- `execute_seedance.py`
- `README.md`
- examples
- schemas

否则仍然会出现“验证通过但执行失败”。

### 4. 让校验器真正读取 schema

`validate_artifacts.py` 不能继续只做手写校验。

至少要：

1. 先跑 JSON Schema 校验
2. 再跑内容规则校验
3. 再跑执行前规则校验

三层分别报错，避免混在一起。

### 5. 增加长视频组装器

建议新增：

- `scripts/assemble_video.py`

职责：

- 根据 `generation-report.json` 找到 block 输出
- 生成 concat 清单
- 调用 `ffmpeg` 组装
- 写 `assembly-report.json`

如果没有这一步，“长视频需要组装”就仍然只是文档说明，不是产品能力。

### 6. 统一 run ledger 状态机

`run-ledger.json` 需要显式阶段状态，例如：

- `brief-normalized`
- `compiled`
- `pending-review`
- `approved`
- `generating`
- `generated`
- `assembling`
- `assembled`
- `publishing`
- `published`
- `failed`

这样失败点才可追踪。

## Proposed Runtime Shape

建议把真实可跑主路径压成 3 个入口：

### Entry A. `compile-for-review`

```bash
python scripts/run_pipeline.py --brief <brief.json> --output-dir <dir>
```

产出完整 review package，状态停在 `pending-review`。

### Entry B. `approve-and-generate`

```bash
python scripts/run_pipeline.py --dir <dir> --approve --generate
```

要求：

- `review-decision.json.status == approved`

执行 Seedance。

### Entry C. `assemble`

```bash
python scripts/assemble_video.py --dir <dir>
```

对长视频或多 block 输出进行拼接。

如果希望再进一步，也可以让 `run_pipeline.py --execute` 在需要时自动调用组装器。

### Entry D. `prepare-publish`

```bash
python scripts/run_pipeline.py --dir <dir> --prepare-publish
```

效果：

- 调用本地 Douyin 发布桥接脚本
- 上传 `assembled-video.mp4`
- 自动填写标题、简介、封面
- 不点击发布
- `run-ledger.json.current_stage = publish-prepared`

## Acceptance Criteria For Real Closure

满足以下条件，才算真正“跑通”：

1. 给一句自然语言目标，能稳定产出完整 review package。
2. 用户未批准时，系统不会调用真实 Seedance。
3. 用户批准后，`execute_seedance.py` 能处理至少一个短视频样例和一个长视频样例。
4. 长视频样例能生成多个 block，并产出最终组装后的视频文件。
5. `run-ledger.json` 能清楚说明当前停在哪个阶段。
6. README 的 smoke test 与真实入口一致。

## Recommended Phase Order

### Phase A. 修闭环基础

- 修 compile / validate / execute 契约断裂
- 新增 review-decision contract
- 修 examples 与 README

### Phase B. 做统一 pipeline 入口

- `run_pipeline.py`
- review package 输出
- pending-review 停机点

### Phase C. 做真实生成闭环

- 批准后调用 Seedance
- 短视频真实 dry-run / execute

### Phase D. 做长视频组装

- `assemble_video.py`
- ffmpeg concat
- assembly-report

### Phase E. 再接 publish

- 生成主路径稳定后，优先做 `prepare-publish`
- 真正“自动点发布”应晚于发布成功判据稳定之后

## Key Judgment

当前真正缺的不是“再补一点 prompt 知识”，而是**把审核状态、执行入口、时长契约、长视频组装器、发布前人工确认边界变成系统的第一类对象**。没有这些，产品永远停留在“能产出一堆文件”，不是“能稳定跑完一条视频生产链”。
