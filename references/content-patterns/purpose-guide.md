# Purpose Guide

叙事目的指南：每个 purpose 对 visual / action / audio 的要求，按 video_type 分化。

## 五拍结构 (短视频 <= 15s)

| Purpose | 核心任务                           | 情绪     |
|---------|------------------------------------|----------|
| hook    | 前2-3秒建立钩子，先给结果感或异常点 | urgent   |
| setup   | 交代场景、人物、任务关系            | focused  |
| turn    | 画面发生明确变化，进入执行或冲突     | active   |
| payoff  | 给出最重要的成果展示或高潮动作       | confident|
| close   | 回稳并落版，留下可执行预期           | resolved |

<= 4s 简化为两拍: hook + payoff。

## 三/五段结构 (长视频 > 15s)

| Phase           | 核心任务                    | 情绪     |
|-----------------|-----------------------------|----------|
| world-build     | 建立世界与空间关系          | calm     |
| setup-flow      | 展开工作流与界面 (>60s才有) | focused  |
| change-push     | 变化推进与升级              | active   |
| peak-moment     | 高潮与成果展示 (>60s才有)   | confident|
| emotional-close | 情绪收束与落点              | resolved |

## Per-Type 视觉指导

### workflow-explainer
- hook: 竖屏开场直接给结果感，突出自动化能力
- setup: 切到工作台与界面，信息密度可读
- turn: 系统开始生成，视觉信息逐步加速
- payoff: 结果面板集中展示，核心成果清晰可见
- close: 画面停在待发布状态，形成收束

### product-demo
- hook: 直接打产品结果镜头，先给强展示感
- setup: 产品 UI 主界面和关键结果卡片，层级清楚
- turn: 核心流程连续演示，能力以卡片/面板/动效打开
- payoff: 核心卖点展示，价值一眼可见
- close: 品牌名或完成状态定格，短促有力

### narrative-story
- hook: 压力先立住，主角困境和截止压力
- setup: 主角、桌面、时间、未完成工作，问题具象化
- turn: AI 介入，局面逆转
- payoff: 主角从焦虑到放松，结果展示
- close: 停在发布成功前一刻，情绪落点

### character-action
- hook: 角色亮相给姿态与目标，立住人物
- setup: 能量聚合，界面元素受控聚集
- turn: 动作推进段，动作与镜头一起升级
- payoff: 高速动作与信息流汇聚，强完成镜头
- close: 英雄式背面或正面收束姿态

### space-tour
- hook: (沿用 workflow-explainer)
- setup: 切到空间入口与路线，建立参观顺序
- turn: (沿用 workflow-explainer)
- payoff: 关键空间细节和材质集中展示
- close: 收束在空间终点，完整参观闭环

## 音频指导

- hook: 短促抓注意力（电子音/能量音/压迫感环境音）
- setup: 轻量环境音 + 操作音，强调真实氛围
- turn: 节奏加快，配乐上扬，反馈音密集
- payoff: 确认音/击中音，配乐最高点停留
- close: 收束音效，留下呼吸感/松一口气的尾音

## 连续性原则

- 同一角色保持一致五官、服装、发型
- 同一场景保持一致环境、光线、空间关系
- 长视频每段重复风格锁定语句
- 尾帧状态 = 下一段起始状态

## 类型专属 Content Pattern

本文件提供通用 purpose 指导。以下类型有专属 pattern，包含更具体的视觉词汇、音频设计模式和 prompt 范例：

- `product-demo` -> [product-demo-pattern.md](product-demo-pattern.md)
- `narrative-story` -> [narrative-story-pattern.md](narrative-story-pattern.md)
- `character-action` -> [character-action-pattern.md](character-action-pattern.md)

Agent 填充骨架时，先读本文件的通用指导，再读对应类型的专属 pattern。
