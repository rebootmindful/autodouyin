<!--
[INPUT]: 依赖 {PRD、中间产物定义与通用性目标} 的 {契约与 schema 设计}
[OUTPUT]: 对外提供 {核心数据对象、字段草案与验证要求}
[POS]: {autodouyin-skill/topics} 的 {数据契约设计文档}，为后续 schema 文件提供蓝图
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
-->

# Contracts And Schemas

Date: 2026-06-19
Status: Draft

## Goal

把 Skill 的中间产物固定成可被：

- 人工阅读
- 另一个 AI 消费
- 脚本验证
- 外部适配器执行

的稳定对象。

## Contract Stack

第一版建议定义 7 个核心对象：

1. `brief`
2. `script`
3. `storyboard`
4. `asset-manifest`
5. `seedance-job`
6. `publish-job`
7. `run-ledger`

## 1. brief

### Role

用户意图的标准输入。

### Required Fields

```json
{
  "id": "brief-20260619-001",
  "goal": "做一条关于XX的抖音视频",
  "platform": "douyin",
  "mode": "plan-only",
  "duration_seconds": 15,
  "aspect_ratio": "9:16"
}
```

### Optional Fields

- `topic`
- `audience`
- `style`
- `tone`
- `source_materials`
- `source_material_files`
- `must_include`
- `must_avoid`
- `execution_preference`

### Validation Rules

- `mode` 只能是：
  - `plan-only`
  - `generate-only`
  - `publish-only`
  - `end-to-end`
- `duration_seconds` 必须是正整数
- `aspect_ratio` 必须是允许值之一
- `source_material_files[]` 若存在，必须是可解析的本地路径、URL 或后续上传句柄

## 2. script

### Role

把 brief 展开成结构化叙事。

### Required Fields

```json
{
  "id": "script-20260619-001",
  "brief_id": "brief-20260619-001",
  "title": "示例标题",
  "logline": "一句话概括",
  "segments": []
}
```

### Segment Shape

```json
{
  "segment_id": "seg-01",
  "purpose": "hook",
  "summary": "开场钩子",
  "emotion": "urgent",
  "estimated_seconds": 3
}
```

### Validation Rules

- `segments[].estimated_seconds` 之和应接近目标时长
- 每个 segment 都必须有 `purpose`

## 3. storyboard

### Role

执行层消费的分镜主对象。

### Required Fields

```json
{
  "id": "storyboard-20260619-001",
  "script_id": "script-20260619-001",
  "shots": []
}
```

### Shot Shape

```json
{
  "shot_id": "shot-01",
  "start_second": 0,
  "end_second": 3,
  "visual": "画面描述",
  "camera": "镜头语言",
  "action": "动作描述",
  "audio": "音效或对白",
  "assets": ["C01", "S01"],
  "continuity_note": "与下一镜头如何衔接"
}
```

### Validation Rules

- `end_second > start_second`
- shots 时间轴不能重叠
- 引用的素材编号必须存在于 `asset-manifest`

## 4. asset-manifest

### Role

统一角色、场景、道具、参考素材。

### Required Fields

```json
{
  "id": "assets-20260619-001",
  "storyboard_id": "storyboard-20260619-001",
  "items": []
}
```

### Item Shape

```json
{
  "asset_id": "C01",
  "type": "character",
  "name": "主角正面全身",
  "description": "素材说明",
  "prompt": "生成素材用描述",
  "source_ref": "brief.source_material_files[0]",
  "resolved_path": "C:/project/input/host.png",
  "required": true
}
```

### Validation Rules

- `asset_id` 必须符合：
  - `C\\d{2}`
  - `S\\d{2}`
  - `P\\d{2}`
- `type` 只能是：
  - `character`
  - `scene`
  - `prop`
  - `reference`
- 如果 `source_ref` 存在，`resolved_path` 或可执行下载结果必须在执行前被填实

## 5. seedance-job

### Role

给 Seedance / Dreamina 执行层的标准任务。

### Required Fields

```json
{
  "id": "seedance-job-20260619-001",
  "storyboard_id": "storyboard-20260619-001",
  "duration_seconds": 15,
  "aspect_ratio": "9:16",
  "mode": "text-image-video",
  "prompt_blocks": []
}
```

### Prompt Block Shape

```json
{
  "block_id": "pb-01",
  "start_second": 0,
  "end_second": 3,
  "prompt": "给平台的文本段",
  "image_refs": ["@图片1"],
  "video_refs": [],
  "audio_refs": []
}
```

### Validation Rules

- 全部 refs 数量要满足平台限制
- `prompt_blocks` 的总时长要覆盖目标时长
- ref 命名必须是平台允许格式
- 对于 `@图片N`，执行前必须能映射到真实文件，而不是只停留在占位 ID

## Reference Input Boundary

当前系统的真实断点是：

1. 用户说“用这张图做参考”
2. `brief.source_materials` 只能写文本
3. 编译器只能产出 `@图片1 -> C01`
4. 执行前又要求用户自己手动把 `C01.png` 放进 `assets/`

这说明当前契约缺少：

- **引用文件输入**
- **路径解析**
- **从 brief 到 asset 的可追踪绑定**

### Recommended Fix

在 `brief` 增加一层机器可消费的文件引用：

```json
{
  "source_material_files": [
    {
      "id": "src-01",
      "role": "character",
      "label": "产品白底图",
      "path": "C:/Users/.../product.png"
    },
    {
      "id": "src-02",
      "role": "scene",
      "label": "办公室场景",
      "path": "C:/Users/.../office.jpg"
    }
  ]
}
```

然后在 `asset-manifest.json` 里显式写回：

```json
{
  "asset_id": "C01",
  "source_ref": "src-01",
  "resolved_path": "C:/Users/.../product.png"
}
```

### Why This Is Correct

这样一来：

1. 用户输入的“这张图”不再丢失
2. 编译器知道哪张图对应哪类素材
3. `asset-manifest` 可追踪
4. 执行器可以直接消费 `resolved_path`
5. 不再需要用户手动去 `output_dir/assets/` 里重命名和搬运

## 6. publish-job

### Role

给平台发布适配器的标准任务。

### Required Fields

```json
{
  "id": "publish-job-20260619-001",
  "platform": "douyin",
  "video_path": "path/to/video.mp4",
  "title": "标题",
  "description": "简介"
}
```

### Optional Fields

- `hashtags`
- `cover_path`
- `schedule_at`
- `visibility`
- `login_profile`

### Validation Rules

- `platform` 第一版固定为 `douyin`
- `video_path` 不能为空
- `title` / `description` 要有长度限制

## 7. run-ledger

### Role

记录一次运行从输入到输出的全过程。

### Required Fields

```json
{
  "id": "run-20260619-001",
  "brief_id": "brief-20260619-001",
  "mode": "plan-only",
  "steps": [],
  "status": "success"
}
```

### Step Shape

```json
{
  "name": "compile-storyboard",
  "status": "success",
  "started_at": "2026-06-19T10:00:00+08:00",
  "ended_at": "2026-06-19T10:00:03+08:00",
  "artifacts": ["storyboard.md", "storyboard.json"],
  "notes": "说明"
}
```

## Markdown Pairing Rule

每个核心 JSON 对象都应该有对应的人类可读版本：

- `script.json` ↔ `script.md`
- `storyboard.json` ↔ `storyboard.md`

因为代码与文档必须同构。JSON 负责机器相，Markdown 负责语义相。

## Minimal Validation Order

1. `brief`
2. `script`
3. `asset-manifest`
4. `storyboard`
5. `seedance-job`
6. `publish-job`
7. `run-ledger`

## Implementation Recommendation

第一步不要急着写满正式 JSON Schema。

更稳的顺序是：

1. 先把这 7 个对象的字段蓝图写清楚
2. 用 1-2 组真实样例跑一遍
3. 再固化为正式 `.schema.json`

这样可以避免一开始把 schema 锁死，后面被真实流程反打。
