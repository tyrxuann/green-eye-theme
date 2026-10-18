#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
严格校验 .icls 里的键名是否真实存在于本机 IntelliJ IDEA 中。

与 validate_names.py 的区别：直接在解压后的字节流上用"名字全集的交替正则"做
精确匹配，不再依赖"可打印字符串切分"，因此不会因为 class 常量池里相邻字节
粘连而漏检。

用法:
    python3 validate_names2.py <file.icls> [more.icls ...]
"""
import os
import re
import sys
import time
import zipfile
import xml.etree.ElementTree as ET
from collections import OrderedDict

IDE = "/Applications/IntelliJ IDEA.app/Contents"
SKIP_EXT = {".png", ".svg", ".gif", ".jpg", ".jpeg", ".ico", ".icns", ".ttf",
            ".otf", ".woff", ".woff2", ".so", ".dylib", ".dll", ".jnilib",
            ".zip", ".jar", ".wav", ".mp3", ".pdf", ".bin", ".dat", ".exe",
            ".mp4", ".webp", ".bmp", ".jar.", ".png."}


def collect_keys(paths):
    keys = OrderedDict()
    for path in paths:
        root = ET.parse(path).getroot()
        for section in ("colors", "attributes"):
            node = root.find(section)
            if node is None:
                continue
            for opt in node.findall("option"):
                name = opt.get("name")
                if name:
                    keys.setdefault(name, set()).add(section)
    return keys


def jar_list(scope="all"):
    out = []
    if scope == "lib":
        import glob
        return sorted(glob.glob(os.path.join(IDE, "lib", "*.jar")))
    for base, _, files in os.walk(IDE):
        if "/jbr/" in base or "/help/" in base or "/license/" in base:
            continue
        for f in files:
            if f.endswith(".jar"):
                out.append(os.path.join(base, f))
    return sorted(out)


def main():
    paths = [p for p in sys.argv[1:] if p.endswith(".icls")]
    if not paths:
        print(__doc__)
        return 2
    keys = collect_keys(paths)
    names = sorted(keys, key=len, reverse=True)
    pat = re.compile(b"|".join(re.escape(n.encode()) for n in names))
    scope = "lib" if "--lib-only" in sys.argv else "all"
    jars = jar_list(scope)
    print("待校验键名 %d 个；范围 %s；扫描 %d 个 jar" % (len(keys), scope, len(jars)))
    found, scanned_bytes = set(), 0
    t0 = time.time()
    for i, jar in enumerate(jars, 1):
        try:
            zf = zipfile.ZipFile(jar)
        except Exception:
            continue
        with zf:
            for info in zf.infolist():
                ext = os.path.splitext(info.filename)[1].lower()
                if ext in SKIP_EXT or info.file_size > 12 << 20:
                    continue
                try:
                    data = zf.read(info)
                except Exception:
                    continue
                scanned_bytes += len(data)
                if not data:
                    continue
                for m in pat.finditer(data):
                    found.add(m.group().decode("utf-8", "ignore"))
        if i % 10 == 0 or i == len(jars):
            print("  ... %d/%d jar  %.0f MB  %.0fs  命中 %d/%d"
                  % (i, len(jars), scanned_bytes / 1e6, time.time() - t0,
                     len(found), len(keys)), flush=True)
        if len(found) == len(keys):
            break

    missing = sorted(set(keys) - found)
    print("\n扫描完成：%.0f MB, %.0fs" % (scanned_bytes / 1e6, time.time() - t0))
    print("命中 %d / %d；未命中 %d" % (len(found), len(keys), len(missing)))
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "..", "build", "ref", "name_validation.txt"),
              "w", encoding="utf-8") as fh:
        fh.write("命中 %d / %d\n\n未命中（IDE 中不存在该字面量）:\n"
                 % (len(found), len(keys)))
        for m in missing:
            fh.write("  %-60s [%s]\n" % (m, "+".join(sorted(keys[m]))))
        fh.write("\n全部键名:\n")
        for k in sorted(keys):
            fh.write("  %-60s %s\n"
                     % (k, "OK" if k in found else "MISSING"))
    if missing:
        print("\n未命中清单（已写入 build/ref/name_validation.txt）:")
        for m in missing:
            print("  - %-58s [%s]" % (m, "+".join(sorted(keys[m]))))
    else:
        print("全部键名均真实存在 ✅")
    return 0


if __name__ == "__main__":
    sys.exit(main())
