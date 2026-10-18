#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INTELLIJ_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
INSTALLER="$SCRIPT_DIR/install.sh"
TMP_HOME="$(mktemp -d)"
trap 'rm -rf "$TMP_HOME"' EXIT
CONFIG_DIR="$TMP_HOME/Library/Application Support/JetBrains/IntelliJIdea2026.2"
mkdir -p "$CONFIG_DIR/plugins" "$CONFIG_DIR/colors"

run_installer() {
  HOME="$TMP_HOME" bash "$INSTALLER" --config-dir "$CONFIG_DIR" "$@"
}

snapshot() {
  find "$CONFIG_DIR" -type f -print | sort | while IFS= read -r file; do
    printf '%s ' "$file"
    shasum -a 256 "$file" | cut -c1-16
  done
}

artifact=""
for candidate in "$INTELLIJ_DIR"/dist/GreenEye-Theme-*.jar; do
  [ -f "$candidate" ] || continue
  artifact="$candidate"
done
[ -f "$artifact" ] || {
  echo "缺少插件包，请先运行 make build。" >&2
  exit 1
}

pass() { printf '  ✅ %s\n' "$1"; }
fail() { printf '  ❌ %s\n' "$1" >&2; exit 1; }

echo "安装器测试（临时 HOME：${TMP_HOME}）"

run_installer --yes >/dev/null && pass "全新安装" || fail "全新安装"
before="$(snapshot)"
output="$(run_installer --yes)"
[ "$before" = "$(snapshot)" ] &&
  printf '%s' "$output" | grep -q "无需改动" &&
  pass "重复安装幂等" || fail "重复安装"

cp "$artifact" "$CONFIG_DIR/plugins/GreenEye-Theme-0.0.1.jar"
mkdir -p "$CONFIG_DIR/plugins/GreenEye-Theme/META-INF"
unzip -p "$artifact" META-INF/plugin.xml > "$CONFIG_DIR/plugins/GreenEye-Theme/META-INF/plugin.xml"
cp "$INTELLIJ_DIR/themes/Green-Eye-Mineral.icls" "$CONFIG_DIR/colors/"
printf 'com.greeneye.intellij.theme\nsome.other.plugin\n' > "$CONFIG_DIR/disabled_plugins.txt"
run_installer --yes >/dev/null
[ ! -e "$CONFIG_DIR/plugins/GreenEye-Theme-0.0.1.jar" ] &&
  [ ! -e "$CONFIG_DIR/plugins/GreenEye-Theme" ] &&
  [ ! -e "$CONFIG_DIR/colors/Green-Eye-Mineral.icls" ] &&
  grep -Fxq "some.other.plugin" "$CONFIG_DIR/disabled_plugins.txt" &&
  ! grep -Fxq "com.greeneye.intellij.theme" "$CONFIG_DIR/disabled_plugins.txt" &&
  pass "脏状态清理" || fail "脏状态清理"

before="$(snapshot)"
run_installer --dry-run --yes >/dev/null
[ "$before" = "$(snapshot)" ] && pass "dry-run" || fail "dry-run"

run_installer --yes --icls-only >/dev/null
[ -z "$(find "$CONFIG_DIR/plugins" -mindepth 1 -maxdepth 1 -print -quit)" ] &&
  [ "$(find "$CONFIG_DIR/colors" -type f -name '*.icls' | wc -l | tr -d ' ')" = "2" ] &&
  pass "插件/配色模式互斥" || fail "插件/配色模式互斥"

run_installer --yes --uninstall >/dev/null
[ -z "$(find "$CONFIG_DIR/plugins" -mindepth 1 -maxdepth 1 -print -quit)" ] &&
  [ -z "$(find "$CONFIG_DIR/colors" -type f -name '*.icls' -print -quit)" ] &&
  pass "卸载完整" || fail "卸载"

echo "安装器测试全部通过。"
