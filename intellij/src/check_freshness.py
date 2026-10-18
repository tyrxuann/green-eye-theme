#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
产物新鲜度断言（评委建议的第二条规则）。

真实事故：我在 23:23 改了 palette.py，但 preview/ 里的裁剪图仍是 23:17 的字节，
于是评审拿旧图核新改动，三条结论一个都验不了。

规则：`preview/*.png`、`themes/*`、`dist/*.jar` 的 mtime 必须 >= 其输入
（src/*.py、build/ref/*_names.txt）的 mtime，否则 fail。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
INPUTS = [os.path.join(HERE, f) for f in os.listdir(HERE) if f.endswith(".py")]
INPUTS += [os.path.join(ROOT, "build", "ref", f)
           for f in os.listdir(os.path.join(ROOT, "build", "ref"))
           if f.endswith(".txt")]
OUTPUT_DIRS = [os.path.join(ROOT, "preview"), os.path.join(ROOT, "themes"),
               os.path.join(ROOT, "dist")]


def main():
    newest_in, newest_name = 0.0, ""
    for p in INPUTS:
        if os.path.isfile(p):
            m = os.path.getmtime(p)
            if m > newest_in:
                newest_in, newest_name = m, os.path.relpath(p, ROOT)
    stale = []
    for d in OUTPUT_DIRS:
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if f.startswith("_") or not f.endswith((".png", ".icls", ".json", ".xml", ".jar")):
                continue
            p = os.path.join(d, f)
            if os.path.getmtime(p) < newest_in - 1:
                stale.append((os.path.relpath(p, ROOT), os.path.getmtime(p)))
    print("产物新鲜度：最新输入 = %s" % newest_name)
    if stale:
        print("  ❌ 以下产物比输入旧（没有反映最新改动）：")
        for name, _ in stale:
            print("     - %s" % name)
        return 1
    print("  ✅ 所有产物都不早于最新输入")
    return 0


if __name__ == "__main__":
    sys.exit(main())
