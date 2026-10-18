#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
渲染样式一致性：预览图里用的粗体/斜体，必须与产物的 FONT_TYPE 一致。

起因：渲染器长期只吃颜色，于是 FONT_TYPE（关键字该不该加粗、TODO 该不该斜体、
常量该不该斜体）**在预览里完全不可见**，两轮"逐像素核对"都照不到这一整个维度；
而 .icls 里还真的写错了 5 个键（关键字加粗、注释斜体、TODO 加粗、常量缺斜体）。
现在渲染器接上了样式，这条检查保证"渲染器说的"和"产物写的"不会各说各话。
"""
import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from palette import PALETTES, icls_path  # noqa: E402
from render_spec import STYLE_BY_KEY  # noqa: E402

# 渲染器的 token 键 -> .icls 属性键
TOKEN_TO_ATTR = {
    "doc_comment": "DEFAULT_DOC_COMMENT",
    "todo": "TODO_DEFAULT_ATTRIBUTES",
    "constant": "DEFAULT_CONSTANT",
    "function": "DEFAULT_STATIC_METHOD",
    "keyword": "DEFAULT_KEYWORD",
    "comment": "DEFAULT_LINE_COMMENT",
}
FT_TO_STYLE = {None: "", "0": "", "1": "b", "2": "i", "3": "bi"}


def main():
    bad = 0
    for key, pal in sorted(PALETTES.items()):
        root = ET.parse(icls_path(pal)).getroot()
        attrs = {o.get("name"): {x.get("name"): x.get("value") for x in o.find("value")}
                 for o in root.find("attributes") if o.find("value") is not None}
        print("【%s「%s」】渲染器声明的样式 vs 产物 FONT_TYPE" % (pal["name"], pal["label"]))
        for token, style in sorted(STYLE_BY_KEY.items()):
            attr = TOKEN_TO_ATTR.get(token)
            if not attr or attr not in attrs:
                continue
            real = FT_TO_STYLE.get(attrs[attr].get("FONT_TYPE"), "")
            ok = real == style
            bad += 0 if ok else 1
            print("   %s %-12s 渲染=%-3s 产物(%s)=%-3s"
                  % ("✅" if ok else "❌", token, style or "常规", attr, real or "常规"))
    # 反向：产物里是粗/斜体、渲染器却按常规画的。
    # 例外：mock 的 tokenizer 分不清静态/实例方法，无法可靠地按语义画斜体。
    MOCK_LIMITATION = {
        "DEFAULT_STATIC_METHOD": "mock 分不清静态/实例方法调用，全部画斜体会是错的",
        "DEFAULT_STATIC_FIELD": "同上：静态字段与实例字段在语法上无法区分",
    }
    for key, pal in sorted(PALETTES.items()):
        root = ET.parse(icls_path(pal)).getroot()
        attrs = {o.get("name"): {x.get("name"): x.get("value") for x in o.find("value")}
                 for o in root.find("attributes") if o.find("value") is not None}
        for token, attr in TOKEN_TO_ATTR.items():
            if attr in attrs:
                real = FT_TO_STYLE.get(attrs[attr].get("FONT_TYPE"), "")
                if real and token not in STYLE_BY_KEY:
                    if attr in MOCK_LIMITATION:
                        print("   ⚠️  %s 产物是 %s，渲染器不画 —— 已知限制：%s"
                              % (attr, real, MOCK_LIMITATION[attr]))
                    else:
                        print("   ❌ %s 在产物里是 %s，但渲染器没画" % (attr, real))
                        bad += 1
    if bad:
        print("\n❌ 渲染样式与产物不一致 %d 处" % bad)
        return 1
    print("\n✅ 渲染样式与产物 FONT_TYPE 一致")
    return 0


if __name__ == "__main__":
    sys.exit(main())
