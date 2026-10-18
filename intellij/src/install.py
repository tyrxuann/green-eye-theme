#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
跨平台安装器（替代 intellij/scripts/install.sh）。

为什么用 Python 重写：
  · Windows 原生没有 bash；旧脚本要求 Git Bash / WSL；
  · 旧脚本依赖 unzip / grep / cmp / awk 等外部命令；
  · 读 jar 只需要标准库 zipfile，复制/原子替换用 shutil + os.replace。

行为与旧脚本保持一致：
  · plugin 模式：把 jar 复制到 <config>/plugins/，清理旧版本与解压形态；
  · --icls-only：只复制两款 .icls 到 <config>/colors/；
  · --uninstall：移除插件、手工配色副本与 disabled_plugins.txt 里的本插件记录；
  · --dry-run：只打印计划；--yes：非交互确认；
  · 幂等：内容相同则跳过，不修改 mtime；
  · 替换先写临时文件再 os.replace，旧版本最后清理。
"""
import argparse
import filecmp
import os
import shutil
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
INTELLIJ = HERE.parent
DIST = INTELLIJ / "dist"
THEMES = INTELLIJ / "themes"

from project_config import JAR_PREFIX, PLUGIN_ID  # noqa: E402

SCHEME_NAMES = ("Green Eye Dark", "Green Eye Mineral")


class InstallError(Exception):
    """可预期的安装错误（打印成一行中文，不抛栈）。"""


@dataclass
class Action:
    kind: str                 # CP / EDIT / DEL
    path: Path
    reason: str
    source: Path = None


class Plan:
    def __init__(self):
        self.actions = []
        self.skipped = 0

    def sync(self, source, target, reason):
        if target.is_file() and filecmp.cmp(str(source), str(target), shallow=False):
            self.skipped += 1
        else:
            self.actions.append(Action("CP", target, reason, source))

    def delete(self, path, reason):
        self.actions.append(Action("DEL", path, reason))

    def edit(self, path, reason):
        self.actions.append(Action("EDIT", path, reason))


def find_artifact():
    jars = sorted(DIST.glob("%s*.jar" % JAR_PREFIX))
    return jars[-1] if jars else None


def jetbrains_root():
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "JetBrains"
    if os.name == "nt":
        appdata = os.environ.get("APPDATA")
        if not appdata:
            raise InstallError("Windows 环境缺少 APPDATA")
        return Path(appdata) / "JetBrains"
    xdg = os.environ.get("XDG_CONFIG_HOME")
    return (Path(xdg) if xdg else Path.home() / ".config") / "JetBrains"


def discover_targets(root, config_dir, all_configs):
    if config_dir:
        path = Path(config_dir).expanduser()
        if not path.is_dir():
            raise InstallError("配置目录不存在: %s" % path)
        return [path]
    if not root.is_dir():
        raise InstallError("找不到 JetBrains 配置根目录: %s" % root)
    dirs = sorted(p for p in root.glob("IntelliJIdea*") if p.is_dir())
    if all_configs:
        return dirs
    return dirs[-1:] if dirs else []


def is_our_jar(path):
    try:
        with zipfile.ZipFile(path) as zf:
            xml = zf.read("META-INF/plugin.xml").decode("utf-8", "replace")
    except (OSError, KeyError, zipfile.BadZipFile):
        return False
    return "<id>%s</id>" % PLUGIN_ID in xml


def is_our_plugin_dir(path):
    manifest = path / "META-INF" / "plugin.xml"
    if not manifest.is_file():
        return False
    return "<id>%s</id>" % PLUGIN_ID in manifest.read_text(
        encoding="utf-8", errors="replace")


def is_our_icls(path):
    text = path.read_text(encoding="utf-8", errors="replace")
    return any('<scheme name="%s"' % name in text for name in SCHEME_NAMES)


def disabled_has_plugin(path):
    if not path.is_file():
        return False
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return PLUGIN_ID in lines


def copy_atomic(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_name(target.name + ".tmp.%d" % os.getpid())
    try:
        shutil.copy2(str(source), str(temp))
        os.replace(str(temp), str(target))
    finally:
        if temp.exists():
            temp.unlink()


def edit_disabled(path):
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    kept = [line for line in lines if line.rstrip("\r\n") != PLUGIN_ID]
    if len(kept) == len(lines):
        return
    temp = path.with_name(path.name + ".tmp.%d" % os.getpid())
    temp.write_text("".join(kept), encoding="utf-8")
    os.replace(str(temp), str(path))


def build_plan(configs, action, mode, artifact):
    plan = Plan()
    jar_name = artifact.name if artifact else ""
    for config in configs:
        colors_dir = config / "colors"
        plugins_dir = config / "plugins"
        disabled_file = config / "disabled_plugins.txt"

        remove_plugin = action == "uninstall" or mode == "icls"
        if remove_plugin:
            for jar in sorted(plugins_dir.glob("*.jar")):
                if is_our_jar(jar):
                    plan.delete(jar, "移除插件")
        else:
            for jar in sorted(plugins_dir.glob("*.jar")):
                if is_our_jar(jar) and jar.name != jar_name:
                    plan.delete(jar, "移除旧版本插件")
        for plugin_dir in sorted(p for p in plugins_dir.glob("*") if p.is_dir()):
            if is_our_plugin_dir(plugin_dir):
                plan.delete(plugin_dir, "移除解压形态插件")

        if action == "uninstall" or mode == "plugin":
            for icls in sorted(colors_dir.glob("*.icls")):
                if is_our_icls(icls):
                    plan.delete(icls, "移除同名手工配色副本")

        if action == "install":
            if mode == "plugin":
                if artifact is None:
                    raise InstallError("dist/ 下没有插件包，请先运行 build")
                plan.sync(artifact, plugins_dir / jar_name, "安装插件")
            else:
                sources = sorted(THEMES.glob("Green-Eye-*.icls"))
                if not sources:
                    raise InstallError("缺少配色方案，请先运行 build")
                for source in sources:
                    plan.sync(source, colors_dir / source.name, "安装配色方案")
            if disabled_has_plugin(disabled_file):
                plan.edit(disabled_file, "移除禁用记录")
    return plan


def execute(plan):
    # 替换/编辑先做，旧形态最后删：任何一步失败都不会先把可用的文件删掉。
    for wanted in ("CP", "EDIT", "DEL"):
        for item in plan.actions:
            if item.kind != wanted:
                continue
            if item.kind == "CP":
                copy_atomic(item.source, item.path)
            elif item.kind == "EDIT":
                edit_disabled(item.path)
            else:
                if item.path.is_dir():
                    shutil.rmtree(str(item.path))
                elif item.path.exists():
                    item.path.unlink()


def run(uninstall=False, icls_only=False, config_dir=None, all_configs=False,
        assume_yes=False, dry_run=False):
    if uninstall and icls_only:
        raise InstallError("--uninstall 不能与 --icls-only 组合")
    if config_dir and all_configs:
        raise InstallError("--config-dir 与 --all 不能同时使用")

    action = "uninstall" if uninstall else "install"
    mode = "icls" if icls_only else "plugin"
    artifact = find_artifact()
    if action == "install" and mode == "plugin" and artifact is None:
        raise InstallError("dist/ 下没有插件包，请先运行 build")

    configs = discover_targets(jetbrains_root(), config_dir, all_configs)
    if not configs:
        raise InstallError("没有找到 IntelliJIdea* 配置目录")

    plan = build_plan(configs, action, mode, artifact)
    print("Green Eye IntelliJ · %s/%s · %d 个配置目录"
          % (action, mode, len(configs)))
    for config in configs:
        print("  %s" % config)
    if not plan.actions:
        extra = "；%d 个文件内容一致" % plan.skipped if plan.skipped else ""
        print("无需改动（幂等）%s。" % extra)
        return 0

    print("计划:")
    for item in plan.actions:
        if item.kind == "CP":
            print("  %s: %s" % (item.reason, item.path))
        else:
            print("  %s: %s (%s)" % (item.kind, item.path, item.reason))

    if dry_run:
        print("dry-run：未修改文件。")
        return 0
    if not assume_yes:
        if not sys.stdin.isatty():
            raise InstallError("非交互环境必须使用 --yes")
        answer = input("继续？[y/N] ")
        if answer.strip().lower() not in ("y", "yes"):
            print("已取消。")
            return 0

    execute(plan)
    print("完成。请完全退出并重启 IntelliJ IDEA。")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="green_eye.py install",
        description="把 Green Eye 主题安装到 IntelliJ IDEA 配置目录")
    ap.add_argument("--uninstall", action="store_true",
                    help="卸载插件、手工配色副本和禁用记录")
    ap.add_argument("--icls-only", action="store_true",
                    help="只安装 .icls 配色方案，不装插件")
    ap.add_argument("--config-dir", help="指定 IntelliJ 配置目录")
    ap.add_argument("--all", action="store_true",
                    help="处理 JetBrains 根目录下全部 IntelliJIdea* 配置")
    ap.add_argument("--yes", "-y", action="store_true", help="不询问")
    ap.add_argument("--dry-run", "-n", action="store_true",
                    help="只显示计划，不修改文件")
    args = ap.parse_args(argv)
    try:
        return run(uninstall=args.uninstall, icls_only=args.icls_only,
                   config_dir=args.config_dir, all_configs=args.all,
                   assume_yes=args.yes, dry_run=args.dry_run)
    except InstallError as exc:
        print("错误: %s" % exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
