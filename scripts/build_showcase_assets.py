"""
/**
 * [INPUT]: 依赖 {run_pipeline.py、examples/brief 与现有契约} 的 {showcase 样例构建需求}
 * [OUTPUT]: 对外提供 {showcase 示例目录 + README 首屏 PNG/GIF + 图标资产}
 * [POS]: {scripts} 的 {展示资产构建器}，把真实命令回放转成公开可见产物
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
PLAN_DIR = ROOT / "examples" / "showcase-plan-only"
DRY_DIR = ROOT / "examples" / "showcase-long-dry-run"
MIN_BRIEF = ROOT / "examples" / "brief" / "minimal-douyin-video.json"
LONG_BRIEF = ROOT / "examples" / "brief" / "ultra-long-workflow.json"
BG = "#f4efe5"
FG = "#171717"
MUTED = "#5a5a5a"


def choose_python() -> list[str]:
    override = os.environ.get("AUTODOUYIN_PYTHON")
    candidates: list[list[str]] = []
    if override:
        candidates.append([override])
    candidates.append([sys.executable])
    for raw in ("python", "python3"):
        candidates.append([raw])
    if os.name == "nt":
        candidates.append(["py", "-3"])
    for cmd in candidates:
        try:
            probe = subprocess.run(
                cmd + ["-c", "import jsonschema"],
                cwd=ROOT,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        except OSError:
            continue
        if probe.returncode == 0:
            return cmd
    raise SystemExit(
        "No Python interpreter with `jsonschema` available. "
        "Set AUTODOUYIN_PYTHON to a working interpreter path."
    )


PYTHON = choose_python()


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, cwd=ROOT, check=True)


def reset_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    names = ["msyhbd.ttc", "msyh.ttc"] if bold else ["msyh.ttc", "segoeui.ttf"]
    for name in names:
        path = Path("C:/Windows/Fonts") / name
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def wrap(text: str, width: int) -> list[str]:
    return textwrap.wrap(text, width=width, replace_whitespace=False) or [text]


def text_block(draw: ImageDraw.ImageDraw, lines: list[str], x: int, y: int, *, ft, fill: str) -> int:
    for line in lines:
        draw.text((x, y), line, font=ft, fill=fill)
        y += int(ft.size * 1.45)
    return y


def pill(draw: ImageDraw.ImageDraw, x: int, y: int, text: str, *, fill: str, text_fill: str) -> None:
    ft = font(24, bold=True)
    left, top, right, bottom = draw.textbbox((0, 0), text, font=ft)
    box = (x, y, x + (right - left) + 38, y + (bottom - top) + 24)
    draw.rounded_rectangle(box, radius=18, fill=fill)
    draw.text((x + 19, y + 10), text, font=ft, fill=text_fill)


def render_card(title: str, subtitle: str, bullets: list[str], out_path: Path, accent: str) -> Image.Image:
    image = Image.new("RGB", (1440, 900), BG)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((56, 56, 1384, 844), radius=36, fill="white", outline="#e7dfd0", width=3)
    draw.rectangle((56, 56, 86, 844), fill=accent)
    draw.text((124, 120), title, font=font(56, bold=True), fill=FG)
    text_block(draw, wrap(subtitle, 42), 124, 210, ft=font(28), fill=MUTED)
    y = 330
    for bullet in bullets:
        draw.ellipse((126, y + 14, 146, y + 34), fill=accent)
        y = text_block(draw, wrap(bullet, 54), 170, y, ft=font(30), fill=FG) + 20
    out_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(out_path)
    return image


def render_icon(text: str, out_path: Path, size: int, accent: str) -> None:
    image = Image.new("RGB", (size, size), accent)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((0, 0, size - 1, size - 1), radius=size // 5, fill=accent)
    ft = font(size // 3, bold=True)
    left, top, right, bottom = draw.textbbox((0, 0), text, font=ft)
    x = (size - (right - left)) // 2
    y = (size - (bottom - top)) // 2 - 6
    draw.text((x, y), text, font=ft, fill="white")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(out_path)


def build_examples() -> None:
    reset_dir(PLAN_DIR)
    reset_dir(DRY_DIR)
    run(PYTHON + ["scripts/run_pipeline.py", "--brief", str(MIN_BRIEF), "--output-dir", str(PLAN_DIR)])
    run(PYTHON + ["scripts/run_pipeline.py", "--brief", str(LONG_BRIEF), "--output-dir", str(DRY_DIR)])
    run(PYTHON + ["scripts/run_pipeline.py", "--dir", str(DRY_DIR), "--approve", "--model", "seedance-2.0-fast"])
    run(PYTHON + ["scripts/run_pipeline.py", "--dir", str(DRY_DIR), "--generate"])


def plan_bullets() -> list[str]:
    review = load_json(PLAN_DIR / "review-decision.json")
    ledger = load_json(PLAN_DIR / "run-ledger.json")
    names = [path.name for path in sorted(PLAN_DIR.iterdir()) if path.is_file()]
    return [
        "命令：python scripts/run_pipeline.py --brief examples/brief/minimal-douyin-video.json --output-dir examples/showcase-plan-only",
        f"审核状态：{review['status']}；当前阶段：{ledger['current_stage']}",
        "产物："
        + ", ".join(names),
        "特点：方案先出完整审核包，再停在 pending-review，不会越过执行关口。",
    ]


def dry_bullets() -> list[str]:
    report = load_json(DRY_DIR / "generation-report.json")
    ledger = load_json(DRY_DIR / "run-ledger.json")
    blocks = [f"{item['block_id']}={item['status']}" for item in report.get("blocks", [])]
    return [
        "命令：python scripts/run_pipeline.py --dir examples/showcase-long-dry-run --approve --model seedance-2.0-fast",
        "命令：python scripts/run_pipeline.py --dir examples/showcase-long-dry-run --generate",
        f"生成状态：{report['overall_status']}；当前阶段：{ledger['current_stage']}",
        "dry-run blocks：" + ", ".join(blocks),
    ]


def render_gif(plan_image: Image.Image, dry_image: Image.Image) -> None:
    frames = [plan_image, dry_image, plan_image.copy()]
    ASSETS.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        ASSETS / "showcase-flow.gif",
        save_all=True,
        append_images=frames[1:],
        duration=[1800, 1800, 1400],
        loop=0,
    )


def render_scorecard() -> None:
    image = Image.new("RGB", (1200, 720), "#171717")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((48, 48, 1152, 672), radius=36, fill="#1f1f1f", outline="#333333", width=2)
    draw.text((94, 110), "AutoDouyin Showcase", font=font(54, bold=True), fill="white")
    draw.text((94, 190), "本地验证：审核包 -> 批准 -> dry-run -> 可选 prepare-publish", font=font(28), fill="#c9c9c9")
    pill(draw, 94, 270, "plan-only", fill="#e4572e", text_fill="white")
    pill(draw, 294, 270, "approved", fill="#145c9e", text_fill="white")
    pill(draw, 494, 270, "dry-run", fill="#3c8d2f", text_fill="white")
    lines = [
        "真实安装：npx skills add . --skill autodouyin -y",
        "真实主链：python scripts/run_pipeline.py --brief examples/brief/minimal-douyin-video.json --output-dir examples/showcase-plan-only",
        "长视频 dry-run：python scripts/run_pipeline.py --dir examples/showcase-long-dry-run --generate",
        "差异点：不是再写一段 prompt，而是产出可审核、可回放、可停手的对象链。",
    ]
    text_block(draw, lines, 94, 360, ft=font(28), fill="white")
    image.save(ASSETS / "showcase-scorecard.png")


def main() -> None:
    build_examples()
    review = render_card(
        "审核包先行，不越权执行",
        "真实回放来自 examples/showcase-plan-only。它展示的是 AutoDouyin 的核心绝活：先把 brief 编译成可审核对象链，而不是直接赌一段 prompt。",
        plan_bullets(),
        ASSETS / "showcase-review-package.png",
        "#e4572e",
    )
    dry = render_card(
        "批准后 dry-run，再决定是否真生成",
        "真实回放来自 examples/showcase-long-dry-run。长视频先按 scene-split 编排，再由统一入口推进 approve -> generate，执行层状态回写 run-ledger。",
        dry_bullets(),
        ASSETS / "showcase-dry-run.png",
        "#145c9e",
    )
    render_gif(review, dry)
    render_scorecard()
    render_icon("AD", ASSETS / "icon-large.png", 512, "#e4572e")
    render_icon("AD", ASSETS / "icon-small.png", 256, "#145c9e")
    shutil.copyfile(ASSETS / "icon-large.png", ASSETS / "logo.png")
    shutil.copyfile(ASSETS / "icon-small.png", ASSETS / "composer-icon.png")


if __name__ == "__main__":
    main()
