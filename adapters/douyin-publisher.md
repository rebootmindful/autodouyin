<!--
[INPUT]: 依赖 {publish-job} 的 {发布所需环境与流程}
[OUTPUT]: 对外提供 {Douyin 发布适配器接口约定}
[POS]: {adapters} 的 {发布适配器契约}
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
-->

# Douyin Publisher Contract

当前推荐实现：

- 优先使用 [douyin-upload-vendor](./douyin-upload-vendor/NOTICE.md) 里的 MCP / daemon / CDP 代码
- 核心 Skill 只负责为它准备 `publish-job`

## Input

- `publish-job.json`

## Output

- 发布状态
- 登录阶段
- 失败详情
- 可选截图路径

## Required Capabilities

1. 登录状态检查
2. 多轮验证推进
3. 视频上传
4. 标题 / 简介填写
5. 发布结果检测

## Local Bridge

当前仓库已提供两个本地桥接脚本：

1. `scripts/douyin_check_login.mjs`
2. `scripts/douyin_publish_job.mjs`

用法：

```bash
node scripts/douyin_check_login.mjs
node scripts/douyin_check_login.mjs --sms-code 123456
node scripts/douyin_publish_job.mjs --job examples/outputs/publish-job.json
```

本地依赖准备：

```bash
cd adapters/douyin-upload-vendor
npm install
```

## Warning

这是平台自动化边界，不属于核心 Skill 逻辑。
