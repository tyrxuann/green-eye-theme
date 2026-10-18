#!/usr/bin/env bash
# 兼容入口：真正的构建逻辑在 green_eye.py（跨平台）。
# Windows 可直接运行: python green_eye.py build
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
PYTHON_BIN="${PYTHON:-python3}"

if [ -x "$PYTHON_BIN" ]; then
  PYTHON_BIN="$(cd "$(dirname "$PYTHON_BIN")" && pwd)/$(basename "$PYTHON_BIN")"
else
  PYTHON_BIN="$(command -v "$PYTHON_BIN")" || {
    echo "找不到 Python: ${PYTHON:-python3}" >&2
    exit 1
  }
fi

exec "$PYTHON_BIN" "$ROOT_DIR/green_eye.py" build "$@"
