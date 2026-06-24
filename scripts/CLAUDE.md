<!--
[INPUT]: 依赖 {根目录 CLAUDE.md 与脚本实现} 的 {编译、校验、执行职责}
[OUTPUT]: 对外提供 {scripts 子树的局部地图与入口说明}
[POS]: {scripts} 的 {L2 局部地图}，统领编译、校验、执行与组装脚本
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
-->

# CLAUDE.md

## Scope

`scripts/` 保存 skill 的本地可执行主链：

- brief 标准化
- 审核包编译
- schema + 业务校验
- Seedance 执行
- 长视频组装
- 最小统一入口

## Key Files

- `normalize_brief.py`：把输入归一化为 `brief.json`
- `compile_skeleton.py`：生成稳定骨架
- `compiler_content.py`：用确定性模板填充完整审核包
- `compile_pipeline.py`：直接产出完整 review package
- `validate_artifacts.py`：schema + 内容 + 平台规则校验
- `execute_seedance.py`：Seedance dry-run / execute
- `execute_official_video.py`：Ark API 官方路径，含 [Image1] 锚图检测与 I2V first_frame 注入
- `compile_from_prompts.py`：从 shot_prompts.json 编译完整审核包，保留/注入 [Image1] 锚点前缀
- `creative_writer.py`：LLM 创作层入口，含 --direct 导演引擎模式
- `assemble_video.py`：多段视频本地组装
- `run_pipeline.py`：统一入口，收敛 compile / approve / generate / assemble

## Rules

- 优先保持主链简单，不再引入额外 orchestrator 层。
- 对用户可见的正式产物，只能落在输出目录，不留无主临时文件。
- 任意执行前规则变化，必须同步更新：
  - 对应 schema
  - `validate_artifacts.py`
  - `README.md`
