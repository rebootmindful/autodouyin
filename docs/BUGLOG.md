# Bug Log — autodouyin

记录真实闭环中遇到的 bug 与修复，避免重复踩坑。

---

## BUG-001: execute_official_video.py API payload 格式不兼容 Ark API

**日期**: 2026-06-23
**严重度**: CRITICAL
**症状**: HTTP 400 Bad Request，无有效错误信息
**根因**: `payload_for_block()` 把 `resolution`/`ratio`/`duration` 作为独立 JSON 字段传给 Ark API，但 Ark API 只接受 `model` + `content`，参数必须以 `--dur --rs --rt` 内联指令形式嵌入 prompt 文本末尾。
**参考**: `happy-video-gen/skills/.../providers/ark.ts` 的 payload 格式
**修复**: 
- 移除 `resolution`/`ratio`/`duration` 独立字段
- 拼入 `directives = f"--dur {N} --rs {res} --rt {ratio}"`
- 最终 payload: `{"model": MODEL_ID, "content": [{"type": "text", "text": prompt + directives}]}`
**文件**: `scripts/execute_official_video.py:payload_for_block()`

---

## BUG-002: Ark API 网络不稳定导致轮询超时/SSL断连

**日期**: 2026-06-23
**严重度**: HIGH
**症状**: POST 创建任务成功，但 `wait_until_done` 轮询时抛 `TimeoutError` 或 `SSL: UNEXPECTED_EOF_WHILE_READING`
**根因**: 到 `ark.cn-beijing.volces.com` 的网络连接不稳定（GFW/跨境因素）
**修复**:
1. 为 POST 添加 `request_with_retry()` 函数（3 次重试 + 指数回退 5s/10s/15s）
2. `wait_until_done` 内轮询的 GET 错误改为 warn + 继续轮询，而非直接崩溃
3. `execute()` 中每完成一个 block 就保存 `generation-report.json`（partial progress）
**文件**: `scripts/execute_official_video.py`

---

## BUG-003: image_content_items 触发 Ark API "at most one first_frame image" 限制

**日期**: 2026-06-23
**严重度**: HIGH
**症状**: HTTP 400: "expected at most one first frame image content but got 3 instead"
**根因**: `image_content_items()` 把 asset-manifest 中的 character/scene/prop 条目编码为 base64 image_url 并嵌入 content 数组。Ark API 限制最多 1 张 `first_frame` 图片，且图片 role 标记不规范导致 API 误判。
**修复**:
- `segment-base` 模式 block 跳过所有图片引用（纯 text-to-video）
- 图片引用仅保留给后续 extension block，且需在首段生成成功后有了真实锚图再用
- 注释掉 `image_content_items` 调用，待后续支持正确的 first_frame 格式后恢复
**文件**: `scripts/execute_official_video.py:payload_for_block()`

---

## BUG-004: assembly concat 路径重复拼接（双重 work/x/work/x/pb.mp4）

**日期**: 2026-06-23
**严重度**: MEDIUM
**症状**: ffmpeg concat 报 "Impossible to open 'work/recruit-pets/work/recruit-pets/pb-01.mp4'"
**根因**: `execute()` 写 `output_path` 时用了相对路径 `str(target)` → `work/recruit-pets/pb-01.mp4`。`assemble_video.py:generated_paths()` 读到后再拼接 `directory / path` → `work/recruit-pets/work/recruit-pets/pb-01.mp4`。
**修复**:
1. `execute_official_video.py`: `item["output_path"] = target.name`（只存文件名）
2. `assemble_video.py`: concat list 用绝对路径而非相对路径
**文件**: `scripts/execute_official_video.py`, `scripts/assemble_video.py`

---

## BUG-005: ffmpeg subtitles filter Windows 路径转义失败

**日期**: 2026-06-23
**严重度**: MEDIUM
**症状**: ffmpeg 报 `Unable to parse "original_size" option value "Usershooji..." as image size`
**根因**: PowerShell 环境下 ffmpeg filter 参数中的 Windows 路径（含 `\` 和 `:`）被错误解析。`:` 是 ffmpeg filter 参数分隔符，`\` 被吃掉。
**修复**: 在 Git Bash 下运行 ffmpeg，使用相对路径 + forward slash，避免 PowerShell 转义问题。
**Workaround**: `cd` 到目标目录 → `ffmpeg -vf "subtitles=subtitles.srt:force_style=..."`（相对路径，无冒号无反斜杠）
**文件**: 非代码 bug，操作环境问题。记录供参考。

---

## BUG-006: compiler_content.py 硬编码虚构品牌名 "戈蓝公司"

**日期**: 2026-06-23
**严重度**: CRITICAL
**症状**: 编译产出中所有招聘相关文案、角色描述、场景描述均出现 "戈蓝公司"/"戈蓝电商" 占位品牌名，全链路污染到 seedance prompt、字幕、发布文案。
**根因**: `compiler_content.py` 在 `recruiting_lines()`、`recruiting_visual()`、`asset_item_text()`、`publish_description()` 中硬编码 "戈蓝公司" 作为虚构占位品牌名（7 处）。
**为何是设计错误**: 模板编译器不应包含虚构品牌名。品牌名称应由用户 brief 提供，或使用通用措辞（如 "品牌"/"我们"）。
**修复**: 所有 "戈蓝公司" 替换为通用措辞（"品牌"/"我们"），详见 commit。
**文件**: `scripts/compiler_content.py` (lines 213, 215, 260, 346, 347, 352, 470)
**教训**: LLM 辅助编写模板时容易无脑继承虚构占位符。Code review 必须检查模板输出是否含有非通用实体名。

---

## BUG-007: 模板关键词匹配导致创意内容被接管

**日期**: 2026-06-23
**严重度**: CRITICAL
**症状**: brief 同时包含"招聘"关键词和"宠物猫狗搞笑反转"创意描述时，编译器全量接管为"人物面对镜头讲解 JD"的通用招聘视频，所有创作元素被丢弃。
**根因**: `is_recruiting_video()` 在 `infer_intent_family()` 中优先级最高且互斥。一旦命中 recruiting 关键词，直接返回 "recruit"，后续 character/atmosphere/narrative 判断全被跳过。`recruit-exact` 模板是接管式而非增强式，用硬编码的 `recruiting_visual/action/audio` 覆盖所有内容。
**修复 (三层递进)**:
1. **L1**: brief schema 新增 `template_override` 字段，支持显式指定 `"none"` 跳过全部模板接管，或 `"recruit-exact"` 强制使用。
2. **L2**: 新增 `is_creative_recruiting()` 函数——检测 `CREATIVE_CONTENT_SIGNALS`（宠物/猫/狗/搞笑/反转/对话等），结合 `video_type`（character-action/narrative-story）判断是否为创作型招聘视频。当 `is_creative_recruiting()` 返回 True 时：
   - `fill_script()`: 保留创作 segment，末尾注入招聘行动号召
   - `fill_storyboard()`: 使用 fallback 创作模板，末段自然过渡至招聘 CTA
   - `asset_item_text()`: 生成"角色-C01"/"场景-S01"而非"招聘讲解人"
   - `fill_publish()`: 融合创作内容 + 招聘信息
   - Pure recruit（无创作元素）保持原有 `recruit-exact` 行为不变。
3. **L3 (未来)**: 用 LLM 做意图分类，支持多标签混合意图。
**文件**: `scripts/compiler_content.py`, `schemas/brief.schema.json`
**验证**: creative recruit brief → template_mode="fallback-information" + 末段 CTA 注入。Pure recruit brief → template_mode="recruit-exact" 保持不变。
