<!--
[INPUT]: 依赖 {Douyin 发布流程与适配器需求} 的 {发布步骤}
[OUTPUT]: 对外提供 {publish-job 应对接的流程模型}
[POS]: {references/publishing} 的 {抖音发布流程参考}
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
-->

# Douyin Workflow

## Publish Video Flow

1. 检查登录状态
2. 进入上传页
3. 上传视频
4. 等待上传 / 转码
5. 填写标题和简介
6. 发布

## Login Flow

发布适配器必须接受多步登录推进：

1. 二维码扫码
2. 短信验证
3. 验证码输入
4. 登录完成

不要把它假装成“单步同步函数”。

## publish-job Minimum

- `platform`
- `video_path`
- `title`
- `description`
