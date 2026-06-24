---
name: autodouyin
description: |
  通用短视频生产与发布编排 Skill。把用户目标或 brief 编译成脚本、分镜、素材清单、Seedance 2.0 任务规格和可选的抖音发布任务。
  用于需要生成视频脚本、分镜、C/S/P 素材编号、Seedance 提示词任务、连续短剧分段方案、或准备 Dreamina/Seedance 与 Douyin 发布适配器输入的场景；也适用于只做方案、不执行外部平台的 dry-run 工作流。
  触发词：编译视频任务、生成 Seedance job、分镜编译、brief 转分镜、短视频方案、抖音发布任务、autodouyin。
  不要用于：直接写一段 Seedance prompt（用 seedance skill）、视频剪辑或格式转换、与短视频无关的通用文案生成。
---

<!--
[INPUT]: 依赖 {references、schemas、examples} 的 {视频生产规则、平台约束与中间契约}
[OUTPUT]: 对外提供 {brief -> review package -> approved generation -> optional assembly 的最小主链}
[POS]: {skill 根目录} 的 {主入口}，协调知识层、契约层与可选适配器
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
-->

# autodouyin

先判断用户当前处于哪个阶段：

1. `plan-only`
   - 生成完整审核包，停在 `pending-review`。
2. `generate-only`
   - 已有审核包且已批准，执行 `seedance-job`。
3. `publish-only`
   - 已有最终视频，补齐或执行 `publish-job`。
4. `end-to-end`
   - 从 brief 一直走到可执行任务，但执行前必须先过审核关口。

## Creative Writing Phase（创作阶段）

当 brief 包含创作元素（角色、剧情、宠物、搞笑、反转等）时，在编译前先进入 LLM 创作阶段。不要让规则模板接管想象力。

### 工作流

```
brief.json
  → [Creative Phase] LLM 创作 creative_content.json
  → [Compile Phase]  compile_pipeline.py --brief ... --output-dir ...
  → [Review Phase]    用户审核
  → [Execute Phase]   生成视频
```

### Step 0: 生成创作模板

```bash
python scripts/compile_pipeline.py --brief <brief.json> --output-dir <dir> --creative
```

产出 `creative_content.json` 空模板。同时产出规则编译产物作为 fallback。

### Step 1: LLM 填入创意

按 `schemas/creative-content.schema.json` 规范填入：

1. **角色先行** — 先创造有辨识度的角色（名字、性格、外观、说话风格、角色弧线）。角色必须有缺陷或欲望。
2. **情绪曲线** — 每段标注 `emotion_curve`（如"安逸→惊恐"）和 `beat_name`（节奏点名）。
3. **视觉即叙事** — `visual_core` 用 Seedance 可理解的视觉语言：空间、光线、材质、动作、表情。不写抽象概念。
4. **对白节奏** — 每句 ≤15 字，含表演提示（`delivery`）。角色之间要有停顿空间。
5. **CTA 是故事终点** — `cta_moment` 是剧情反转的自然结果，不是贴上去的广告。

### 方法论

- **不要**把 brief 当成信息清单逐条翻译。
- **要**先想象"这个视频最好看的 3 秒是什么"，从那 3 秒倒推整个结构。
- **不要**让角色面对镜头念 JD。
- **要**让角色在场景里活起来——做什么、怕什么、想要什么。
- 约束越具体，创作越聚焦。空白画布让 LLM 输出陈词滥调。

### 编译器行为

- `creative_content.json` 存在且已填充 → 编译器使用 LLM 创作内容（`template_mode: llm-creative`），仅补充技术细节（camera codec、duration、aspect_ratio）
- `creative_content.json` 不存在或为空模板 → 编译器 fallback 到规则模板（含 creative_recruit 检测）

### 也可直接手写 creative_content.json

如果不想用 `--creative` 生成模板，可以直接按 schema 手写 `creative_content.json` 放入产物目录。编译器检测到已填充内容后自动启用创作路径。

## Identity & Product Consistency（身份与产品一致性）

纯 T2V 每次从随机噪声出发，同一段 text 生成三个 block，产品形态必然不同。解决：**锚图驱动 I2V**。

### 自动判断逻辑

```
检查 asset-manifest.json → C01 是否有 resolved_path 指向存在的文件？
  ├── 有 → 直接注入为 first_frame 锚点，所有 prompt block 共享
  └── 无 → AI 闭环生成产品定妆照 → 注册 C01 → 注入锚点
```

### AI 闭环工作流（无实物图时自动触发）

```
检测无产品锚图（默认情况）
  → Step A: 调用图片生成 API 生成产品定妆照
      - 白底/干净背景, ghost mannequin 或平坦展示
      - 9:16 比例, 2K 分辨率
      - 存入 assets/C01-product-anchor.png
  → Step B: 更新 asset-manifest.json
      - C01.resolved_path = "assets/C01-product-anchor.png"
      - C01.type = "character"（触发 character_reference→first_frame 路由）
  → Step C: 所有 prompt block 的 prompt 开头注入 [Image1] 锚点引用
      - "以参考图[Image1]中的产品为视觉锚点, 保持面料/剪裁/颜色完全一致。"
  → Step D: 重编译 pipeline
  → Step E: execute_official_video.py 检测 [Image1]
      → 自动将 C01 图编码为 base64, 以 first_frame role 注入 Ark API content
      → I2V 模式: 所有 block 从同一锚图出发 → 产品形态一致
```

### [Image1] 机制

`execute_official_video.py:125-136` 检测 prompt 中的 `[Image1]` 标记，自动从 `image_content_items()` 取 C01 图以 `first_frame` role 注入 Ark API payload。`compile_from_prompts.py` 负责在 shot_prompts 编译为 prompt_blocks 时保留或注入 `[Image1]` 前缀。

### 锚图质量要求

- 白底/干净背景产品照
- ghost mannequin 或平坦展示, 不出现真人面部
- 9:16 比例（与视频 aspect_ratio 一致）
- 分辨率 ≥ 2K, 纹理细节清晰可辨

## Runtime Rule

当前最小主链只有 6 步：

0. 无产品图时 AI 自动生成锚图（见上方 Identity 章节）
1. 生成审核包
2. 用户批准
3. 执行 Seedance
4. 长视频需要时组装
5. 无参考图时可抽取人物锚图

不要再把主流程理解成“先 skeleton，再会话内 enrichment，再手工拼装”。当前实现已经收敛为本地确定性编译主链。

把这个 Skill 理解成“审核包优先的生产编排器”，不要理解成“直接代替用户点击发布的黑盒自动化器”。

推荐发布方式：

1. 走完生成与组装
2. 调用 `--prepare-publish`
3. 让用户在抖音创作者平台页面人工确认后点击发布

## Main Commands

### 0. （推荐）LLM 创作阶段

```bash
# 生成 creative_content.json 模板 + 规则编译产物
python scripts/run_pipeline.py --brief <brief.json> --output-dir <dir> --creative
```

然后 LLM 按 `schemas/creative-content.schema.json` 填入创意内容到 `creative_content.json`。

再运行普通编译，编译器自动检测已填充的 creative_content.json 并启用 `llm-creative` 路径：

```bash
python scripts/run_pipeline.py --brief <brief.json> --output-dir <dir>
```

### 1. 生成审核包（无创作阶段）

```bash
python scripts/run_pipeline.py --brief <brief.json> --output-dir <dir>
```

产出：

- `brief.json`
- `script.json` + `script.md`
- `storyboard.json` + `storyboard.md`
- `asset-manifest.json`
- `seedance-job.json`
- `publish-job.json`
- `review-summary.md`
- `review-decision.json`
- `run-ledger.json`

此时状态必须停在：

- `review-decision.json.status = pending-review`
- `run-ledger.json.current_stage = pending-review`

### 2. 用户批准

```bash
python scripts/run_pipeline.py --dir <dir> --approve --model <model>
```

效果：

- 将 `review-decision.json.status` 改为 `approved`
- 记录批准时间
- 写入 `review-decision.json.selected_model`

### 3. 执行 Seedance

```bash
# dry-run
python scripts/run_pipeline.py --dir <dir> --generate

# real execute
python scripts/run_pipeline.py --dir <dir> --generate --execute
```

模型路由：

- `doubao-seedance-1-5-pro-251215` -> 官方 Ark API
- `seedance-2.0-fast` -> `seedance` CLI
- `seedance-2.0-standard` -> `seedance` CLI

前提：

- `review-decision.json.status == approved`
- `review-decision.json.selected_model` 已明确
- `seedance` CLI 已安装
- `ARK_API_KEY` 已配置
- 素材文件已按 `C01 / S01 / P01` 命名放入输出目录或 `assets/` 目录

### 4. 长视频组装

```bash
python scripts/run_pipeline.py --dir <dir> --assemble
```

效果：

- 对多段输出做本地拼接
- 产出 `assembled-video.mp4`
- 产出 `assembly-report.json`

### 5. 准备发布页但不点击发布

```bash
python scripts/run_pipeline.py --dir <dir> --prepare-publish
```

效果：

- 上传 `assembled-video.mp4`
- 自动填写标题、简介、封面
- 状态停在 `publish-prepared`
- 由用户自己审核后点击发布

### 6. 从首段提取人物锚图

```bash
python scripts/run_pipeline.py --dir <dir> --extract-identity-stills
```

效果：

- 从第一个成功视频块抽取 1-3 张稳定帧
- 写入 `derived/C01_anchor_*.png`
- 生成 `derived/identity-stills-report.json`
- 可供后续重试或跨 scene 复用

## Core Constraints

### 审核关口

- 未批准前，不能执行 Seedance
- 所有真实执行前都先检查 `review-decision.json`

### Seedance 时长

- 每个 `prompt_block` 必须满足 `4-15s`
- `<=15s`：单段或少量 block
- `16-60s`：按 sequential block
- `>60s`：按 `scene_plan` 拆 scene，生成后再组装

### 校验

运行：

```bash
python scripts/validate_artifacts.py --dir <dir>
```

校验分三层：

1. JSON Schema
2. 内容完整性
3. 执行前平台规则

## Read Path

### 用户要做 LLM 创作

先读：

- [schemas/creative-content.schema.json](schemas/creative-content.schema.json)
- [scripts/creative_writer.py](scripts/creative_writer.py)

### 用户要做方案与审核

先读：

- [references/README.md](references/README.md)
- [references/storyboard/story-structure.md](references/storyboard/story-structure.md)
- [references/storyboard/continuity-rules.md](references/storyboard/continuity-rules.md)
- [references/aesthetic-presets.json](references/aesthetic-presets.json)

### 用户要做 Seedance 执行

再读：

- [references/seedance/platform-specs.md](references/seedance/platform-specs.md)
- [references/seedance/duration-boundaries.md](references/seedance/duration-boundaries.md)
- [references/content-patterns/seedance-templates.md](references/content-patterns/seedance-templates.md)
- [references/content-patterns/anchor-image-strategy.md](references/content-patterns/anchor-image-strategy.md)（产品身份一致性）

### 用户要做抖音发布

最后读：

- [references/publishing/douyin-workflow.md](references/publishing/douyin-workflow.md)
- [references/publishing/adapter-boundary.md](references/publishing/adapter-boundary.md)
- [adapters/douyin-publisher.md](adapters/douyin-publisher.md)

## Aesthetic Style

生成任何内容前，都要确认 `brief.aesthetic_preset` 并贯穿全片：

1. 将预设的 `visual_keywords` 织入每个 shot 的 visual 描述
2. 将预设的 `seedance_style_anchor` 作为 seedance-job 的 `global_style_anchor`
3. 将预设的 `seedance_negative_additions` 追加到 `negative_constraints`
4. 让预设的 `motion_character` 指导镜头和动作表达

## Contract Discipline

所有核心产物都必须遵守 `schemas/`：

- `brief.schema.json`
- `script.schema.json`
- `storyboard.schema.json`
- `asset-manifest.schema.json`
- `seedance-job.schema.json`
- `publish-job.schema.json`
- `run-ledger.schema.json`
- `review-decision.schema.json`

如果用户只要 Markdown，也先按 schema 组织内容，再输出人类可读版本。

## Output Order

默认按这个顺序输出：

1. brief 摘要
2. script
3. storyboard
4. asset manifest
5. seedance job
6. review summary
7. review decision
8. publish job（如需要）
9. run ledger

## Adapter Rules

1. 先产出任务，再谈执行。
2. 外部执行是可选层，不是默认行为。
3. 长视频组装是本地后处理，不依赖外部平台。
4. 抖音发布适配器是独立边界，不要把浏览器自动化细节揉进核心 Skill 推理。
5. 如果适配器未安装或未配置，仍要完整产出任务文件。
6. 如果使用 vendored Douyin adapter，保留其许可证边界，不把其代码当成核心 Skill 内部逻辑叙述。

## Safety Boundary

不会做什么：

- 不会在 `review-decision.json` 未批准时执行 Seedance
- 不会自动执行任何外部平台操作（除非用户明确选择 `end-to-end` 模式并确认执行）
- 不会在用户未确认的情况下发布视频到抖音
- 不会把 brief 内容发送到第三方服务
- 不会修改或删除用户已有的文件
- 不会在适配器未安装时报错崩溃

什么时候停下来问用户：

- 用户要求执行外部平台操作时，先确认产物再执行
- brief 信息不足以判断视频类型或时长时
- 生成的产物未通过校验时

## Validation

交付前检查（由 `scripts/validate_artifacts.py` 自动执行）：

**结构校验：**
- brief 的模式、时长、比例明确
- `seedance-job` 满足平台数量和时长限制
- `publish-job` 至少具备平台、视频路径、标题、简介
- `review-decision` 具备审核状态
- `run-ledger` 能说明当前阶段和产物状态

**内容校验：**
- storyboard 每个 shot 的 visual/camera/action/audio 非空
- script 的 logline 和每个 segment 的 summary 非空
- asset-manifest 每个 item 的 name/description/prompt 非空
- seedance-job 每个 prompt_block 的 prompt 非空

**连续性校验：**
- storyboard 时间轴连续且不重叠
- 总时长匹配 brief 的 duration_seconds

**风格校验：**
- 如设了 aesthetic_preset，global_style_anchor 包含预设关键词
- negative_constraints 包含预设的附加约束

**相机校验：**
- Z 在 Z1-Z9，Y 在 Y1-Y7，X 在 X1-X4
- focal_length_mm 为标准值 (18/24/35/50/85/135)
- depth 为 shallow/medium/deep

## Failure Modes

遇到以下情况，停下来报告具体原因，不要猜测或跳过。详见 `references/failure-modes.md`。

### F1: Brief 信息不足
- **症状：** goal / duration_seconds / aspect_ratio 任一无法确定
- **动作：** 列出已确定和缺失的字段，问用户补齐最少必要信息
- **不做什么：** 不自己编造缺失字段，不假设默认值

### F2: 时长超限
- **症状：** 请求总时长 > 15s（Seedance 单次生成上限），或单 prompt_block > 15s
- **动作：** 自动应用 scene-split-edit-pipeline 策略，产出 scene_plan 拆分为多段
- **不做什么：** 不默默截断时长，不假装一条 prompt 能一步做完长视频

### F2.1: 审核未通过
- **症状：** `review-decision.json.status != approved`
- **动作：** 停在审核包阶段，只输出 review summary / review decision，不执行 Seedance
- **不做什么：** 不绕过审核关口继续调用 CLI

### F3: 素材引用断裂
- **症状：** storyboard 中引用的 asset_id 在 asset-manifest 中不存在，或反向（孤儿素材）
- **动作：** 标出断裂的引用链，回退到 storyboard 或 asset manifest 修正
- **不做什么：** 不跳过验证继续编译 seedance-job

### F4: Schema 校验失败
- **症状：** 产物不符合对应 JSON Schema 的 required 字段或 pattern 约束
- **动作：** 报告具体校验错误（哪个文件、哪个字段、期望什么、实际是什么），在 Step 8 修复循环中修正
- **不做什么：** 不输出不合规的 JSON 文件，不忽略校验错误

### F5: 适配器不可用
- **症状：** 用户要求执行 Seedance 生成或抖音发布，但 CLI/API key/素材/适配器任一缺失
- **动作：** 产出完整的 job 文件 + run-ledger，告知「已生成任务规格，执行需要适配器。当前只交付任务文件。」
- **不做什么：** 不假装执行、不跳过适配器直接调平台 API、不报错崩溃

### F5.1: 长视频未组装
- **症状：** 多段生成已完成，但用户仍需要单个最终视频文件
- **动作：** 调用 `python scripts/run_pipeline.py --dir <dir> --assemble`
- **不做什么：** 不把多段 block 当作最终交付成片

### F6: 许可证边界
- **症状：** 用户要求把 vendored adapter（AGPL-3.0）的代码逻辑写进核心 Skill 推理
- **动作：** 告知许可证边界，保持 adapter 独立调用，引用 NOTICE.md
- **不做什么：** 不把 AGPL 代码吸收进核心 Skill 叙述

### F7: 产品身份漂移
- **症状：** 多 block 生成后，各镜中产品面料/剪裁/颜色不一致（如 pb-01 蕾丝边、pb-02 光滑边、pb-03 不同颜色）
- **根因：** 纯 T2V 每次从随机噪声出发，无视觉锚点约束同一产品形态
- **动作：** 自动判断 `asset-manifest.json` C01 是否有 `resolved_path` → 无则走 AI 闭环（生成产品定妆照 → 注册 C01 → prompt 注入 `[Image1]` → I2V 重跑）
- **不做什么：** 不假装三个不同产品是同一个，不跳过锚图生成继续裸 T2V

## Example

用户说：

> 做一条 15 秒 9:16 的抖音视频，主题是 AI 帮人自动生成并发布短视频，先给我方案不要执行。

应当进入：

- `plan-only`
- 运行 `python scripts/run_pipeline.py --brief <brief.json> --output-dir <dir>`
- 产出完整 review package
- 停在 `pending-review`
- 不执行任何外部平台
