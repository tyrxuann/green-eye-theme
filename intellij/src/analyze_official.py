#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析 JetBrains 官方内置配色方案，提炼"官方是怎么做配色的"。

数据来源：build/ref/ide_official_schemes/*.xml
    这些是安装包内 <bundledColorScheme> 指向的官方方案原文，
    即 Islands Dark / Dark / High contrast / Light / IntelliJ Light 的实际定义。

注意：这些方案都是 parent_scheme="Darcula" 或 "Default"，只写了"主题特有的覆盖项"，
      未覆盖的键继承自代码里注册的 Darcula / Default 基方案。
      所以这里分析的是"官方在基方案之上又改了什么"，同样很有信息量。
"""
import colorsys
import glob
import os
import re
import sys
from collections import Counter, defaultdict

import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(HERE, "..", "build", "ref", "ide_official_schemes")
sys.path.insert(0, HERE)
from palette import contrast, hex_to_rgb  # noqa: E402

FONT = {"0": "", "1": "粗", "2": "斜", "3": "粗斜"}
EFFECT = {"0": "下划线", "1": "波浪线", "2": "粗下划线", "3": "删除线", "4": "点线", "5": "方框"}


def hls(h):
    r, g, b = [v / 255 for v in hex_to_rgb(h)]
    H, L, S = colorsys.rgb_to_hls(r, g, b)
    return H * 360, S * 100, L * 100


def load(path):
    root = ET.parse(path).getroot()
    attrs = {}
    a = root.find("attributes")
    if a is not None:
        for o in a.findall("option"):
            val = o.find("value")
            if val is None:
                continue
            attrs[o.get("name")] = {x.get("name"): x.get("value") for x in val}
    c = root.find("colors")
    if c is not None:
        for o in c.findall("option"):
            if o.get("value"):
                attrs.setdefault("$" + o.get("name"), {"VALUE": o.get("value")})
    t = attrs.get("TEXT", {})
    bg = "#" + t.get("BACKGROUND", "2B2B2B")
    return root.get("name"), root.get("parent_scheme"), bg, attrs


def color_of(v):
    for k in ("FOREGROUND", "VALUE"):
        c = v.get(k)
        if c and re.fullmatch(r"[0-9A-Fa-f]{6}", c):
            return "#" + c
    return None


def report(name, parent, bg, attrs, limit=None):
    rows = []
    for key, v in attrs.items():
        c = color_of(v)
        if not c:
            continue
        H, S, L = hls(c)
        rows.append((key, c, H, S, L, contrast(c, bg),
                     FONT.get(v.get("FONT_TYPE", "0"), ""),
                     EFFECT.get(v.get("EFFECT_TYPE"), ""),
                     ("#" + v["BACKGROUND"]) if re.fullmatch(r"[0-9A-Fa-f]{6}", v.get("BACKGROUND") or "") else ""))
    print("=" * 108)
    print("【%s】  parent=%s  正文底色=%s   定义了 %d 个带颜色的键"
          % (name, parent, bg, len(rows)))
    txt = color_of(attrs.get("TEXT", {})) or "#000000"
    print("  TEXT 前景=%s 对比 %.2f:1" % (txt, contrast(txt, bg)))
    # 统计
    cnt = Counter(r[1] for r in rows)
    neut = [r for r in rows if r[3] < 20]
    print("  用到的不同颜色数: %d ；饱和度<20%% 的键: %d/%d"
          % (len(cnt), len(neut), len(rows)))
    fam = Counter(int(r[2] // 30) * 30 for r in rows if r[3] >= 20)
    print("  有彩色键的色相分布(每30°): %s"
          % "  ".join("%d°:%d" % (k, v) for k, v in sorted(fam.items())))
    cs = [r[5] for r in rows if r[1] != bg]
    if cs:
        cs.sort()
        print("  对比度分布: 最低 %.2f  中位 %.2f  最高 %.2f"
              % (cs[0], cs[len(cs) // 2], cs[-1]))
    print("  被多个键共用的颜色（说明官方靠少量颜色覆盖大量语义）:")
    for c, n in cnt.most_common(6):
        if n > 1:
            keys = [r[0] for r in rows if r[1] == c][:4]
            H, S, L = hls(c)
            print("     %s  用 %2d 次   H=%3.0f° S=%2.0f%% L=%2.0f%%   例: %s"
                  % (c, n, H, S, L, ", ".join(keys)))
    if limit:
        print("  --- 明细（按对比度升序，前 %d 条）---" % limit)
        for r in sorted(rows, key=lambda x: x[5])[:limit]:
            print("     %-38s %s  H=%3.0f° S=%2.0f%% L=%2.0f%%  %5.2f:1  %s%s%s"
                  % (r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7],
                     ("  bg=" + r[8]) if r[8] else ""))


def main():
    files = {
        "Islands Dark": "IslandSchemeDark.xml",
        "Dark (expUI)": "expUI_darkScheme.xml",
        "High contrast": "highContrastScheme.xml",
        "Darcula Contrast": "expUI_darculaContrastScheme.xml",
        "Light (expUI)": "expUI_lightScheme.xml",
    }
    for label, fn in files.items():
        p = os.path.join(REF, fn)
        if not os.path.exists(p):
            continue
        name, parent, bg, attrs = load(p)
        report(label, parent, bg, attrs, limit=28)


if __name__ == "__main__":
    main()
