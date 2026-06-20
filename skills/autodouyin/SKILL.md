---
name: autodouyin
description: |
  Review-first short-video production orchestration skill for Codex plugin packaging.
  Compile a brief into a review package, storyboard, Seedance job, and optional Douyin publish preparation.
  Use when the user needs a short-video plan, a dry-run generation chain, or a publish-prepared package with a human approval gate.
  Trigger phrases include: 编译视频任务、生成 Seedance job、brief 转分镜、抖音发布任务、autodouyin。
  Do not use for: single-shot prompt polishing, generic copywriting, or direct video editing.
---

# autodouyin

这是根目录 `SKILL.md` 的插件包装版。行为目标不变，只是把路径改成相对插件根可用的形式。

## Core Flow

1. 先产出审核包：

```bash
python ../../scripts/run_pipeline.py --brief <brief.json> --output-dir <dir>
```

2. 用户批准后，再选模型：

```bash
python ../../scripts/run_pipeline.py --dir <dir> --approve --model <model>
```

3. dry-run 或真实执行：

```bash
python ../../scripts/run_pipeline.py --dir <dir> --generate
python ../../scripts/run_pipeline.py --dir <dir> --generate --execute
```

4. 长视频需要时，本地组装：

```bash
python ../../scripts/run_pipeline.py --dir <dir> --assemble
```

5. 如果要准备发布页，但不点击发布：

```bash
python ../../scripts/run_pipeline.py --dir <dir> --prepare-publish
```

6. 如果没有参考图，需要抽人物锚图：

```bash
python ../../scripts/run_pipeline.py --dir <dir> --extract-identity-stills
```

## Read Path

- `../../references/README.md`
- `../../references/seedance/platform-specs.md`
- `../../references/storyboard/story-structure.md`
- `../../references/publishing/douyin-workflow.md`
- `../../adapters/douyin-publisher.md`

## Contract Discipline

所有核心产物都必须遵守：

- `../../schemas/brief.schema.json`
- `../../schemas/script.schema.json`
- `../../schemas/storyboard.schema.json`
- `../../schemas/asset-manifest.schema.json`
- `../../schemas/seedance-job.schema.json`
- `../../schemas/publish-job.schema.json`
- `../../schemas/run-ledger.schema.json`
- `../../schemas/review-decision.schema.json`

## Safety Boundary

- 未批准前，不执行 Seedance
- 不自动点击抖音发布
- 先交审核包，再推进执行
- 适配器缺失时，也要交出完整任务文件
