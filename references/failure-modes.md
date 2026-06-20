<!--
[INPUT]: 依赖 {SKILL.md、schemas、references/seedance} 的 {工作流规则与平台约束}
[OUTPUT]: 对外提供 {失败模式分类、症状识别、恢复步骤}
[POS]: {references} 的 {失败模式参考}，被 SKILL.md Failure Modes 段引用
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
-->

# Failure Modes

## Seedance 平台拒绝

| 失败 | 症状 | 根因 | 对策 |
|---|---|---|---|
| 时长超限 | 单 prompt block > 15s | 未拆分长视频 | 用 scene-split-edit-pipeline 拆成多个 prompt block |
| 素材超量 | @图片 + @视频 + @音频 > 12 | 素材规划未检查上限 | 合并同类素材、降低参考图数量 |
| 引用格式错误 | 使用了 @图1 而非 @图片1 | 未参照官方命名 | 检查 @图片1-9 / @视频1-3 / @音频1-3 格式 |
| 比例不匹配 | 请求 16:9 但用了 9:16 的 prompt 结构 | 上游参数透传错误 | 校验 seedance-job.aspect_ratio 与 brief.aspect_ratio 一致 |

## 编排失败

| 失败 | 症状 | 根因 | 对策 |
|---|---|---|---|
| 时间轴断裂 | storyboard 最后一个 shot 的 end_second ≠ 总时长 | 各 shot 时长未累加校验 | 补时间轴连续性检查 |
| 素材孤儿 | asset-manifest 有 asset_id 但 storyboard 无引用 | 素材规划与分镜脱节 | 交叉校验引用链 |
| 编号冲突 | 两个不同素材使用相同 C/S/P 编号 | 编号分配无唯一性保证 | 按素材类型顺序编号，不跳号不重用 |
| 契约版本不匹配 | JSON 文件缺少新 schema 的 required 字段 | schema 演进后旧产物未更新 | run-ledger 记录 schema 版本号 |

## 执行失败

| 失败 | 症状 | 根因 | 对策 |
|---|---|---|---|
| 适配器缺失 | 用户说"生成视频"但 seedance-executor 不可用 | 未检查适配器可用性 | 回退到 plan-only，产出完整 job 文件 |
| 登录态过期 | douyin_check_login 返回未登录 | cookie 过期 | 提示用户重新扫码登录 |
| SMS 验证超时 | 抖音要求短信验证但用户未及时输入 | 多因素认证 | 给用户 120 秒窗口，超时则保存当前状态退出 |
| 平台风控拦截 | 视频上传后状态为"审核不通过" | 内容触发平台审核 | 检查 must_avoid 清单，给出修改建议 |

## 预防原则

1. **先 dry-run，再执行。** plan-only 模式零外部依赖，始终可用。
2. **每步产出都过 schema 校验。** 不合规不进入下一步。
3. **外部操作用独立适配器。** 核心 Skill 不直接调平台 API。
4. **失败可追溯。** run-ledger 记录每一步的实际状态，不覆盖。
