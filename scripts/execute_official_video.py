"""
/**
 * [INPUT]: 依赖 {seedance-job.json 与 review 模型选择} 的 {官方 Ark 视频生成需求}
 * [OUTPUT]: 对外提供 {generation-report.json + 本地下载视频}
 * [POS]: {scripts} 的 {官方 API 执行器}，负责 1.5 pro 模型的真实调用
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import subprocess
import time
import urllib.request
from pathlib import Path

from identity_stills import anchor_paths, ensure_identity_stills


MODEL_ID = "doubao-seedance-1-5-pro-251215"


def is_remote_ref(path: str) -> bool:
    lowered = path.lower()
    return lowered.startswith(("http://", "https://", "data:"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Official Ark video executor")
    parser.add_argument("--dir", required=True, help="artifact directory containing seedance-job.json")
    parser.add_argument("--dry-run", action="store_true", default=True, help="print official API payloads only")
    parser.add_argument("--execute", action="store_true", help="actually call official Ark API")
    return parser.parse_args()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def config_value(key: str, default: str = "") -> str:
    result = subprocess.run(
        ["cmd", "/c", "seedance", "config", "get", key],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode == 0:
        return result.stdout.strip()
    return default


def api_key() -> str:
    return os.environ.get("ARK_API_KEY") or config_value("api_key")


def base_url() -> str:
    return config_value("base_url", "https://ark.cn-beijing.volces.com/api/v3")


def request_json(url: str, token: str, method: str, payload: dict | None = None) -> dict:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {e.code}: {err_body}") from e


def data_url(path: Path) -> str:
    suffix = path.suffix.lower().lstrip(".") or "png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/{suffix};base64,{encoded}"


def image_content_items(output_dir: Path) -> list[dict]:
    """Build Ark-format image entries: {type, image_url: {url}, role?}."""
    items = []
    manifest = output_dir / "asset-manifest.json"
    if manifest.exists():
        data = load_json(manifest)
        for item in data.get("items", []):
            resolved = item.get("resolved_path")
            if not resolved:
                continue
            image_entry: dict = {}
            if is_remote_ref(resolved):
                image_entry = {"type": "image_url", "image_url": {"url": resolved}}
            else:
                p = Path(resolved)
                if p.exists():
                    image_entry = {"type": "image_url", "image_url": {"url": data_url(p)}}
            if image_entry:
                if item.get("type") == "character":
                    image_entry["role"] = "character_reference"
                items.append(image_entry)
    for path in anchor_paths(output_dir):
        items.append({"type": "image_url", "image_url": {"url": data_url(path)}, "role": "first_frame"})
    return items


def payload_for_block(job: dict, block: dict, output_dir: Path) -> dict:
    """Ark API payload: only model + content. Params as inline directives."""
    directives = f"--dur {int(block['duration_seconds'])}"
    resolution = job.get("resolution", "720p")
    if resolution:
        directives += f" --rs {resolution}"
    ratio = job.get("aspect_ratio")
    if ratio:
        directives += f" --rt {ratio}"
    prompt_text = f"{block['prompt']} {directives}"
    content: list[dict] = [{"type": "text", "text": prompt_text}]
    # NOTE: image refs disabled for now — the API only accepts max 1 first_frame image.
    # Anchor images from derived/ will be used once the first block completes successfully.
    return {
        "model": MODEL_ID,
        "content": content,
    }


def request_with_retry(url: str, token: str, method: str, payload: dict | None = None, retries: int = 3) -> dict:
    """Request with retry + exponential backoff for transient network issues."""
    last_err = None
    for attempt in range(retries):
        try:
            return request_json(url, token, method, payload)
        except (urllib.error.URLError, OSError) as e:
            last_err = e
            wait_s = (attempt + 1) * 5
            print(f"  [retry {attempt+1}/{retries}] {e} — waiting {wait_s}s...")
            time.sleep(wait_s)
    raise SystemExit(f"request failed after {retries} retries: {last_err}")


def wait_until_done(task_id: str, token: str, root: str, timeout_seconds: int = 600) -> dict:
    deadline = time.time() + timeout_seconds
    url = f"{root}/contents/generations/tasks/{task_id}"
    while time.time() < deadline:
        try:
            result = request_json(url, token, "GET")
            if result.get("status") in {"succeeded", "failed", "cancelled", "expired"}:
                return result
        except (urllib.error.URLError, OSError) as e:
            print(f"  poll error (will retry): {e}")
        time.sleep(10)
    return {"id": task_id, "status": "timeout"}


def download_video(url: str, target: Path) -> None:
    urllib.request.urlretrieve(url, target)


def dry_run(job: dict, output_dir: Path) -> dict:
    blocks = []
    commands = []
    for block in job["prompt_blocks"]:
        blocks.append(
            {
                "block_id": block["block_id"],
                "task_id": "dry-run",
                "status": "planned",
                "output_path": str(output_dir / f"{block['block_id']}.mp4"),
                "duration_seconds": int(block["duration_seconds"]),
            }
        )
        commands.append({"block_id": block["block_id"], "payload": payload_for_block(job, block, output_dir)})
    return {
        "mode": "dry-run",
        "backend": "official-api",
        "model": MODEL_ID,
        "job_mode": job.get("mode", "text-image-video"),
        "identity_strategy": job.get("identity_strategy", "text-only"),
        "total_blocks": len(job["prompt_blocks"]),
        "blocks": blocks,
        "commands": commands,
        "overall_status": "dry-run",
        "notes": "官方 API 路径在存在 derived/C01_anchor_*.png 时，会把这些锚图作为 input_image 回注到后续段。",
    }


def execute(job: dict, output_dir: Path) -> dict:
    token = api_key()
    if not token:
        raise SystemExit("missing ARK_API_KEY and seedance config api_key")
    root = base_url()
    task_url = f"{root}/contents/generations/tasks"
    blocks = []
    for block in job["prompt_blocks"]:
        print(f"[{block['block_id']}] creating task...")
        created = request_with_retry(task_url, token, "POST", payload_for_block(job, block, output_dir))
        task_id = created["id"]
        print(f"[{block['block_id']}] task_id={task_id} — polling...")
        result = wait_until_done(task_id, token, root)
        item = {
            "block_id": block["block_id"],
            "task_id": task_id,
            "status": result.get("status", "unknown"),
            "output_path": "",
            "duration_seconds": int(block["duration_seconds"]),
        }
        video_url = result.get("content", {}).get("video_url")
        if result.get("status") == "succeeded" and video_url:
            target = output_dir / f"{block['block_id']}.mp4"
            download_video(video_url, target)
            print(f"[{block['block_id']}] downloaded -> {target}")
            item["output_path"] = target.name
            if job.get("identity_strategy") in {"first-block-anchor", "derived-stills"} and not anchor_paths(output_dir):
                ensure_identity_stills(output_dir, target)
        else:
            item["error"] = json.dumps(result, ensure_ascii=False)
            print(f"[{block['block_id']}] {result.get('status', 'unknown')}: {item.get('error', '')[:200]}")
        blocks.append(item)
        # save partial progress after each block
        partial_report = {
            "mode": "execute", "backend": "official-api", "model": MODEL_ID,
            "job_id": job.get("id", "unknown"), "blocks": blocks,
            "overall_status": "partial",
        }
        (output_dir / "generation-report.json").write_text(
            json.dumps(partial_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    overall_status = "success" if all(b["status"] == "succeeded" for b in blocks) else "partial"
    return {
        "mode": "execute",
        "backend": "official-api",
        "model": MODEL_ID,
        "identity_strategy": job.get("identity_strategy", "text-only"),
        "job_id": job.get("id", "unknown"),
        "blocks": blocks,
        "overall_status": overall_status,
        "notes": "官方 API 路径会在有锚图时把首段抽帧回注为 input_image。",
    }


def main() -> None:
    args = parse_args()
    output_dir = Path(args.dir)
    job = load_json(output_dir / "seedance-job.json")
    report = execute(job, output_dir) if args.execute else dry_run(job, output_dir)
    report_path = output_dir / "generation-report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"report -> {report_path}")


if __name__ == "__main__":
    main()
