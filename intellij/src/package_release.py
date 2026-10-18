#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
打发布包（A 方案）：一个 zip，用户不需要 Python / bash / make。

单平台包（默认，IntelliJ）：
    green-eye-<version>/
    ├── GreenEye-Theme-<version>.jar
    ├── Green-Eye-Dark.icls
    ├── Green-Eye-Mineral.icls
    ├── INSTALL.txt
    ├── THIRD_PARTY_NOTICES.md
    ├── LICENSE（存在时）
    └── SHA256SUMS

--all 会额外把 VS Code .vsix 放进来：
    green-eye-<version>/
    ├── intellij/...
    ├── vscode/green-eye-theme-<version>.vsix
    └── INSTALL.txt / NOTICE / SHA256SUMS
"""
import argparse
import hashlib
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
INTELLIJ = HERE.parent
ROOT = INTELLIJ.parent
DIST = INTELLIJ / "dist"
THEMES = INTELLIJ / "themes"
VSCODE_DIST = ROOT / "vscode" / "dist"

from project_config import JAR_PREFIX, VERSION  # noqa: E402

INSTALL_TEXT = """Green Eye 护眼主题 {version}

推荐安装（两款主题都包含在 jar 里，不需要 Python / bash / make）：

  1. 打开 IntelliJ IDEA
  2. Settings / Preferences -> Plugins
  3. 右上角齿轮 -> Install Plugin from Disk...
  4. 选择 GreenEye-Theme-{version}.jar
  5. 完全退出并重启 IDEA
  6. Settings -> Appearance & Behavior -> Appearance -> Theme
     选择「Green Eye Dark 松林」或「Green Eye Mineral 矿彩」

只想导入配色方案（不使用插件）：

  Settings -> Editor -> Color Scheme -> 齿轮 -> Import Scheme...
  选择 Green-Eye-Dark.icls 或 Green-Eye-Mineral.icls

卸载：

  Plugins 里卸载 Green Eye；
  或在 Color Scheme 里删除同名方案。

更多说明见项目 README。
"""

INSTALL_ALL_TEXT = """Green Eye 护眼主题 {version}（IntelliJ IDEA + VS Code）

IntelliJ IDEA：
  1. Settings / Preferences -> Plugins
  2. 齿轮 -> Install Plugin from Disk...
  3. 选择 intellij/GreenEye-Theme-{version}.jar
  4. 完全退出并重启 IDEA
  5. Settings -> Appearance & Behavior -> Appearance -> Theme
     选择「Green Eye Dark 松林」或「Green Eye Mineral 矿彩」

VS Code：
  1. Extensions -> 右上角 ... -> Install from VSIX...
  2. 选择 vscode/green-eye-theme-{version}.vsix
  3. Command Palette -> Preferences: Color Theme
     选择「Green Eye Dark 松林」或「Green Eye Mineral 矿彩」

只想给 IntelliJ 导入配色方案：
  Settings -> Editor -> Color Scheme -> 齿轮 -> Import Scheme...
  选择 intellij/Green-Eye-Dark.icls 或 Green-Eye-Mineral.icls

卸载：插件/扩展管理器里卸载即可。
更多说明见项目 README。
"""


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def _texts():
    texts = []
    for name in ("THIRD_PARTY_NOTICES.md", "LICENSE"):
        path = ROOT / name
        if path.is_file():
            texts.append((name, path.read_text(encoding="utf-8")))
    return texts


def _write(target, name, records):
    sums = ["%s  %s" % (sha256_bytes(data), arc.rsplit("/", 1)[-1])
            for arc, data in records]
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
        for arc, data in records:
            zf.writestr(arc, data)
        zf.writestr("%s/SHA256SUMS" % name, "\n".join(sums) + "\n")
    print("写入 %s（%d 字节，%d 个文件）"
          % (target, target.stat().st_size, len(records) + 1))


def _release_dir(outdir):
    release = Path(outdir).expanduser() if outdir else ROOT / "release"
    release.mkdir(parents=True, exist_ok=True)
    return release


def package(outdir=None):
    jars = sorted(DIST.glob("%s*.jar" % JAR_PREFIX))
    if not jars:
        print("缺少 dist/%s*.jar；先运行 build。" % JAR_PREFIX, file=sys.stderr)
        return 1
    icls = sorted(THEMES.glob("Green-Eye-*.icls"))
    if len(icls) < 2:
        print("缺少 themes/Green-Eye-*.icls；先运行 build。", file=sys.stderr)
        return 1
    jar = jars[-1]
    name = "green-eye-%s" % VERSION
    records = [("%s/%s" % (name, src.name), src.read_bytes())
               for src in [jar] + icls]
    records.append(("%s/INSTALL.txt" % name,
                    INSTALL_TEXT.format(version=VERSION).encode("utf-8")))
    for filename, text in _texts():
        records.append(("%s/%s" % (name, filename), text.encode("utf-8")))
    _write(_release_dir(outdir) / ("%s.zip" % name), name, records)
    return 0


def package_all(outdir=None):
    jars = sorted(DIST.glob("%s*.jar" % JAR_PREFIX))
    icls = sorted(THEMES.glob("Green-Eye-*.icls"))
    vsix = VSCODE_DIST / ("green-eye-theme-%s.vsix" % VERSION)
    if not jars or len(icls) < 2:
        print("缺少 IntelliJ 产物；先运行 build。", file=sys.stderr)
        return 1
    if not vsix.is_file():
        print("缺少 %s；先运行 green_eye.py vscode。" % vsix, file=sys.stderr)
        return 1
    name = "green-eye-%s" % VERSION
    records = []
    records.append(("%s/intellij/%s" % (name, jars[-1].name),
                    jars[-1].read_bytes()))
    for source in icls:
        records.append(("%s/intellij/%s" % (name, source.name),
                        source.read_bytes()))
    records.append(("%s/vscode/%s" % (name, vsix.name), vsix.read_bytes()))
    records.append(("%s/INSTALL.txt" % name,
                    INSTALL_ALL_TEXT.format(version=VERSION).encode("utf-8")))
    for filename, text in _texts():
        records.append(("%s/%s" % (name, filename), text.encode("utf-8")))
    _write(_release_dir(outdir) / ("%s-all.zip" % name), name, records)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="打发布包")
    ap.add_argument("--outdir")
    ap.add_argument("--all", action="store_true",
                    help="同时包含 VS Code .vsix")
    args = ap.parse_args(argv)
    return package_all(args.outdir) if args.all else package(args.outdir)


if __name__ == "__main__":
    sys.exit(main())
