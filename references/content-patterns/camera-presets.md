# Camera Presets Guide

从 `compiler_story.py` 提取的 purpose-to-codec 默认映射，结合四维相机编码系统。

## Purpose -> Codec 默认映射

| Purpose  | Z轴  | Y轴  | X轴  | 焦段mm | 景深   | 运镜             | 效果               |
|----------|------|------|------|--------|--------|------------------|--------------------|
| hook     | Z4   | Y4   | X1   | 35     | shallow| 快速推近         | 第一眼抓人         |
| setup    | Z5   | Y4   | X2   | 50     | medium | 中景稳定推进     | 交代空间和背景     |
| turn     | Z5   | Y4   | X2   | 50     | medium | 轻微横移配合主体 | 展示变化推进       |
| payoff   | Z3   | Y4   | X2   | 85     | shallow| 由中景推到近景   | 强调结果与完成状态 |
| close    | Z6   | Y4   | X4   | 50     | medium | 缓慢拉远         | 形成收束和留白     |

## 四维编码速查

- **Z轴(距离)**: Z1大特写 -> Z9大远景
- **Y轴(高度)**: Y1虫视 -> Y7垂直顶视
- **X轴(方位)**: X1正面, X2侧45, X3正侧, X4背面
- **F层(滤镜/焦段/叙事)**: 物理光学 + 身份叙事 + 构图几何

## 编码规则

- 每个镜头最多双轴运动，三轴同时变化 = 失控
- 焦段标准值: 18, 24, 35, 50, 85, 135
- 景深三档: shallow / medium / deep

## 长视频默认编码

| Phase            | Z轴  | Y轴  | X轴  | 焦段mm | 景深   |
|------------------|------|------|------|--------|--------|
| world-build      | Z7   | Y4   | X2   | 50     | deep   |
| change-push      | Z5   | Y4   | X2   | 50     | medium |
| emotional-close  | Z6   | Y4   | X4   | 50     | medium |

详细编码规则见 `references/seedance/camera-codec-source.md`。
