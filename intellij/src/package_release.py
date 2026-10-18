#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
打发布包（A 方案）：一个 zip，用户不需要 Python / bash / make。

包内容：
    green-eye-<version>/
    ├── GreenEye-Theme-<version>.jar   插件（两款主题都在里面）
    ├── Green-Eye-Dark.icls            可选：只导入配色方案
    ├── Green-Eye-Mineral.icls
    ├── INSTALL.txt                    三步安装说明
    └── SHA256SUMS
"""
import hashlib
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
INTELLIJ = HERE.parent
ROOT = INTELLIJ.parent
DIST = INTELLIJ / "dist"
THEMES = INTELLIJ / "themes"

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


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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
    release = Path(outdir).expanduser() if outdir else ROOT / "release"
    release.mkdir(parents=True, exist_ok=True)
    name = "green-eye-%s" % VERSION
    target = release / ("%s.zip" % name)
    install_text = INSTALL_TEXT.format(version=VERSION)

    members = [(jar, "%s/%s" % (name, jar.name))]
    members += [(p, "%s/%s" % (name, p.name)) for p in icls]
    sums = ["%s  %s" % (sha256(src), arc.split("/")[-1]) for src, arc in members]
    sums_text = "\n".join(sums) + "\n"

    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
        for src, arc in members:
            zf.write(str(src), arc)
        zf.writestr("%s/INSTALL.txt" % name, install_text)
        zf.writestr("%s/SHA256SUMS" % name, sums_text)

    print("写入 %s（%d 字节，%d 个文件）"
          % (target, target.stat().st_size, len(members) + 2))
    return 0


if __name__ == "__main__":
    sys.exit(package())
