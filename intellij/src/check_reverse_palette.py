#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
反向覆盖检查：产物里的每个颜色，是否都来自**它自己的**调色板。

起因：`gen_icls.py` 里有几处硬编码十六进制（`grey_underline` / `followed_link` /
`implicit_ec` 的效果色），于是「矿彩」的 .icls 里混进了「松林」的颜色 ——
正向检查（调色板里的键都被消费）永远发现不了，因为问题在反方向：
**产物里出现了调色板里没有的颜色**。

规则：`themes/<scheme>.icls` 的 attributes + colors 里所有 6 位十六进制，
必须能在对应调色板的取值集合里找到（大小写不敏感）。
"""
import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from palette import PALETTES, icls_path  # noqa: E402


def colors_in(path):
    root = ET.parse(path).getroot()
    out = set()
    for o in root.iter("option"):
        v = o.get("value") or ""
        if len(v) == 6 and all(c in "0123456789abcdefABCDEF" for c in v):
            out.add("#" + v.upper())
    return out


def main():
    bad_total = 0
    for key, pal in sorted(PALETTES.items()):
        path = icls_path(pal)
        if not os.path.exists(path):
            print("缺少产物 %s" % path)
            return 1
        allowed = {v.upper() for v in pal.values() if isinstance(v, str) and v.startswith("#")}
        used = colors_in(path)
        extra = sorted(used - allowed)
        print("【%s「%s」】产物用色 %d 种，其中不在本调色板里的：%d %s"
              % (pal["name"], pal["label"], len(used), len(extra), extra or "✅"))
        for c in extra:
            owners = [p["name"] for _, p in sorted(PALETTES.items())
                      if c in {v.upper() for v in p.values() if isinstance(v, str)}]
            print("   ❌ %s 不属于本主题；它出现在：%s" % (c, owners or "任何调色板都没有（硬编码）"))
        bad_total += len(extra)
    if bad_total:
        print("\n❌ 共 %d 个颜色越界 —— 多半是生成器里的硬编码" % bad_total)
        return 1
    print("\n✅ 两款方案的产物用色都严格来自各自的调色板")
    return 0


if __name__ == "__main__":
    sys.exit(main())
