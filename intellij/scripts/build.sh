#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INTELLIJ_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SRC_DIR="$INTELLIJ_DIR/src"
ROOT_DIR="$(cd "$INTELLIJ_DIR/.." && pwd)"
PLATFORM_DOC="$INTELLIJ_DIR/README.md"
PYTHON_BIN="${PYTHON:-python3}"

PYTHON_PATH="$(command -v "$PYTHON_BIN")" || {
  echo "找不到 Python: $PYTHON_BIN" >&2
  exit 1
}
# Anchor the executable before changing cwd; keep the venv symlink intact.
PYTHON_BIN="$(cd "$(dirname "$PYTHON_PATH")" && pwd)/$(basename "$PYTHON_PATH")"

"$PYTHON_BIN" -c 'import PIL' >/dev/null 2>&1 || {
  echo "Python 缺少 Pillow。先运行 make setup，或用 PYTHON 指向已安装 Pillow 的解释器。" >&2
  exit 1
}

NAMES=(
  "$INTELLIJ_DIR/build/ref/all_reference_attribute_names.txt"
  "$INTELLIJ_DIR/build/ref/ide_language_attribute_names.txt"
  "$INTELLIJ_DIR/build/ref/ide_official_attribute_names.txt"
)
CHROME=(
  "$INTELLIJ_DIR/build/ref/ide_chrome_names.txt"
  "$INTELLIJ_DIR/build/ref/ide_official_chrome_names.txt"
)

cd "$SRC_DIR"

run() {
  "$PYTHON_BIN" "$@"
}

echo "== style =="
run check_style.py

echo "== editor schemes =="
run gen_icls.py --names "${NAMES[@]}" --chrome-names "${CHROME[@]}" \
  --outdir "$INTELLIJ_DIR/themes" --check

echo "== palette and parity checks =="
run check_collisions.py
run check_token_separation.py
run check_identity.py
run check_reverse_palette.py
run check_render_styles.py
run check_attribute_parity.py

echo "== theme package =="
run gen_theme_json.py

echo "== installer tests =="
bash "$SCRIPT_DIR/test_install.sh"

echo "== generated documentation =="
run gen_readme_table.py "$PLATFORM_DOC"
run gen_deviations.py "$PLATFORM_DOC"
run gen_mineral_doc.py "$PLATFORM_DOC"

echo "== shared palette =="
run "$ROOT_DIR/shared/export_palette.py"
run "$ROOT_DIR/shared/export_palette.py" --check
run "$ROOT_DIR/shared/tools/check_palette.py"

echo "== previews =="
run render_java.py >/dev/null
run render_ui.py >/dev/null
run render_diff_debug.py >/dev/null

echo "== artifact checks =="
run check_palette_usage.py
run check_freshness.py
run gen_verification_report.py

echo "Build complete."
