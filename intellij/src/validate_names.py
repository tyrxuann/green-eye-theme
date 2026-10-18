#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
校验 .icls 里用到的每一个键名是否真实存在于本机 IntelliJ IDEA 中。

原理：IntelliJ 的 TextAttributesKey / EditorColors 外部名会以字符串常量形式
编译进 class 文件，因此只要在 IDE 安装包的 class 常量池里能找到该字面量，
就说明该键名有效（反之几乎可以确定是拼错的无效键）。

用法:
    python3 validate_names.py ../themes/Green-Eye-Dark.icls
"""
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from collections import OrderedDict

IDE = "/Applications/IntelliJ IDEA.app/Contents"
SKIP_EXT = {".png", ".svg", ".gif", ".jpg", ".jpeg", ".ico", ".icns", ".ttf",
            ".otf", ".woff", ".woff2", ".so", ".dylib", ".dll", ".jnilib",
            ".zip", ".jar", ".wav", ".mp3", ".pdf", ".bin", ".dat", ".exe"}
# 一个可打印 ASCII 串（class 常量池里的 UTF8 常量）
RUN = re.compile(rb"[\x21-\x7e]{3,80}")


def collect_keys(paths):
    keys = OrderedDict()
    for path in paths:
        tree = ET.parse(path)
        root = tree.getroot()
        for section in ("colors", "attributes"):
            node = root.find(section)
            if node is None:
                continue
            for opt in node.findall("option"):
                name = opt.get("name")
                if name:
                    keys.setdefault(name, set()).add(section)
    return keys


def jar_list():
    out = []
    for base, _, files in os.walk(IDE):
        if "/jbr/" in base or "/help/" in base:
            continue
        for f in files:
            if f.endswith(".jar"):
                out.append(os.path.join(base, f))
    return out


def scan(jars, wanted):
    """返回找到的键集合。"""
    found = set()
    total = len(jars)
    for i, jar in enumerate(jars, 1):
        try:
            zf = zipfile.ZipFile(jar)
        except Exception:
            continue
        with zf:
            for info in zf.infolist():
                ext = os.path.splitext(info.filename)[1].lower()
                if ext in SKIP_EXT or info.file_size > 8 << 20:
                    continue
                try:
                    data = zf.read(info)
                except Exception:
                    continue
                for m in RUN.finditer(data):
                    tok = m.group().decode("ascii", "ignore")
                    if tok in wanted:
                        found.add(tok)
        if i % 40 == 0 or i == total:
            print("  ... %d/%d jars, 命中 %d/%d"
                  % (i, total, len(found), len(wanted)), flush=True)
        if len(found) == len(wanted):
            break
    return found


def main():
    paths = [p for p in sys.argv[1:] if p.endswith(".icls")]
    if not paths:
        print("用法: validate_names.py <file.icls> [...]")
        return 2
    keys = collect_keys(paths)
    print("待校验键名: %d 个（attributes+colors 去重）" % len(keys))
    jars = jar_list()
    print("扫描 %d 个 jar ..." % len(jars))
    found = scan(jars, set(keys))
    missing = sorted(set(keys) - found)
    print("\n结果: 命中 %d / %d" % (len(found), len(keys)))
    if missing:
        print("\n未在 IDE 中找到的键（%d 个，通常是拼写错误或过时键名）:"
              % len(missing))
        for m in missing:
            print("  - %-58s [%s]" % (m, "+".join(sorted(keys[m]))))
    else:
        print("全部键名均真实存在 ✅")
    return 0


if __name__ == "__main__":
    sys.exit(main())
