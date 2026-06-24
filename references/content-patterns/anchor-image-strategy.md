<!--
[INPUT]: 依赖 {asset-manifest.json, execute_official_video.py} 的 {C01 锚图注册与 I2V 注入}
[OUTPUT]: 对外提供 {产品身份一致性的自动检测与 AI 闭环修复策略}
[POS]: {references/content-patterns} 的 {锚图策略参考}, 被 SKILL.md Identity 段与 failure-modes.md F7 引用
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
-->

# Anchor Image Strategy（锚图策略）

## 问题本质

纯 T2V（Text-to-Video）模型每次生成从随机噪声初始化。同一段产品描述分三次生成 → 三个不同的产品形态。这是扩散模型的架构性质，不是参数调优能解决的。

## 解法：I2V 锚图闭环

```
   纯 T2V（失败）                  锚图 I2V（正确）
   ┌──────────┐                   ┌──────────────┐
   │ prompt   │                   │ 产品定妆照    │ ← AI 生成或用户提供
   └────┬─────┘                   └──────┬───────┘
        │                                │
   ┌────▼────┐                      ┌────▼────┐
   │ 随机噪声 │                      │ first_frame
   └────┬────┘                      └────┬────┘
        │                                │
   ┌────▼────┐                      ┌────▼────┐
   │ 视频块1  │ 产品A               │ 视频块1  │ 产品X
   └─────────┘                      └─────────┘
   ┌─────────┐                      ┌─────────┐
   │ 视频块2  │ 产品B ≠ A           │ 视频块2  │ 产品X (一致)
   └─────────┘                      └─────────┘
   ┌─────────┐                      ┌─────────┐
   │ 视频块3  │ 产品C ≠ A,B         │ 视频块3  │ 产品X (一致)
   └─────────┘                      └─────────┘
```

## 自动判断逻辑

```
Step 0: 检查 asset-manifest.json → C01.resolved_path 指向存在的文件?
  ├── YES → 直接注入 I2V, 跳过生成
  └── NO  → AI 闭环
```

## AI 闭环详细步骤

### Step A: 生成产品定妆照

调用图片生成 API（GPT-Image2 / DALL-E / Stable Diffusion），prompt 要求：

- 产品正面/45度展示
- 白底或干净纯色背景（便于视频模型做背景分离）
- ghost mannequin（隐形人台）或平坦展示
- 不出现真人、面部、品牌文字、logo
- 9:16 竖屏比例（与视频 aspect_ratio 一致）
- 2K 分辨率保证纹理细节

输出路径: `{output_dir}/assets/C01-product-anchor.png`

### Step B: 注册 C01 锚点

更新 `asset-manifest.json`:

```json
{
  "asset_id": "C01",
  "type": "character",
  "name": "产品锚图",
  "resolved_path": "assets/C01-product-anchor.png",
  "required": true,
  "continuity_priority": "high"
}
```

关键：`type: "character"` 触发 `execute_official_video.py` 中的 `character_reference → first_frame` 路由。

### Step C: Prompt 注入 [Image1]

每个 prompt block 的 prompt 开头前置：

```
以参考图[Image1]中的{产品名}产品为视觉锚点, 保持面料纹理、剪裁结构、颜色完全一致。
```

### Step D: 重编译

```bash
python scripts/compile_pipeline.py --brief <brief.json> --output-dir <dir>
```

### Step E: I2V 执行

`execute_official_video.py:125-136` 检测到 `[Image1]` → 自动将 C01 图 base64 编码，以 `first_frame` role 注入 Ark API content 数组：

```python
if "[Image1]" in block.get("prompt", ""):
    imgs = image_content_items(output_dir)
    char_imgs = [img for img in imgs if img.get("role") == "character_reference"]
    if char_imgs:
        char_imgs[0]["role"] = "first_frame"
        content.append(char_imgs[0])
```

结果：所有 prompt block 从同一张锚图出发生成 → 产品形态被锁死。

## 安全审核注意

Ark API 对"真人身体 + 内衣/泳装"组合有严格安全过滤（`OutputVideoSensitiveContentDetected`）。锚图本身不触发审核（图片模型无此限制），但视频 prompt 中的实穿描述可能触发。对策：

- 锚图用 ghost mannequin（无人脸无皮肤暴露）
- 视频 prompt 优先用衣架/人台/极近特写（肩颈、面料局部）避开全身皮肤
- 如必须实穿：背面视角、剪影逆光、肩带锁骨区域特写

## 与 identity_stills 的关系

| 机制 | 时机 | 用途 |
|------|------|------|
| **anchor image (本文)** | 视频生成前 | 所有 block 共享同一产品锚图 |
| **identity stills** | 首 block 生成后 | 从 pb-01 抽帧回注后续 block，保持人物一致 |

两者互补：anchor image 解决产品一致性问题，identity stills 解决人物/角色一致性问题。
