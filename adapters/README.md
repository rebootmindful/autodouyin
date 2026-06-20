<!--
[INPUT]: 依赖 {核心 Skill 生成的 jobs} 的 {外部执行入口}
[OUTPUT]: 对外提供 {adapter 总览与接入方向}
[POS]: {adapters} 的 {适配层索引}
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
-->

# Adapters

这里记录可选适配器边界，而不是默认执行代码。

## Current

- `seedance-executor.md`
- `douyin-publisher.md`
- `douyin-upload-vendor/`

## Rule

核心 Skill 必须在没有适配器的情况下也能完成 `plan-only` 产物生成。

## Vendor

`douyin-upload-vendor/` 是直接引入的上游 adapter 源码，带独立许可证边界。

## Hygiene

- `douyin-upload-vendor/node_modules/` 不属于仓库正式资产，需要时在本地执行 `npm install`
- `douyin-upload-vendor/temp/` 是运行时目录，不应作为样例或发布内容保留
