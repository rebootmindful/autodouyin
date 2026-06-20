"""
/**
 * [INPUT]: 依赖 {成功视频块} 的 {人物稳定帧提取需求}
 * [OUTPUT]: 对外提供 {derived/C01_anchor_*.png 与锚图元数据}
 * [POS]: {scripts} 的 {人物锚图工具模块}，服务执行期的一致性增强
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


def derived_dir(output_dir: Path) -> Path:
    path = output_dir / "derived"
    path.mkdir(parents=True, exist_ok=True)
    return path


def anchor_paths(output_dir: Path) -> list[Path]:
    return sorted(derived_dir(output_dir).glob("C01_anchor_*.png"))


def write_identity_report(output_dir: Path, source_video: Path, outputs: list[Path]) -> Path:
    report_path = derived_dir(output_dir) / "identity-stills-report.json"
    report_path.write_text(
        json.dumps(
            {
                "source_video": str(source_video),
                "identity_strategy": "derived-stills",
                "outputs": [str(path) for path in outputs],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return report_path


def extract_frame(video_path: Path, target: Path, seconds: float) -> None:
    cmd = [
        "ffmpeg",
        "-y",
        "-ss",
        str(seconds),
        "-i",
        str(video_path),
        "-frames:v",
        "1",
        str(target),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError(result.stderr[:1000] or "ffmpeg frame extraction failed")


def ensure_identity_stills(output_dir: Path, source_video: Path, count: int = 3) -> list[Path]:
    existing = anchor_paths(output_dir)
    if existing:
        return existing
    seconds_list = [0.5, 1.5, 2.5][: max(1, min(count, 3))]
    outputs = []
    for index, seconds in enumerate(seconds_list, start=1):
        target = derived_dir(output_dir) / f"C01_anchor_{index:02d}.png"
        extract_frame(source_video, target, seconds)
        outputs.append(target)
    write_identity_report(output_dir, source_video, outputs)
    return outputs
