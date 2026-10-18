#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从本机 IntelliJ IDEA 安装包里采集配色键，共两个来源：

来源一（插件语言片段）：各语言插件的 `colorSchemes/*.xml`（<list> 根节点），
    例如 Kotlin/Groovy/SQL/YAML/Markdown/Mermaid/Docker/Angular/Sass 等。

来源二（官方内置方案，最权威）：安装包里所有 plugin.xml 中
    `<bundledColorScheme id="..." path="..."/>` 指向的方案文件。
    这些是 JetBrains 自己随 IDE 发布的方案（Islands Dark / Light / High contrast …），
    键名 100% 有效，是覆盖率最高、歧义最少的一手依据。
    采集到的原文会导出到 build/ref/ide_official_schemes/ 便于人工核对。

输出:
    build/ref/ide_language_attribute_names.txt   来自语言插件的属性键
    build/ref/ide_chrome_names.txt               来自语言插件的界面颜色键
    build/ref/ide_official_attribute_names.txt   官方内置方案的属性键
    build/ref/ide_official_chrome_names.txt      官方内置方案的界面颜色键
    build/ref/ide_language_report.txt            明细
"""
import os
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from collections import OrderedDict

IDE = "/Applications/IntelliJ IDEA.app/Contents"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "build", "ref")
# 官方确实使用带空格的可读键名（如 "Unresolved reference access"），
# 早先我按"不允许空白"过滤，导致这类键从未进过清单 —— 这是个真漏洞。
OK_NAME = re.compile(r"^[^<>\"&]{1,80}$")
FRAGMENT = re.compile(r"colorSchemes/([^/]+)\.xml$")


def jars():
    for base, _, files in os.walk(IDE):
        if "/jbr/" in base or "/help/" in base:
            continue
        for f in files:
            if f.endswith(".jar"):
                yield os.path.join(base, f)


def keys_of(root):
    """从 <list> 或 <scheme> 根节点里取 (属性键, 界面颜色键)。"""
    attrs, chrome = [], []
    if root.tag == "list":
        for o in root.findall("option"):
            if o.get("name"):
                attrs.append(o.get("name"))
    for node in root.iter():
        if node.tag == "attributes":
            attrs += [o.get("name") for o in node.findall("option") if o.get("name")]
        elif node.tag == "colors":
            chrome += [o.get("name") for o in node.findall("option") if o.get("name")]
    return attrs, chrome


def harvest_fragments():
    attrs, chrome, report = OrderedDict(), OrderedDict(), []
    for jar in jars():
        try:
            zf = zipfile.ZipFile(jar)
        except Exception:
            continue
        with zf:
            for info in zf.infolist():
                m = FRAGMENT.search(info.filename)
                if not m:
                    continue
                try:
                    root = ET.fromstring(zf.read(info))
                except Exception as exc:
                    report.append("%-44s 解析失败 %s" % (info.filename, exc))
                    continue
                a, c = keys_of(root)
                a = [k for k in a if OK_NAME.match(k)]
                c = [k for k in c if OK_NAME.match(k)]
                for k in a:
                    attrs.setdefault(k, set()).add(m.group(1))
                for k in c:
                    chrome.setdefault(k, set()).add(m.group(1))
                report.append("%-58s 属性 %3d  颜色 %2d"
                              % (info.filename, len(set(a)), len(set(c))))
    return attrs, chrome, report


def harvest_official(export_dir):
    """从 <bundledColorScheme path="..."/> 找到官方方案文件并采集。"""
    attrs, chrome, report = OrderedDict(), OrderedDict(), []
    paths = OrderedDict()          # 资源路径 -> 所在 jar
    for jar in jars():
        try:
            zf = zipfile.ZipFile(jar)
        except Exception:
            continue
        with zf:
            for info in zf.infolist():
                if not info.filename.endswith("META-INF/plugin.xml"):
                    continue
                try:
                    root = ET.fromstring(zf.read(info))
                except Exception:
                    continue
                for tag in ("bundledColorScheme", "themeProvider"):
                    for ep in root.iter(tag):
                        p = ep.get("path")
                        if p and p.endswith(".xml"):
                            paths.setdefault(p.lstrip("/"), jar)

    all_jars = list(jars())
    os.makedirs(export_dir, exist_ok=True)
    for path, jar in paths.items():
        # 声明 <bundledColorScheme> 的 jar 与文件实际所在的 jar 可能不同
        # （声明在 Ultimate 定制包里，文件在平台包里），所以要回退到全盘查找。
        data = None
        for candidate in [jar] + [j for j in all_jars if j != jar]:
            try:
                with zipfile.ZipFile(candidate) as zf:
                    data = zf.read(path)
                break
            except Exception:
                continue
        if data is None:
            report.append("%-52s 读取失败（全盘未找到该资源）" % path)
            continue
        with open(os.path.join(export_dir, os.path.basename(path)), "wb") as fh:
            fh.write(data)
        try:
            root = ET.fromstring(data)
        except Exception as exc:
            report.append("%-52s 解析失败 %s" % (path, exc))
            continue
        a, c = keys_of(root)
        a = [k for k in a if OK_NAME.match(k)]
        c = [k for k in c if OK_NAME.match(k)]
        for k in a:
            attrs.setdefault(k, set()).add(root.get("name") or path)
        for k in c:
            chrome.setdefault(k, set()).add(root.get("name") or path)
        report.append("%-52s 属性 %3d  颜色 %2d  (父=%s)"
                      % (path, len(set(a)), len(set(c)), root.get("parent_scheme")))
    return attrs, chrome, report


def dump(path, keys):
    with open(path, "w", encoding="utf-8") as fh:
        for k in sorted(keys):
            fh.write(k + "\n")


def main():
    os.makedirs(OUT, exist_ok=True)
    a1, c1, r1 = harvest_fragments()
    a2, c2, r2 = harvest_official(os.path.join(OUT, "ide_official_schemes"))
    dump(os.path.join(OUT, "ide_language_attribute_names.txt"), a1)
    dump(os.path.join(OUT, "ide_chrome_names.txt"), c1)
    dump(os.path.join(OUT, "ide_official_attribute_names.txt"), a2)
    dump(os.path.join(OUT, "ide_official_chrome_names.txt"), c2)

    with open(os.path.join(OUT, "ide_language_report.txt"), "w",
              encoding="utf-8") as fh:
        fh.write("=== 来源一：语言插件的 colorSchemes 片段 ===\n")
        fh.write("\n".join(sorted(r1)) + "\n")
        fh.write("\n=== 来源二：官方 <bundledColorScheme> 指向的方案 ===\n")
        fh.write("\n".join(sorted(r2)) + "\n")
        for title, d in (("来源一 属性键", a1), ("来源一 颜色键", c1),
                         ("来源二 属性键", a2), ("来源二 颜色键", c2)):
            fh.write("\n=== %s -> 出处 ===\n" % title)
            for k in sorted(d):
                fh.write("  %-56s %s\n" % (k, ", ".join(sorted(d[k]))))

    print("来源一 语言插件片段 : 属性键 %3d  界面色键 %2d" % (len(a1), len(c1)))
    print("来源二 官方内置方案 : 属性键 %3d  界面色键 %2d" % (len(a2), len(c2)))
    print("来源文件 %d 个（片段）+ %d 个（官方方案）" % (len(r1), len(r2)))
    print("\n官方方案的父方案（判断该用哪个父方案的一手依据）:")
    for line in sorted(r2):
        if "父=" in line:
            print("   ", line)


if __name__ == "__main__":
    sys.exit(main())
