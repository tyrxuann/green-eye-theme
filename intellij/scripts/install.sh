#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INTELLIJ_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
DIST_DIR="$INTELLIJ_DIR/dist"
THEMES_DIR="$INTELLIJ_DIR/themes"

PLUGIN_ID="com.greeneye.intellij.theme"
SCHEME_NAMES=("Green Eye Dark" "Green Eye Mineral")
MODE="plugin"
ACTION="install"
ASSUME_YES=0
DRY_RUN=0
ALL_CONFIGS=0
CONFIG_DIR=""

usage() {
  cat <<'EOF'
用法:
  bash intellij/scripts/install.sh [选项]

选项:
  --uninstall             卸载插件、手工配色副本和禁用记录
  --icls-only             只安装 .icls 配色方案
  --config-dir PATH       指定 IntelliJ 配置目录
  --all                   处理 JetBrains 根目录下全部 IntelliJIdea* 配置
  --yes, -y               不询问
  --dry-run, -n           只显示计划
  --help, -h              显示帮助
EOF
}

die() {
  echo "错误: $*" >&2
  exit 1
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --uninstall) ACTION="uninstall" ;;
    --icls-only) MODE="icls" ;;
    --config-dir)
      [ "$#" -ge 2 ] || die "--config-dir 需要路径"
      CONFIG_DIR="$2"
      shift
      ;;
    --all) ALL_CONFIGS=1 ;;
    --yes|-y) ASSUME_YES=1 ;;
    --dry-run|-n) DRY_RUN=1 ;;
    --help|-h) usage; exit 0 ;;
    *) die "未知参数: $1" ;;
  esac
  shift
done

[ "$ACTION" = "uninstall" ] && [ "$MODE" = "plugin" ] || \
  [ "$ACTION" = "install" ] || die "--uninstall 不能与 --icls-only 组合"
[ -z "$CONFIG_DIR" ] || [ "$ALL_CONFIGS" -eq 0 ] || \
  die "--config-dir 与 --all 不能同时使用"

find_artifact() {
  local candidate=""
  for path in "$DIST_DIR"/GreenEye-Theme-*.jar; do
    [ -f "$path" ] || continue
    candidate="$path"
  done
  [ -n "$candidate" ] && printf '%s\n' "$candidate"
}

ARTIFACT="$(find_artifact || true)"
if [ "$ACTION" = "install" ] && [ "$MODE" = "plugin" ]; then
  [ -n "$ARTIFACT" ] || die "dist/ 下没有插件包，请先运行 make build"
fi
JAR_NAME="${ARTIFACT##*/}"

jetbrains_root() {
  case "$(uname -s)" in
    Darwin) printf '%s\n' "$HOME/Library/Application Support/JetBrains" ;;
    Linux) printf '%s\n' "${XDG_CONFIG_HOME:-$HOME/.config}/JetBrains" ;;
    MINGW*|MSYS*|CYGWIN*)
      [ -n "${APPDATA:-}" ] || die "Windows 环境缺少 APPDATA"
      printf '%s\n' "$APPDATA/JetBrains"
      ;;
    *) die "不支持的操作系统: $(uname -s)" ;;
  esac
}

discover_targets() {
  local root="$1" latest="" path
  TARGETS=()
  if [ -n "$CONFIG_DIR" ]; then
    [ -d "$CONFIG_DIR" ] || die "配置目录不存在: $CONFIG_DIR"
    TARGETS+=("$CONFIG_DIR")
    return
  fi
  [ -d "$root" ] || die "找不到 JetBrains 配置根目录: $root"
  for path in "$root"/IntelliJIdea*; do
    [ -d "$path" ] || continue
    if [ "$ALL_CONFIGS" -eq 1 ]; then
      TARGETS+=("$path")
    elif [ -z "$latest" ] || [ "$(basename "$path")" \> "$(basename "$latest")" ]; then
      latest="$path"
    fi
  done
  if [ "$ALL_CONFIGS" -eq 0 ] && [ -n "$latest" ]; then
    TARGETS+=("$latest")
  fi
  [ "${#TARGETS[@]}" -gt 0 ] || die "没有找到 IntelliJIdea* 配置目录"
}

is_our_jar() {
  unzip -p "$1" META-INF/plugin.xml 2>/dev/null |
    grep -Fq "<id>$PLUGIN_ID</id>"
}

is_our_plugin_dir() {
  [ -f "$1/META-INF/plugin.xml" ] &&
    grep -Fq "<id>$PLUGIN_ID</id>" "$1/META-INF/plugin.xml"
}

is_our_icls() {
  local name
  for name in "${SCHEME_NAMES[@]}"; do
    grep -Fq "<scheme name=\"$name\"" "$1" 2>/dev/null && return 0
  done
  return 1
}

PLAN=()
SKIPPED=0
plan() {
  PLAN+=("$1"$'\t'"$2"$'\t'"$3")
}

plan_sync() {
  local source="$1" target="$2" reason="$3"
  if [ -f "$target" ] && cmp -s "$source" "$target"; then
    SKIPPED=$((SKIPPED + 1))
  elif [ -f "$target" ]; then
    plan CP "$source|$target" "$reason"
  else
    plan CP "$source|$target" "新增"
  fi
}

discover_targets "$(jetbrains_root)"

for config in "${TARGETS[@]}"; do
  colors_dir="$config/colors"
  plugins_dir="$config/plugins"
  disabled_file="$config/disabled_plugins.txt"

  if [ "$ACTION" = "uninstall" ] || [ "$MODE" = "icls" ]; then
    for jar in "$plugins_dir"/*.jar; do
      [ -f "$jar" ] && is_our_jar "$jar" &&
        plan DEL "$jar" "移除插件"
    done
    for plugin_dir in "$plugins_dir"/*; do
      [ -d "$plugin_dir" ] && is_our_plugin_dir "$plugin_dir" &&
        plan DEL "$plugin_dir" "移除解压形态插件"
    done
  else
    for jar in "$plugins_dir"/*.jar; do
      [ -f "$jar" ] || continue
      is_our_jar "$jar" || continue
      [ "$(basename "$jar")" = "$JAR_NAME" ] ||
        plan DEL "$jar" "移除旧版本插件"
    done
    for plugin_dir in "$plugins_dir"/*; do
      [ -d "$plugin_dir" ] && is_our_plugin_dir "$plugin_dir" &&
        plan DEL "$plugin_dir" "移除解压形态插件"
    done
  fi

  if [ "$ACTION" = "uninstall" ] || [ "$MODE" = "plugin" ]; then
    for icls in "$colors_dir"/*.icls; do
      [ -f "$icls" ] && is_our_icls "$icls" &&
        plan DEL "$icls" "移除同名手工配色副本"
    done
  fi

  if [ "$ACTION" = "install" ]; then
    if [ "$MODE" = "plugin" ]; then
      plan_sync "$ARTIFACT" "$plugins_dir/$JAR_NAME" "安装插件"
    else
      for source in "$THEMES_DIR"/Green-Eye-*.icls; do
        [ -f "$source" ] || die "缺少配色方案: $source"
        plan_sync "$source" "$colors_dir/$(basename "$source")" "安装配色方案"
      done
    fi
    if [ -f "$disabled_file" ] && grep -Fqx "$PLUGIN_ID" "$disabled_file"; then
      plan EDIT "$disabled_file" "移除禁用记录"
    fi
  fi
done

echo "Green Eye IntelliJ · $ACTION/$MODE · ${#TARGETS[@]} 个配置目录"
for target in "${TARGETS[@]}"; do echo "  $target"; done

if [ "${#PLAN[@]}" -eq 0 ]; then
  echo "无需改动（幂等）${SKIPPED:+；$SKIPPED 个文件内容一致}。"
  exit 0
fi

echo "计划:"
for item in "${PLAN[@]}"; do
  IFS=$'\t' read -r kind path reason <<< "$item"
  case "$kind" in
    CP) echo "  $reason: ${path#*|}" ;;
    EDIT|DEL) echo "  $kind: $path ($reason)" ;;
  esac
done

[ "$DRY_RUN" -eq 1 ] && { echo "dry-run：未修改文件。"; exit 0; }

if [ "$ASSUME_YES" -eq 0 ]; then
  [ -t 0 ] || die "非交互环境必须使用 --yes"
  read -r -p "继续？[y/N] " answer
  case "$answer" in
    y|Y|yes|YES) ;;
    *) echo "已取消。"; exit 0 ;;
  esac
fi

copy_atomic() {
  local pair="$1"
  local source="${pair%%|*}" target="${pair#*|}"
  local temp="${target}.tmp.$$"
  mkdir -p "$(dirname "$target")"
  cp -p "$source" "$temp"
  mv -f "$temp" "$target"
}

edit_disabled() {
  local file="$1"
  local temp="${file}.tmp.$$"
  awk -v plugin_id="$PLUGIN_ID" '$0 != plugin_id { print }' "$file" > "$temp"
  mv -f "$temp" "$file"
}

# Replacements first; stale variants are removed only after desired files exist.
for kind in CP EDIT DEL; do
  for item in "${PLAN[@]}"; do
    IFS=$'\t' read -r action path reason <<< "$item"
    [ "$action" = "$kind" ] || continue
    case "$kind" in
      CP) copy_atomic "$path" ;;
      EDIT) edit_disabled "$path" ;;
      DEL) rm -rf "$path" ;;
    esac
  done
done

echo "完成。请完全退出并重启 IntelliJ IDEA。"
