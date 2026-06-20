"""
/**
 * [INPUT]: 依赖 {seedance-job.json + 素材文件} 的 {prompt blocks 与 asset refs}
 * [OUTPUT]: 对外提供 {generation-report.json + 视频文件}
 * [POS]: {scripts} 的 {Seedance 执行适配器}，连接编译产物与真实视频生成
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from identity_stills import anchor_paths, ensure_identity_stills

SEEDANCE_BIN = "seedance"


# ---------------------------------------------------------------
# Asset resolution
# ---------------------------------------------------------------

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}


def is_remote_ref(path: str) -> bool:
    lowered = path.lower()
    return lowered.startswith(("http://", "https://", "data:"))


def resolved_asset_paths(output_dir: Path) -> dict[str, str]:
    manifest = output_dir / "asset-manifest.json"
    if not manifest.exists():
        return {}
    data = json.loads(manifest.read_text(encoding="utf-8"))
    mapping = {}
    for item in data.get("items", []):
        if item.get("resolved_path"):
            mapping[item["asset_id"]] = item["resolved_path"]
    return mapping


def resolve_assets(job: dict, output_dir: Path) -> dict[str, Path | None]:
    """Map @图片N refs to actual file paths via slot_plan + asset files on disk."""
    slot_plan = job.get("slot_plan", [])
    found: dict[str, str | Path | None] = {}
    resolved_map = resolved_asset_paths(output_dir)

    search_dirs = [output_dir / "assets", output_dir / "derived", output_dir]

    for slot in slot_plan:
        ref = slot["ref"]  # e.g. "@图片1"
        asset_id = slot["asset_id"]  # e.g. "C01"
        resolved = None
        if asset_id in resolved_map:
            candidate = resolved_map[asset_id]
            if is_remote_ref(candidate):
                found[ref] = candidate
                continue
            candidate_path = Path(candidate)
            if candidate_path.exists():
                found[ref] = candidate_path
                continue
        for d in search_dirs:
            if not d.exists():
                continue
            for f in d.iterdir():
                if f.stem.upper() == asset_id.upper() and f.suffix.lower() in IMAGE_EXTS:
                    resolved = f
                    break
            if resolved:
                break
        found[ref] = resolved

    return found


def derived_anchor_images(job: dict, output_dir: Path) -> list[Path]:
    if job.get("identity_strategy") not in {"first-block-anchor", "derived-stills", "reference-image"}:
        return []
    return anchor_paths(output_dir)


# ---------------------------------------------------------------
# Command building
# ---------------------------------------------------------------

def build_command(
    block: dict,
    job: dict,
    assets: dict[str, str | Path | None],
    output_dir: Path,
    prev_video: Path | None = None,
    model_alias: str | None = None,
) -> list[str]:
    """Build seedance generate CLI command for one prompt block."""
    duration = block["end_second"] - block["start_second"]
    ratio = job.get("aspect_ratio", "9:16")

    # Write prompt to temp file to avoid shell escaping
    prompt_file = output_dir / f".prompt_{block['block_id']}.txt"
    prompt_file.write_text(block["prompt"], encoding="utf-8")

    cmd = [SEEDANCE_BIN, "generate", f"@{prompt_file}"]
    cmd.extend(["--duration", str(duration)])
    cmd.extend(["--ratio", ratio])

    # Image refs from slot_plan
    for ref in block.get("image_refs", []):
        path = assets.get(ref)
        if path:
            cmd.extend(["--image", str(path)])

    # Derived character anchors: once extracted from the first successful block,
    # reuse them for later blocks to stabilize face, outfit and persona.
    existing_images = {str(path) for ref, path in assets.items() if path}
    for anchor in derived_anchor_images(job, output_dir):
        if str(anchor) not in existing_images:
            cmd.extend(["--image", str(anchor)])

    # Video refs (segmented-extension: previous output)
    if prev_video and block.get("video_refs"):
        cmd.extend(["--video", str(prev_video)])

    if model_alias:
        cmd.extend(["--model", model_alias])

    cmd.extend(["--wait", "--json"])
    cmd.extend(["--output", str(output_dir / f"{block['block_id']}.mp4")])
    cmd.extend(["--timeout", "600"])

    return cmd


# ---------------------------------------------------------------
# Validation
# ---------------------------------------------------------------

def validate(job: dict, assets: dict[str, str | Path | None]) -> list[str]:
    """Pre-execution validation per contract."""
    issues = []
    ratio = job.get("aspect_ratio", "9:16")

    for block in job.get("prompt_blocks", []):
        bid = block.get("block_id", "?")
        dur = block["end_second"] - block["start_second"]
        if dur > 15:
            issues.append(f"{bid}: duration {dur}s exceeds 15s limit")
        if dur < 4:
            issues.append(f"{bid}: duration {dur}s below 4s minimum")

    # Count total assets per block
    for block in job.get("prompt_blocks", []):
        bid = block.get("block_id", "?")
        total = len(block.get("image_refs", [])) + len(block.get("video_refs", [])) + len(block.get("audio_refs", []))
        if total > 12:
            issues.append(f"{bid}: total refs {total} exceeds Rule of 12")

    # Check asset availability (warn, not block)
    missing = [ref for ref, path in assets.items() if path is None]
    if missing:
        issues.append(f"warning: assets not found for {missing} (will generate without them)")

    return issues


# ---------------------------------------------------------------
# Execution
# ---------------------------------------------------------------

def run_block(cmd: list[str], block_id: str) -> dict:
    """Execute one seedance generate command and return result."""
    print(f"\n{'='*60}")
    print(f"[{block_id}] executing...")
    print(f"  cmd: {' '.join(cmd[:4])}... (prompt in file)")
    print(f"{'='*60}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=660, encoding="utf-8")
        stdout = result.stdout.strip()

        if result.returncode == 0 and stdout:
            try:
                data = json.loads(stdout)
                return {
                    "block_id": block_id,
                    "task_id": data.get("task_id", "unknown"),
                    "status": "success",
                    "output_path": data.get("output_path", ""),
                    "raw": data,
                }
            except json.JSONDecodeError:
                return {
                    "block_id": block_id,
                    "task_id": "unknown",
                    "status": "success",
                    "output_path": stdout.split("\n")[-1] if stdout else "",
                    "raw": stdout[:500],
                }
        else:
            return {
                "block_id": block_id,
                "task_id": "unknown",
                "status": "failed",
                "error": result.stderr[:500] if result.stderr else f"exit code {result.returncode}",
                "output_path": "",
            }
    except subprocess.TimeoutExpired:
        return {
            "block_id": block_id,
            "task_id": "unknown",
            "status": "timeout",
            "error": "exceeded 660s timeout",
            "output_path": "",
        }
    except FileNotFoundError:
        return {
            "block_id": block_id,
            "task_id": "unknown",
            "status": "failed",
            "error": "seedance CLI not found in PATH",
            "output_path": "",
        }


# ---------------------------------------------------------------
# Main
# ---------------------------------------------------------------

def main() -> None:
    p = argparse.ArgumentParser(description="Seedance executor: seedance-job.json -> video")
    p.add_argument("--dir", required=True, help="output directory containing seedance-job.json")
    p.add_argument("--dry-run", action="store_true", default=True, help="print commands without executing (default)")
    p.add_argument("--execute", action="store_true", help="actually run seedance generate")
    p.add_argument("--seedance-bin", default=None, help="path to seedance binary (default: auto-detect)")
    p.add_argument("--model", choices=["fast", "standard"], default=None, help="2.0 CLI model alias")
    args = p.parse_args()

    global SEEDANCE_BIN
    if args.seedance_bin:
        SEEDANCE_BIN = args.seedance_bin
    else:
        import shutil
        found = shutil.which("seedance")
        if found:
            SEEDANCE_BIN = found

    output_dir = Path(args.dir)
    job_path = output_dir / "seedance-job.json"
    if not job_path.exists():
        print(f"error: {job_path} not found", file=sys.stderr)
        sys.exit(1)

    job = json.loads(job_path.read_text(encoding="utf-8"))
    assets = resolve_assets(job, output_dir)
    mode = job.get("mode", "text-image-video")

    # Validate
    issues = validate(job, assets)
    errors = [i for i in issues if not i.startswith("warning:")]
    warnings = [i for i in issues if i.startswith("warning:")]

    for w in warnings:
        print(f"  WARN: {w}")
    if errors:
        print("validation errors:", file=sys.stderr)
        for e in errors:
            print(f"  ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    blocks = job["prompt_blocks"]
    is_dry = not args.execute

    if is_dry:
        # --- DRY RUN ---
        dry_report = {
            "mode": "dry-run",
            "total_blocks": len(blocks),
            "job_mode": mode,
            "blocks": [],
            "commands": [],
            "asset_requirements": {ref: str(path) if path else "MISSING" for ref, path in assets.items()},
            "total_asset_count": sum(1 for p in assets.values() if p is not None),
            "overall_status": "dry-run",
        }
        for block in blocks:
            cmd = build_command(block, job, assets, output_dir, model_alias=args.model)
            output_path = str(output_dir / f"{block['block_id']}.mp4")
            dry_report["blocks"].append({
                "block_id": block["block_id"],
                "task_id": "dry-run",
                "status": "planned",
                "output_path": output_path,
                "duration_seconds": block["end_second"] - block["start_second"],
            })
            dry_report["commands"].append({
                "block_id": block["block_id"],
                "command": " ".join(cmd),
                "duration_seconds": block["end_second"] - block["start_second"],
            })
            print(f"\n[{block['block_id']}] {block['start_second']}-{block['end_second']}s")
            print(f"  {' '.join(cmd[:6])}...")

        report_path = output_dir / "generation-report.json"
        report_path.write_text(json.dumps(dry_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"\ndry-run report -> {report_path}")
        for block in blocks:
            pf = output_dir / f".prompt_{block['block_id']}.txt"
            pf.unlink(missing_ok=True)

    else:
        # --- EXECUTE ---
        print(f"executing {len(blocks)} blocks (mode: {mode})...")
        report_blocks = []
        prev_video = None

        for block in blocks:
            # For segmented-extension, pass previous output as --video
            cmd = build_command(block, job, assets, output_dir, prev_video, args.model)
            result = run_block(cmd, block["block_id"])
            report_blocks.append(result)

            # Track previous output for sequential modes
            if result["status"] == "success" and result.get("output_path"):
                prev_video = Path(result["output_path"])
                if job.get("identity_strategy") in {"first-block-anchor", "derived-stills"} and not anchor_paths(output_dir):
                    ensure_identity_stills(output_dir, prev_video)
                    assets = resolve_assets(job, output_dir)
            elif mode != "text-image-video":
                print(f"  WARN: {block['block_id']} failed, sequential chain broken")
                prev_video = None

        overall = "success" if all(r["status"] == "success" for r in report_blocks) else "partial"

        report = {
            "job_id": job.get("id", "unknown"),
            "blocks": [{k: v for k, v in r.items() if k != "raw"} for r in report_blocks],
            "overall_status": overall,
        }
        report_path = output_dir / "generation-report.json"
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"\n{'='*60}")
        print(f"overall: {overall}")
        print(f"report -> {report_path}")

        # Cleanup prompt temp files
        for block in blocks:
            pf = output_dir / f".prompt_{block['block_id']}.txt"
            pf.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
