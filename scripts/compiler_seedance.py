"""
/**
 * [INPUT]: 依赖 {brief、storyboard 与视频策略} 的 {Seedance 任务编译需求}
 * [OUTPUT]: 对外提供 {slot_plan 结构映射工具}
 * [POS]: {scripts} 的 {Seedance 工具模块}，纯结构，不含内容模板
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 *
 * 内容生成已迁移至 Agent 层 (见 SKILL.md Enrichment Workflow)。
 * 骨架生成见 compile_skeleton.py。
 * prompt 组装模式见 references/content-patterns/seedance-templates.md。
 */
"""

from __future__ import annotations


def slot_plan() -> list[dict]:
    return [
        {"ref": "@图片1", "asset_id": "C01", "usage": "主体一致性参考"},
        {"ref": "@图片2", "asset_id": "S01", "usage": "场景或空间背景参考"},
        {"ref": "@图片3", "asset_id": "P01", "usage": "关键道具、结果卡片或动作强化参考"},
    ]
