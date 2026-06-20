"""
/**
 * [INPUT]: 依赖 {brief 与视频类型策略} 的 {叙事结构编排需求}
 * [OUTPUT]: 对外提供 {时长切分与时间轴计算工具}
 * [POS]: {scripts} 的 {叙事工具模块}，纯算术，不含内容模板
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 *
 * 内容生成已迁移至 Agent 层 (见 SKILL.md Enrichment Workflow)。
 * 骨架生成见 compile_skeleton.py。
 * 叙事指导见 references/content-patterns/purpose-guide.md。
 */
"""

from __future__ import annotations


def split_lengths(total: int, count: int) -> list[int]:
    base, extra = divmod(total, count)
    return [base + (1 if i < extra else 0) for i in range(count)]


def segment_times(segments: list[dict]) -> list[tuple[int, int]]:
    start = 0
    result = []
    for seg in segments:
        end = start + seg["estimated_seconds"]
        result.append((start, end))
        start = end
    return result
