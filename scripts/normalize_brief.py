"""
/**
 * [INPUT]: 依赖 {examples/brief 或用户输入} 的 {原始 brief 文本或 JSON}
 * [OUTPUT]: 对外提供 {符合 brief.schema.json 的标准化 brief}
 * [POS]: {scripts} 的 {输入归一化脚本}，为后续编译脚本提供稳定入口
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from compiler_types import infer_aesthetic_preset, infer_video_type, video_type_duration_profile


DEFAULTS = {
    "platform": "douyin",
    "mode": "plan-only",
    "aspect_ratio": "9:16",
}

ROLE_KEYWORDS = {
    "character": ["人物", "主角", "主持人", "讲解人", "人像", "portrait", "host", "speaker", "avatar", "model", "角色"],
    "scene": ["场景", "办公室", "工位", "背景", "workspace", "office", "room", "desk", "scene", "background"],
    "prop": ["产品", "商品", "道具", "卡片", "海报", "product", "prop", "item", "bottle", "cup"],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", help="raw brief json path")
    parser.add_argument("--goal", help="fallback goal text")
    parser.add_argument("--output", help="normalized brief path")
    return parser.parse_args()


def load_source(args: argparse.Namespace) -> dict:
    if args.input:
        return json.loads(Path(args.input).read_text(encoding="utf-8"))
    if args.goal:
        return {"goal": args.goal}
    raise SystemExit("need --input or --goal")


def infer_source_role(text: str) -> str:
    lowered = text.lower()
    for role, keywords in ROLE_KEYWORDS.items():
        if any(keyword.lower() in lowered for keyword in keywords):
            return role
    return "reference"


def normalize_source_material_files(source: dict) -> list[dict]:
    files = source.get("source_material_files") or []
    normalized = []
    for index, item in enumerate(files, start=1):
        if isinstance(item, str):
            path = item
            label = Path(path).name if "://" not in path else path
            role = infer_source_role(label)
            normalized.append({"id": f"src-{index:02d}", "role": role, "label": label, "path": path})
            continue
        path = str(item.get("path") or "").strip()
        if not path:
            continue
        label = str(item.get("label") or Path(path).name if "://" not in path else path)
        role = str(item.get("role") or infer_source_role(" ".join([label, path]))).strip()
        normalized.append(
            {
                "id": str(item.get("id") or f"src-{index:02d}"),
                "role": role if role in {"character", "scene", "prop", "reference"} else "reference",
                "label": label,
                "path": path,
            }
        )
    return normalized


def merge_defaults(source: dict) -> dict:
    brief = {**DEFAULTS, **source}
    brief["goal"] = str(brief.get("goal") or "").strip()
    video_type = infer_video_type(brief)
    brief["video_type"] = video_type
    if "duration_seconds" not in source:
        brief["duration_seconds"] = video_type_duration_profile(video_type)["default_duration_seconds"]
    brief["id"] = brief.get("id") or "brief-local-001"
    brief["aesthetic_preset"] = infer_aesthetic_preset(brief)
    brief["source_material_files"] = normalize_source_material_files(source)
    return brief


def write_output(brief: dict, output: str | None) -> None:
    text = json.dumps(brief, ensure_ascii=False, indent=2)
    if output:
        Path(output).write_text(text + "\n", encoding="utf-8")
        return
    print(text)


def main() -> None:
    args = parse_args()
    source = load_source(args)
    brief = merge_defaults(source)
    write_output(brief, args.output)


if __name__ == "__main__":
    main()
