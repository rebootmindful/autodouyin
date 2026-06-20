<!--
[INPUT]: 依赖 {seedance-job} 的 {执行所需环境与契约}
[OUTPUT]: 对外提供 {Seedance/Dreamina 执行适配器接口约定}
[POS]: {adapters} 的 {视频生成适配器契约}
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
-->

# Seedance Executor Contract

## Input

- `seedance-job.json`
- 所需本地素材路径 (对应 slot_plan 中的 @图片N 引用)

## Output

- 生成结果视频路径
- task_id
- status: success / fail / pending
- 平台错误详情
- `generation-report.json`: 汇总所有 block 的执行状态

## Mode

适配器支持：

1. `dry-run` (默认): 打印将执行的命令，不实际调用
2. `execute`: 实际提交生成任务

## CLI Mapping

首选集成路径: `seedance` CLI (npm, MIT, Rust, 火山引擎 Ark API)

安装: `npm install -g seedance`
认证: 设置环境变量 `ARK_API_KEY`

### 命令映射

seedance-job.json 的每个 prompt_block 映射为一次 `seedance generate` 调用:

```bash
seedance generate "<prompt>" \
  --image <C01_path> --image <S01_path> --image <P01_path> \
  --duration <block_duration> \
  --ratio <aspect_ratio> \
  --wait --json
```

### 模式映射

| seedance-job mode         | CLI 行为                                              |
|---------------------------|-------------------------------------------------------|
| `text-image-video`        | 单次 `seedance generate`，传入所有图片引用             |
| `segmented-extension`     | 首段正常生成；后续段加 `--video <prev_output>` 续拍    |
| `scene-split-edit-pipeline`| 按 scene_id 分组，组内续拍，组间输出拼接指令          |

### 参数映射

| seedance-job 字段          | CLI 参数              |
|---------------------------|----------------------|
| `prompt_blocks[].prompt`  | 位置参数 `"<prompt>"` |
| `slot_plan[].asset_id`    | `--image <path>` (按顺序) |
| `duration_seconds` (per block) | `--duration N`   |
| `aspect_ratio`            | `--ratio X:Y`        |
| `video_refs` 含 @视频1    | `--video <prev.mp4>` |

## Pre-Execution Validation

执行前自动校验:

- 所有引用的素材文件存在
- 图片+视频+音频总数 <= 12 (Rule of 12)
- 每个 prompt_block 时长 <= 15s
- aspect_ratio 与 brief 一致
- `seedance` CLI 在 PATH 中可用 (execute 模式)

## Dry-Run Output

dry-run 模式输出:

```json
{
  "mode": "dry-run",
  "total_blocks": 5,
  "commands": [
    {
      "block_id": "pb-01",
      "command": "seedance generate '...' --image c01.png --image s01.png --image p01.png --duration 3 --ratio 9:16 --wait --json",
      "estimated_duration_seconds": 3
    }
  ],
  "asset_requirements": ["c01.png", "s01.png", "p01.png"],
  "total_asset_count": 3
}
```

## Generation Report

execute 模式产出 `generation-report.json`:

```json
{
  "job_id": "seedance-job-local-001",
  "blocks": [
    {
      "block_id": "pb-01",
      "task_id": "ark-task-xxx",
      "status": "success",
      "output_path": "artifacts/pb-01.mp4",
      "duration_seconds": 3
    }
  ],
  "overall_status": "success"
}
```

## Constraint

执行前先验证：

- 引用素材数量 <= 12
- 每 block 时长 <= 15s
- 比例与 brief 一致
- @引用命名规范 (@图片1-9, @视频1-3, @音频1-3)
