"""
/**
 * [INPUT]: 依赖 {brief 或现有产物目录} 的 {编译、审核和执行控制}
 * [OUTPUT]: 对外提供 {最小统一运行入口}
 * [POS]: {scripts} 的 {主编排入口}，收敛 review gate、生成和组装的用户操作
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from compile_pipeline import compile_to_directory, ensure_dir, load_brief
from validate_artifacts import validate_directory


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Unified AutoDouyin pipeline")
    parser.add_argument("--brief", help="input brief json")
    parser.add_argument("--output-dir", help="artifact output dir")
    parser.add_argument("--dir", help="existing artifact dir")
    parser.add_argument("--approve", action="store_true", help="mark review approved")
    parser.add_argument("--generate", action="store_true", help="run execute_seedance after approval")
    parser.add_argument("--execute", action="store_true", help="use real seedance execution instead of dry-run")
    parser.add_argument("--assemble", action="store_true", help="assemble generated blocks after execution")
    parser.add_argument("--prepare-publish", action="store_true", help="upload video and fill publish form, but do not click publish")
    parser.add_argument("--extract-identity-stills", action="store_true", help="extract anchor stills from generated blocks")
    parser.add_argument("--model", help="execution model: doubao-seedance-1-5-pro-251215 | seedance-2.0-fast | seedance-2.0-standard")
    return parser.parse_args()


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append_ledger_step(directory: Path, name: str, status: str, artifacts: list[str], notes: str) -> None:
    ledger_path = directory / "run-ledger.json"
    ledger = load_json(ledger_path)
    timestamp = now_iso()
    ledger.setdefault("steps", []).append(
        {
            "name": name,
            "status": status,
            "started_at": timestamp,
            "ended_at": timestamp,
            "artifacts": artifacts,
            "notes": notes,
        }
    )
    write_json(ledger_path, ledger)


def artifact_dir_from_args(args: argparse.Namespace) -> Path:
    if args.brief:
        if not args.output_dir:
            raise SystemExit("--brief requires --output-dir")
        return ensure_dir(args.output_dir)
    if args.dir:
        return Path(args.dir)
    raise SystemExit("provide either --brief/--output-dir or --dir")


def compile_phase(args: argparse.Namespace, directory: Path) -> None:
    brief = load_brief(args.brief)
    issues = compile_to_directory(brief, directory)
    if issues:
        raise SystemExit("\n".join(issues))
    print(f"compiled review package -> {directory}")


def approve_phase(directory: Path, selected_model: str | None) -> None:
    review_path = directory / "review-decision.json"
    ledger_path = directory / "run-ledger.json"
    review = load_json(review_path)
    review["status"] = "approved"
    review["reviewer"] = "user"
    review["approved_at"] = now_iso()
    review["selected_model"] = selected_model or review.get("selected_model", "")
    if not review.get("notes"):
        review["notes"] = "用户已批准，允许执行。"
    write_json(review_path, review)

    ledger = load_json(ledger_path)
    ledger["status"] = "approved"
    ledger["current_stage"] = "approved"
    write_json(ledger_path, ledger)
    append_ledger_step(
        directory,
        "approve-review",
        "success",
        ["review-decision.json"],
        f"审核已批准，选定模型：{review['selected_model'] or '未指定'}。",
    )
    print("review status -> approved")


def ensure_approved(directory: Path) -> None:
    review = load_json(directory / "review-decision.json")
    if review.get("status") != "approved":
        raise SystemExit("review-decision.json is not approved")
    if not review.get("selected_model"):
        raise SystemExit("review-decision.json has no selected_model")


def cli_model_alias(model_name: str) -> str:
    mapping = {
        "seedance-2.0-fast": "fast",
        "seedance-2.0-standard": "standard",
    }
    if model_name not in mapping:
        raise SystemExit(f"unsupported CLI model route: {model_name}")
    return mapping[model_name]


def update_ledger_stage(directory: Path, status: str, stage: str) -> None:
    ledger_path = directory / "run-ledger.json"
    ledger = load_json(ledger_path)
    ledger["status"] = status
    ledger["current_stage"] = stage
    write_json(ledger_path, ledger)


def cleanup_temp_files(directory: Path) -> None:
    for path in directory.glob(".prompt_*.txt"):
        path.unlink(missing_ok=True)


def prepare_publish_page(directory: Path, timeout: int = 600000) -> None:
    publish_job = directory / "publish-job.json"
    if not publish_job.exists():
        raise SystemExit(f"missing {publish_job}")
    update_ledger_stage(directory, "success", "publish-prepared")
    cmd = [
        "node",
        "scripts/douyin_publish_job.mjs",
        "--job",
        str(publish_job),
        "--timeout",
        str(timeout),
        "--prepare-only",
    ]
    result = subprocess.run(cmd, text=True)
    if result.returncode != 0:
        update_ledger_stage(directory, "failed", "failed")
        append_ledger_step(
            directory,
            "prepare-publish-page",
            "failed",
            ["publish-job.json"],
            "上传页准备失败，请检查浏览器日志或页面状态。",
        )
        raise SystemExit(result.returncode)
    append_ledger_step(
        directory,
        "prepare-publish-page",
        "success",
        ["publish-job.json"],
        "已上传视频并填好标题、简介、封面，停在发布前等待人工确认。",
    )


def extract_identity_stills(directory: Path) -> None:
    update_ledger_stage(directory, "success", "generated")
    cmd = ["python", "scripts/extract_identity_stills.py", "--dir", str(directory)]
    result = subprocess.run(cmd, text=True)
    if result.returncode != 0:
        append_ledger_step(
            directory,
            "extract-identity-stills",
            "failed",
            ["derived/identity-stills-report.json"],
            "人物锚图提取失败，请检查 generation-report.json 与视频块输出。",
        )
        raise SystemExit(result.returncode)
    append_ledger_step(
        directory,
        "extract-identity-stills",
        "success",
        ["derived/identity-stills-report.json"],
        "已从首个成功视频块提取人物锚图，可供后续重试或跨 scene 复用。",
    )


def run_execute(directory: Path, execute: bool) -> None:
    ensure_approved(directory)
    issues = validate_directory(directory)
    if issues:
        raise SystemExit("\n".join(issues))
    update_ledger_stage(directory, "partial", "generating")
    review = load_json(directory / "review-decision.json")
    selected_model = review["selected_model"]
    if selected_model == "doubao-seedance-1-5-pro-251215":
        cmd = ["python", "scripts/execute_official_video.py", "--dir", str(directory)]
    else:
        cmd = [
            "python",
            "scripts/execute_seedance.py",
            "--dir",
            str(directory),
            "--model",
            cli_model_alias(selected_model),
        ]
    cmd.append("--execute" if execute else "--dry-run")
    result = subprocess.run(cmd, text=True)
    if result.returncode != 0:
        update_ledger_stage(directory, "failed", "failed")
        append_ledger_step(
            directory,
            "generate-video",
            "failed",
            ["generation-report.json"],
            "视频生成失败，详见 generation-report.json 或命令输出。",
        )
        raise SystemExit(result.returncode)
    update_ledger_stage(directory, "partial" if not execute else "success", "generated")
    append_ledger_step(
        directory,
        "generate-video",
        "success",
        ["generation-report.json"],
        "视频生成阶段完成。" if execute else "已完成 dry-run，生成了执行计划报告。",
    )
    cleanup_temp_files(directory)


def run_assemble(directory: Path) -> None:
    ledger = load_json(directory / "run-ledger.json")
    current_status = ledger.get("status", "partial")
    update_ledger_stage(directory, current_status, "assembling")
    cmd = ["python", "scripts/assemble_video.py", "--dir", str(directory)]
    result = subprocess.run(cmd, text=True)
    if result.returncode != 0:
        update_ledger_stage(directory, "failed", "failed")
        append_ledger_step(
            directory,
            "assemble-video",
            "failed",
            ["assembly-report.json"],
            "视频组装失败，详见 assembly-report.json 或命令输出。",
        )
        raise SystemExit(result.returncode)
    final_status = "success" if (directory / "generation-report.json").exists() and current_status != "pending-review" else current_status
    update_ledger_stage(directory, final_status, "assembled")
    append_ledger_step(
        directory,
        "assemble-video",
        "success",
        ["assembly-report.json", "assembled-video.mp4"],
        "视频组装完成，已产出最终成片。",
    )
    cleanup_temp_files(directory)


def main() -> None:
    args = parse_args()
    directory = artifact_dir_from_args(args)

    if args.brief:
        compile_phase(args, directory)
        return

    if args.approve:
        approve_phase(directory, args.model)

    if args.generate:
        run_execute(directory, execute=args.execute)

    if args.assemble:
        run_assemble(directory)

    if args.prepare_publish:
        prepare_publish_page(directory)

    if args.extract_identity_stills:
        extract_identity_stills(directory)

    if not any([args.approve, args.generate, args.assemble, args.prepare_publish, args.extract_identity_stills]):
        issues = validate_directory(directory)
        if issues:
            raise SystemExit("\n".join(issues))
        print("artifacts are valid")


if __name__ == "__main__":
    main()
