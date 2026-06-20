#!/usr/bin/env bash
# [INPUT]: 依赖 {requirements、vendor package.json 与本机环境} 的 {一键安装需求}
# [OUTPUT]: 对外提供 {profile 化 bootstrap 安装与 smoke 验证}
# [POS]: {scripts} 的 {POSIX 安装入口}，把 clone 后的手工安装收敛成一条命令
# [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md

set -euo pipefail

PROFILE="${1:-core}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$ROOT/.venv"
PYTHON_EXE="$VENV_DIR/bin/python"
PIP_EXE="$VENV_DIR/bin/pip"
VENDOR_DIR="$ROOT/adapters/douyin-upload-vendor"
SKIP_SMOKE="${SKIP_SMOKE:-0}"

ensure_command() {
  command -v "$1" >/dev/null 2>&1 || { echo "Missing required command: $1" >&2; exit 1; }
}

ensure_venv() {
  ensure_command python3
  if [ ! -x "$PYTHON_EXE" ]; then
    python3 -m venv "$VENV_DIR"
  fi
  "$PYTHON_EXE" -m pip install --upgrade pip >/dev/null
  "$PIP_EXE" install -r "$ROOT/requirements.txt" >/dev/null
}

install_vendor() {
  ensure_command node
  ensure_command npm
  (
    cd "$VENDOR_DIR"
    npm install
  )
}

run_smoke() {
  local out_dir
  out_dir="$(mktemp -d)"
  "$PYTHON_EXE" "$ROOT/scripts/run_pipeline.py" --brief "$ROOT/examples/brief/minimal-douyin-video.json" --output-dir "$out_dir"
  "$PYTHON_EXE" "$ROOT/scripts/validate_artifacts.py" --dir "$out_dir"
}

ensure_venv

case "$PROFILE" in
  publish|all)
    install_vendor
    ;;
  core|showcase|generate-cli|generate-official|assemble)
    ;;
  *)
    echo "Unsupported profile: $PROFILE" >&2
    exit 1
    ;;
esac

"$PYTHON_EXE" "$ROOT/scripts/doctor.py" --profile "$PROFILE"

if [ "$SKIP_SMOKE" != "1" ] && [[ "$PROFILE" =~ ^(core|showcase|generate-cli|generate-official|assemble|all)$ ]]; then
  run_smoke
fi

echo "bootstrap complete: $PROFILE"
