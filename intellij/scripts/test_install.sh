#!/usr/bin/env bash
# 兼容入口：安装器集成测试现在是 tests/test_install.py（跨平台，不用 shasum）。
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

exec "$PYTHON_BIN" -m unittest discover -s "$ROOT_DIR/tests" -p "test_install.py" -v
