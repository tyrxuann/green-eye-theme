#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 palette.py 自动生成 README 里的配色表（避免文档与实现漂移）。

注意：同一行在不同主题里的"说明"并不相同（松林沿用官方色相，矿彩是原创分配），
所以 notes 按主题分开；以前只用一份松林 notes 套两款，矿彩表里的 H/S 说明全是错的。
用法: python3 gen_readme_table.py [README 路径]
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from palette import PALETTES, contrast  # noqa: E402

B = "<!-- PALETTE-TABLE:BEGIN -->"
E = "<!-- PALETTE-TABLE:END -->"
OFFICIAL = {  # 官方 Islands Dark 的对应值（评审用的对照基准）
    "fg": "#bcbec4", "comment": "#7a7e85", "doc_comment": "#5f826b",
    "keyword": "#cf8e6d", "string": "#6aab73", "number": "#2aacb8",
    "function": "#56a8f5", "constant": "#c77dbb", "annotation": "#b3ae60",
    "warning": "官方未定义", "todo": "#8bb33d", "error": "#f75464",
    "caret": "#ced0d6", "line_numbers": "#4b5059", "hyperlink": "#548af7",
}
ROWS = [
    ("正文 / 标识符 / 类名 / 括号 / 运算符 / 标签", "fg", "全部同色（官方做法）"),
    ("注释", "comment", "冷绿灰中性，与正文色相拉开 60°+"),
    ("文档注释（斜体）", "doc_comment", "压到 3.7:1，长 Javadoc 不再发光"),
    ("关键字", "keyword", "色相/饱和度同官方"),
    ("字符串", "string", "色相 128°→112°，与底色间距拉到 36°"),
    ("数字", "number", "同官方"),
    ("函数 / 方法", "function", "饱和度 89%→79%"),
    ("字段 / 静态 / 常量", "constant", "同官方"),
    ("注解 / Javadoc 标签", "annotation", "同官方"),
    ("警告（前景＝注解色，波浪线另用）", "warning", "不自造色相；波浪线见下"),
    ("警告波浪线", "warning_stripe", "比前景明显更亮"),
    ("TODO（斜体）", "todo", "同官方"),
    ("错误 / 未匹配括号", "error", "同官方"),
    ("链接", "hyperlink", "色相 220°→245°，与函数蓝分开"),
    ("光标", "caret", "官方 11.3:1"),
    ("行号", "line_numbers", "官方 2.15:1"),
    ("背景：编辑器 / 面板 / 浮层", None, ""),
    ("边框：浮层轮廓 / 窗口发丝线", None, ""),
    ("当前行 / 折叠区", None, ""),
    ("选中 / 查找匹配", None, ""),
    ("diff 新增 / 删除 / 修改", None, ""),
]

# 矿彩是原创分配，H/S 说明不能复述松林的官方色相。
MINERAL_NOTES = {
    "comment": "冷石色，与正文暖墨分层",
    "keyword": "金黄 H42，与错误(H358)分开",
    "string": "冰青 H196，与底色 H148 拉开 48°",
    "number": "紫晶 H272，与函数(玉青 H168)分开",
    "function": "玉青 H168，S50 降低刺激",
    "constant": "赭石 H20，暖极深处",
    "annotation": "玫瑰 H338，暖极另一端",
    "todo": "芥黄 H62，与字符串(冰青)拉开",
    "error": "红 H358，与关键字(H42)分开",
    "hyperlink": "灰青 H168，比函数更灰、更暗",
}
SELECTION_LABELS = {"dark": ("青", "绿"), "mineral": ("绿", "琥珀")}


def build_table(p, marker_begin, marker_end, theme_key):
    notes = MINERAL_NOTES if theme_key == "mineral" else {}
    rows = []
    for name, key, note in ROWS:
        if key is None:
            if name.startswith("背景"):
                v = "%s / %s / %s" % (p["bg_editor"], p["bg_panel"], p["bg_raised"])
                o = "#191A1C / #26282C / #33353B"
                d = "浮层对编辑器 %.2f:1" % contrast(p["bg_raised"], p["bg_editor"])
            elif name.startswith("边框"):
                v = "%s / %s" % (p["border"], p["separator"])
                o = "—"
                d = "对编辑器 %.2f / %.2f:1" % (contrast(p["border"], p["bg_editor"]),
                                                contrast(p["separator"], p["bg_editor"]))
            elif name.startswith("当前行"):
                v = "%s（与底色同相）" % p["bg_caret_row"]
                o = "—"
                d = "%.2f:1" % contrast(p["bg_caret_row"], p["bg_editor"])
            elif name.startswith("选中"):
                sel, sea = SELECTION_LABELS.get(theme_key, ("选中", "查找"))
                v = "%s %s / %s %s + 描边 %s" % (p["bg_selection"], sel,
                                                 p["bg_search"], sea,
                                                 p["search_border"])
                o = "—"
                d = "%.2f / %.2f:1" % (contrast(p["bg_selection"], p["bg_editor"]),
                                       contrast(p["bg_search"], p["bg_editor"]))
            else:
                v = "%s / %s / %s" % (p["bg_diff_add"], p["bg_diff_del"],
                                      p["bg_diff_mod"])
                o = "—"
                d = "%.2f / %.2f / %.2f:1" % tuple(
                    contrast(p[k], p["bg_editor"]) for k in
                    ("bg_diff_add", "bg_diff_del", "bg_diff_mod"))
            rows.append("| %s | %s | `%s` | %s |" % (name, o, v, d))
        else:
            c = "%.2f:1" % contrast(p[key], p["bg_editor"])
            real_note = notes.get(key, note)
            rows.append("| %s | `%s` | `%s` | %s %s |"
                        % (name, OFFICIAL.get(key, "—"), p[key], c,
                           ("· " + real_note) if real_note else ""))
    return (marker_begin + "\n| 语义 | 官方 Islands Dark | %s「%s」 | 对比度 |\n"
            "|---|---|---|---|\n" % ("本主题", p["label"]) + "\n".join(rows) + "\n" + marker_end)


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "README.md"
    s = open(path, encoding="utf-8").read()
    n = 0
    for key, pal in sorted(PALETTES.items()):
        b = "<!-- PALETTE-TABLE:%s:BEGIN -->" % key.upper()
        e = "<!-- PALETTE-TABLE:%s:END -->" % key.upper()
        if b not in s:
            print("README 缺少标记 %s（跳过 %s）" % (b, key))
            continue
        block = build_table(pal, b, e, key)
        s = re.sub(re.escape(b) + r".*?" + re.escape(e), block, s, count=1, flags=re.S)
        n += 1
    open(path, "w", encoding="utf-8").write(s)
    print("README 配色表已重新生成（%d 款主题）" % n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
