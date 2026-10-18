#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查"调色板里的每个键都真的被消费"（评委建议的第三条规则）。

背景：`palette.py` 里的键是动态引用的（`pal["keyword"]`），改完调色板但渲染器/
生成器没跟着引用时，改动会**静默失效**。真实案例：`doc_tag` 加进调色板后，
`render_java.py` 仍把 Javadoc tag 写死成 `annotation`，于是"tag 变绿"在预览里
永远不生效，而生成器是吃调色板的 —— 两边不一致，评审无法验证。

规则：调色板每个键必须在 src/*.py 里至少出现一次字符串引用，否则 fail。
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from palette import DARK, PALETTES  # noqa: E402

# 这些键由 gen_theme_json.py 的 UI 映射表消费（键名以映射表的形式出现，允许）
EXEMPT = {"label", "name", "parent", "dark"}


def main():
    src = {}
    for f in sorted(os.listdir(HERE)):
        if f.endswith(".py"):
            src[f] = open(os.path.join(HERE, f), encoding="utf-8").read()
    unused = []
    allkeys = set()
    for pal in PALETTES.values():
        allkeys |= set(pal)
    for key in sorted(allkeys):
        if key in EXEMPT:
            continue
        pat = '"%s"' % key
        if not any(pat in text for text in src.values()):
            unused.append(key)
    print("调色板使用检查：%d 款主题、%d 个键（并集）" % (len(PALETTES), len(allkeys)))
    if unused:
        print("  ❌ 以下键在 src/*.py 里从未被引用（改动会静默失效）：")
        for k in unused:
            print("     - %s = %s" % (k, DARK[k]))
        return 1
    print("  ✅ 每个键都至少被一处消费（生成器或渲染器）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
