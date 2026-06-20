# Review Summary

## 当前状态
- 状态：pending-review
- 说明：请先审核方案，再批准执行 Seedance。
- 生成前必须选择模型：`doubao-seedance-1-5-pro-251215` 或 `seedance-2.0-fast/standard`

## Brief
- 目标：做一条 15 秒 9:16 的抖音视频，主题是 AI 帮人自动生成并发布短视频
- 时长：15s
- 比例：9:16
- 视频类型：workflow-explainer
- 策略：five-beat-short-video
- 模板模式：fallback-information
- 模板置信度：low
- 人物一致性策略：text-only
- 人物一致性风险：high

## 参考素材绑定
- 未提供可直接消费的参考图文件，当前依赖文本锁定或后续抽帧锚图。

## Script Segments
- seg-01 setup 6s: 围绕目标分点说明：交代主体、场景和工作流背景。 主题围绕“做一条 15 秒 9:16 的抖音视频，主题是 AI 帮人自动生成并发布短视频”展开。
- seg-02 payoff 9s: 围绕目标分点说明：集中展示结果，让价值清楚落地。 主题围绕“做一条 15 秒 9:16 的抖音视频，主题是 AI 帮人自动生成并发布短视频”展开。

## Prompt Blocks
- pb-01 6s / mode=single-sequence
- pb-02 9s / mode=single-sequence

## 执行建议
- 当前未检测到人物参考图，建议先用首段建立主角，再复用续拍。
- 如果追求精修出品，建议从首段视频抽 1-3 张稳定帧回写为 C01 锚图。

## 执行方式
- 只批准并选模型：`python scripts/run_pipeline.py --dir <dir> --approve --model doubao-seedance-1-5-pro-251215`
- 批准后生成：`python scripts/run_pipeline.py --dir <dir> --generate`
