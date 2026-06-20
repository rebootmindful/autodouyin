<!--
[INPUT]: 依赖 {当前编译器能力、开放 brief 风险与多段续拍问题} 的 {精修方案}
[OUTPUT]: 对外提供 {通用兜底模板策略与人物一致性精修路径}
[POS]: {autodouyin-skill/topics} 的 {质量精修专题}，指导下一轮内容生成升级
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
-->

# Fallback Template And Identity Consistency

Date: 2026-06-20
Status: Implementation design

## Goal

解决两个当前会持续影响出品质量的问题：

1. 用户 brief 可能非常发散，无法稳定命中现有场景模板
2. 多段生成 / 拼凑视频时，人物样貌、衣着、气质与空间关系容易漂

目标不是“写更多模板就完事”，而是建立一套：

- **先归一，再落模板**
- **先锁人物，再编镜头**

的稳定策略。

## Problem A: Open Brief Does Not Match Existing Template

### Current Situation

当前 `compiler_content.py` 的显式增强主要覆盖：

- 通用 `workflow-explainer`
- 招聘宣传口播模板

它能跑，但有两个限制：

1. brief 如果过于抽象或混合多个目标，很容易回退到一个过于平的 `workflow-explainer`
2. 当 brief 的题材不属于既有模板时，内容会“可执行但不漂亮”

### Root Cause

当前系统仍然是“先猜 video_type，再直接套模板”。

这在以下场景容易失真：

- 概念广告
- 氛围片
- 诗性 / 抽象叙事
- 复杂人物设定
- 混合目的 brief（既想讲产品，又想讲人，又想讲故事）

### Recommended Fix: Two-Step Fallback

不要只靠 `video_type`，要引入 **Intent Layer**。

#### Step 1. Intent Classification

先把任何 brief 归一成更底层的表达意图：

- `explain`
- `sell`
- `recruit`
- `narrate`
- `showcase-character`
- `tour-space`
- `atmosphere`
- `mixed`

这层不直接决定最终模板，只决定“讲法重心”。

#### Step 2. Fallback Template Family

在 `video_type` 之外，再维护 3 套兜底模板族：

##### A. Information Template

适用于：

- 解释流程
- 招聘
- 产品说明
- JD 讲解

默认结构：

1. 开场明确主题
2. 中段分点解释
3. 收尾给行动指令

##### B. Demonstration Template

适用于：

- 产品展示
- 人物能力展示
- 操作流程展示
- before / after

默认结构：

1. 先给结果或主体
2. 展开关键动作 / 变化
3. 收在成果或亮点

##### C. Atmosphere Template

适用于：

- 抽象概念
- 情绪短片
- 品牌氛围片
- 无明确业务口播的“感觉型” brief

默认结构：

1. 建立主视觉与空间
2. 推进情绪 / 光线 / 动作层次
3. 留出余韵，不强塞说明

### Practical Rule

如果命中精确模板，则走精确模板。

如果没有命中，就走：

`brief -> intent -> fallback family -> segment copy`

而不是直接扔回一个平铺的 `workflow-explainer`。

## Problem B: Multi-Block Video Loses Identity

### Current Situation

现在系统已经有：

- `continuity_locks`
- `negative_constraints`
- `continuity_note`
- `@视频1` 续拍

这能减少漂移，但还不够。

用户真正关心的不是“系统写了 continuity lock”，而是：

- 人物脸不能变
- 衣服不能变
- 发型不能变
- 年龄感 / 气质不能变
- 镜头切过去后还是同一个人

### Root Cause

当前一致性仍然主要靠语言锁定，缺少**结构化角色锚点**。

语言锁定是必要条件，但不是充分条件。

如果没有明确的角色卡与素材锚点，模型会在长段 / 多段里自己“补全”，这就是漂移来源。

## Recommended Fix: Identity Lock Stack

### Layer 1. Character Sheet

为每个主角色增加结构化角色卡，不只写在 prompt 里。

建议新增到 `asset-manifest.json` 的 `Cxx` 项或独立子对象：

```json
{
  "asset_id": "C01",
  "type": "character",
  "name": "主讲人",
  "identity_lock": {
    "gender_presentation": "female",
    "approx_age_range": "25-32",
    "hair": "black shoulder-length straight hair",
    "outfit": "white shirt + dark blazer",
    "accessories": "small stud earrings",
    "body_shape": "slim",
    "speaking_style": "calm professional",
    "persona": "confident recruiter"
  }
}
```

重点不是字段名字，而是：

- **把人物一致性变成结构，而不是散在句子里**

### Layer 2. Reference Image Priority

对主讲人 / 主角色：

- 优先要求 `C01` 成为强制参考图
- 在所有 block 中持续引用 `@图片1`

如果没有角色参考图：

- 先明确告诉用户：长视频人物一致性风险升高
- 仍可生成，但要在 review summary 里标明风险等级

### Layer 3. Prompt-Level Identity Anchor

除了通用 continuity lock，再额外为角色加一段身份锚：

```text
主角保持同一张脸、同一发型、同一服装、同一年龄感和同一职业气质，不切换人物设定。
```

如果是招聘讲解类，还要加：

```text
保持同一位主讲人面对镜头讲解，口型、神态和职业感前后一致。
```

### Layer 4. Shot Transition Discipline

当镜头跨 block 时，不要突然切大变化。

更稳的顺序是：

1. 上一段结尾停在稳定的半身或中景
2. 下一段开头保留 0.8-1.5 秒微动作
3. 再推进到新的信息点

这条在人物视频里尤其重要，因为脸部漂移最常发生在“突然切到另一个更近的脸”。

### Layer 5. Wardrobe / Prop Echo

如果主角需要跨 2 段以上持续出现：

- 每段都要重复一个可见的衣着锚点
- 每段都尽量保留一个相同道具或相同背景元素

例如：

- 同一件白衬衫 + 深色西装
- 同一张工位桌面
- 同一块电商后台屏幕

空间锚越稳定，人物一致性越容易成立。

## No-Reference-Image Strategy

### Key Judgment

**没有参考图片时，不能承诺“绝对一致”，只能做“可控一致性”。**

这类问题本质上不是“再多写一句 prompt”就能解决，而是要把“谁是主角”变成生成链路中的可复用锚点。

### Recommended Priority

从稳到不稳，建议分 4 档：

#### Tier 1. Generate Anchor First, Then Reuse It

最稳做法不是直接做完整长视频，而是：

1. 先单独生成一个 4-6 秒的人物建立镜头
2. 从这个镜头抽帧
3. 把抽出的角色帧当作 `C01` 参考图
4. 后续所有 block / scene 都复用这张锚图

这相当于把“没有参考图”变成“系统先替用户造出参考图”。

#### Tier 2. Use First Successful Block As Canonical Identity

如果不额外单独做角色锚片，也至少要：

1. 让第一个 block 先稳定展示主角
2. 把这个 block 视为 canonical identity
3. 后续 `16-60s` 场景优先走 `segmented-extension`
4. 不要让后续 block 重新从零起片

也就是说：

- **先建立人，再继续讲故事**

#### Tier 3. Derive Stills Between Scenes

对 `>60s` 的 scene-split 模式：

1. 第一 scene 成功后
2. 自动从 scene 输出里截取 1-3 张稳定帧
3. 写回 `derived/C01_anchor_01.png` 之类的路径
4. 后续独立 scene 再把这些图喂回去

这是解决“跨 scene 无法直接用 @视频1 续拍”的最实用办法。

#### Tier 4. Pure Text-Only Continuity

这是最不稳、但仍可作为兜底的路径：

- 只靠角色卡
- 只靠 prompt 锁定
- 不喂任何参考图

它可以用，但必须在 review summary 里明确标成：

- `identity_risk = high`

### Practical Rules

#### Rule A. Prefer Extension Over Fresh Generation

如果用户没有参考图：

- `<=60s` 尽量走 `segmented-extension`
- 少做“每段都重新生成”

因为同一条视频的续拍，通常比多次独立生图/生视频更稳。

#### Rule B. First Block Must Be Character-Establishing

第一段不能太快切业务信息，应该先花 1-2 秒明确主角：

- 正脸或 3/4 侧脸
- 稳定光线
- 稳定衣着
- 稳定半身或中景

否则后面没有“谁是这个人”的 anchor。

#### Rule C. Reduce Face-Risk Shots

无参考图时，尽量少用：

- 极近景脸部切换
- 大角度脸部转向
- 强烈光线变化
- 剧烈动作后立刻切新场景

更稳的是：

- 中景
- 半身
- 小幅动作
- 平稳镜头推进

#### Rule D. Lock Outfit And One Visible Marker

人物一致性不要只写“同一人”。

至少还要锁：

- 发型
- 上衣
- 外套
- 一个可见配饰

例如：

```text
黑色直发，白衬衫，深色西装外套，左耳小耳钉，全片保持一致
```

这样即使脸有轻微漂移，观感也更容易被理解为“同一人物”。

#### Rule E. If No Anchor, Be Honest In Review

如果用户不给图，系统也没做首段抽帧回注，那么必须在 review summary 明写：

- 当前是 text-only identity lock
- 长段或跨 scene 有人物漂移风险

这不是保守，是诚实。

## Recommended Execution Upgrade

要把这件事真正落进系统，建议新增一个轻量执行策略字段：

```json
{
  "identity_strategy": "reference-image | first-block-anchor | derived-stills | text-only"
}
```

含义：

- `reference-image`
  用户本来就提供了人物图
- `first-block-anchor`
  用第一段建立人物后持续续拍
- `derived-stills`
  从前面生成的视频抽帧反哺后续 scene
- `text-only`
  没有图，只靠语言锁定

### Best Engineering Path

如果你要“精修出品”，推荐最终走：

1. 编译阶段生成 `identity_lock`
2. 执行阶段先产一个 anchor block
3. 自动抽 1-3 张人物稳定帧
4. 回注为 `C01` 参考图
5. 后续 scene / retry 都复用

这才是无参考图情况下，最接近“稳定人物一致性”的工程做法。

## Broken Link And Fix

### Broken Link

当前真正“断掉”的环节不是抽帧本身，而是：

1. 第一轮执行开始时没有锚图
2. 锚图只有在首段成功后才能生成
3. 如果执行链还是“一口气把所有 block 都当作同一轮请求规划”，那么：
   - dry-run 看不到后续段带锚图
   - review 难以确认哪一段开始真正受益于锚图

### Correct Fix

把无参考图执行链显式拆成两段：

#### Phase A. Anchor Round

- 只执行：
  - 第一段 `segment-base`
  - 或每个新 scene 的 `scene-base`
- 成功后立刻：
  - 抽 1-3 张稳定帧
  - 生成 `derived/C01_anchor_*.png`

#### Phase B. Continuation Round

- 从后续 block 开始继续
- 把 `derived/C01_anchor_*.png` 自动回注到：
  - CLI 路径的 `--image`
  - 官方 API 路径的 `input_image`

### Why This Is The Right Cut

这样做的好处：

1. 逻辑明确：先建人，再续拍
2. review 可解释：哪一段开始有锚图，一清二楚
3. retry 可复用：首段失败重来，后段不必盲跑
4. scene-split 可扩展：每个 scene 都能重新建锚

### Recommended Runtime Shape

建议未来把执行入口显式做成：

1. `--generate-anchor`
   - 只跑首段 / scene-base
2. `--extract-identity-stills`
   - 抽帧生成锚图
3. `--generate-rest`
   - 跑剩余 block / scene，并自动带锚图

如果不想暴露三个命令给用户，也至少要在内部保持这个状态机。

## Review-Time Quality Gates

对精修出品，建议新增两类 review gate。

### Gate A. Template Confidence

输出 review package 时，标记：

- `template_mode`: exact / fallback-information / fallback-demonstration / fallback-atmosphere
- `template_confidence`: high / medium / low

这样用户能知道这次是不是“强命中模板”。

### Gate B. Identity Risk

如果满足以下任一条件，就在 review summary 里标红：

- 长视频且无角色参考图
- 多段口播且角色近景占比高
- 人物设定描述不足（衣着 / 发型 / 年龄感缺失）

建议给 3 档：

- `low`: 有角色图 + 有角色卡 + 有稳定场景
- `medium`: 无图但有人物结构描述
- `high`: 既无图又无结构描述

## Minimal Implementation Plan

为避免再把系统做复杂，建议最小落地分 3 步。

### Step 1. Add Fallback Family Routing

在 `compiler_content.py` 增加：

- `infer_intent_family(brief)`
- `fallback copy builders`

先解决“开放 brief 不命中模板”的问题。

### Step 2. Add Character Sheet Fields

优先在 `asset-manifest` 的 `C01` 项增加：

- `identity_lock`
- `continuity_priority`

先不必一次性扩到所有角色。

### Step 3. Add Review Risk Labels

在 `review-summary.md` 加：

- `template_confidence`
- `identity_risk`

这样用户在执行前就能知道“这条片稳不稳”。

## Recommended Output Additions

建议在未来版本中，把以下字段加入正式产物：

### `script.json`

- `template_mode`
- `template_confidence`

### `storyboard.json`

- `identity_anchor`
- `transition_risk`

### `asset-manifest.json`

- `identity_lock`
- `continuity_priority`

### `review-summary.md`

- `template_mode`
- `identity_risk`
- `needs_reference_image`

## Key Judgment

要把系统从“能跑”推进到“精修出品”，关键不在于继续堆 prompt，而在于：

1. **任何 brief 都先落到稳定的意图层和兜底模板族**
2. **任何长视频人物都先落到结构化角色锚点，而不是只写一句保持一致**

这两步做对了，出片质量才会从“偶尔好”变成“可控地好”。
