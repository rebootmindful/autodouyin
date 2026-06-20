# Review Summary

## 当前状态
- 状态：pending-review
- 说明：请先审核方案，再批准执行 Seedance。
- 生成前必须选择模型：`doubao-seedance-1-5-pro-251215` 或 `seedance-2.0-fast/standard`

## Brief
- 目标：做一个 75 秒的长流程视频，完整展示从 brief、脚本、分镜、视频任务到发布准备的全链路
- 时长：75s
- 比例：9:16
- 视频类型：workflow-explainer
- 策略：scene-split-edit-pipeline
- 模板模式：fallback-information
- 模板置信度：low
- 人物一致性策略：derived-stills
- 人物一致性风险：medium

## 参考素材绑定
- 未提供可直接消费的参考图文件，当前依赖文本锁定或后续抽帧锚图。

## Script Segments
- seg-01 world-build 15s: 围绕目标分点说明：建立世界与空间关系，让观众先看懂环境。 主题围绕“做一个 75 秒的长流程视频，完整展示从 brief、脚本、分镜、视频任务到发布准备的全链路”展开。
- seg-02 setup-flow 15s: 围绕目标分点说明：把主要流程展开，让结构进入视野。 主题围绕“做一个 75 秒的长流程视频，完整展示从 brief、脚本、分镜、视频任务到发布准备的全链路”展开。
- seg-03 change-push 15s: 围绕目标分点说明：把变化推起来，让系统、动作和信息同步升级。 主题围绕“做一个 75 秒的长流程视频，完整展示从 brief、脚本、分镜、视频任务到发布准备的全链路”展开。
- seg-04 peak-moment 15s: 围绕目标分点说明：把高潮结果推到最强，形成强记忆点。 主题围绕“做一个 75 秒的长流程视频，完整展示从 brief、脚本、分镜、视频任务到发布准备的全链路”展开。
- seg-05 emotional-close 15s: 围绕目标分点说明：把节奏收回来，让画面与情绪落点稳定。 主题围绕“做一个 75 秒的长流程视频，完整展示从 brief、脚本、分镜、视频任务到发布准备的全链路”展开。

## Prompt Blocks
- pb-01 15s / mode=scene-base
- pb-02 15s / mode=scene-base
- pb-03 15s / mode=scene-base
- pb-04 15s / mode=scene-base
- pb-05 15s / mode=scene-base

## 执行建议
- 当前未检测到人物参考图，建议先用首段建立主角，再复用续拍。
- 如果追求精修出品，建议从首段视频抽 1-3 张稳定帧回写为 C01 锚图。

## 执行方式
- 只批准并选模型：`python scripts/run_pipeline.py --dir <dir> --approve --model doubao-seedance-1-5-pro-251215`
- 批准后生成：`python scripts/run_pipeline.py --dir <dir> --generate`
