#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
补上渲染管线缺失的两个视图：**diff 视图**与**调试器视图**。

为什么必须补：撞色检查里最可疑的几条例外（涉及 diff 新增/删除/修改行、
断点行、调用栈非栈顶帧、当前执行行）**全部只在这两个视图里出现**，
而之前渲染管线一个都没画 —— 也就是说这些例外在结构上无法被证伪。
（这一条是第二款主题第 1 轮评审提出的 MUST。）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw  # noqa: E402
from render_preview import (S, FONT_SIZE, GUTTER_W, LINE_H, F,  # noqa: E402
                            draw_run, run_width)
from palette import PALETTES  # noqa: E402

PAD_TOP = 10
SMALL = 12
TITLE_H = 30
TAB_H = 34


def _window(W, H, pal, tabs, active=0):
    img = Image.new("RGB", (W * S, H * S), pal["bg_editor"])
    d = ImageDraw.Draw(img)
    # 标题栏
    d.rectangle([0, 0, W * S, TITLE_H * S], fill=pal["bg_panel"])
    for i, col in enumerate(("#5A5A52", "#8A8A78", "#4A5A50")):
        d.ellipse([(12 + i * 20) * S, 10 * S, (22 + i * 20) * S, 20 * S], fill=col)
    # 标签栏
    ty = TITLE_H * S
    d.rectangle([0, ty, W * S, ty + TAB_H * S], fill=pal["bg_panel"])
    tx = 0
    for i, t in enumerate(tabs):
        tw = (12 + run_width(d, t, SMALL) + 12) * S
        if i == active:
            d.rectangle([tx, ty, tx + tw, ty + TAB_H * S], fill=pal["bg_editor"])
            d.line([tx, ty + TAB_H * S - 2 * S, tx + tw, ty + TAB_H * S - 2 * S],
                   fill=pal["tab_underline"], width=2 * S)
        draw_run(d, tx + 12 * S, ty + 9 * S, t, SMALL * S,
                 pal["fg"] if i == active else pal["fg_dim"])
        tx += tw
    return img, d


def _code_line(d, pal, y, ln, text, w, bg=None, marker=None, marker_col=None,
               styles=None, indent=0):
    """画一行代码（行号槽 + 代码区），可选整行底色 / gutter 标记。"""
    x0 = GUTTER_W * S + 8 * S
    if bg:
        d.rectangle([0, y, w * S, y + LINE_H * S], fill=bg)
    if marker and marker_col:
        d.rectangle([0, y, 5 * S, y + LINE_H * S], fill=marker_col)
    draw_run(d, 12 * S, y + 5 * S, str(ln) if ln else "", SMALL * S, pal["line_numbers"])
    if marker:
        draw_run(d, 40 * S, y + 5 * S, marker, SMALL * S,
                 marker_col or pal["fg_dim"])
    cx = x0 + indent * 8 * S
    for chunk, key in (styles or [("", "fg")]):
        st = "i" if key == "doc_comment" else ""
        cx = draw_run(d, cx, y + 5 * S, chunk, FONT_SIZE * S, pal[key], style=st)
    return y + LINE_H * S


def render_diff(pal):
    """diff 视图：新增/删除/修改行 + 合并冲突 + gutter 标记 + 滚动条条纹。"""
    W, H = 720, 330
    img, d = _window(W, H, pal, ["CarbonCalculator.java  (左)  ←→  (右)"])
    y = (TITLE_H + TAB_H) * S + PAD_TOP * S
    lines = [
        (40, "     if (plots == null || plots.isEmpty()) {", None, None),
        (41, '         throw new IllegalArgumentException("empty");', pal["bg_diff_del"], "-"),
        (41, '         throw new IllegalArgumentException("样地列表不能为空: " + plots);',
         pal["bg_diff_add"], "+"),
        (42, "     }", None, None),
        (44, "     double mean = values.stream().mapToDouble(Double::doubleValue)",
         None, None),
        (45, "             .average().orElse(0.0);",
         pal["bg_diff_mod"], "~"),
        (47, "     return result;", None, None),
        # 修改行内"被删除的片段"（占位行，实际由 _inline_deleted 画）
        (47.5, "", None, None),

        (48, "<<<<<<< HEAD", pal["bg_diff_del"], None),
        (49, "     private final double coefficient = 0.48;", pal["bg_diff_add"], None),
        (50, "=======", pal["bg_diff_del"], None),
        (51, "     private final double coefficient = 0.52;", pal["bg_diff_add"], None),
        (52, ">>>>>>> feature", pal["bg_error_hint"], None),
    ]
    import re
    TOK = re.compile(r'"[^"]*"|\b(?:if|throw|new|return|private|final|double)\b|'
                     r'\b\d+\.\d+\b|<<<<<<<|=======|>>>>>>>')
    for ln, text, bg, mk in lines:
        if isinstance(ln, float):          # 内联删除片段的示意行
            y = _inline_deleted(d, pal, y, W)
            continue
        parts, i = [], 0
        for m in TOK.finditer(text):
            if m.start() > i:
                parts.append((text[i:m.start()], "fg"))
            tok = m.group()
            key = ("string" if tok.startswith('"') else
                   "number" if tok[0].isdigit() else
                   "error" if tok[0] in "<>=!" else "keyword")
            parts.append((tok, key))
            i = m.end()
        if i < len(text):
            parts.append((text[i:], "fg"))
        y = _code_line(d, pal, y, ln, text, W, bg=bg, marker=mk,
                       marker_col=(pal["error"] if mk == "-" else
                                   pal["string"] if mk == "+" else
                                   pal["number"] if mk == "~" else None),
                       styles=parts)
    # 底部：gutter 条纹带（ERROR_STRIPE 语义）
    sy = H * S - 26 * S
    d.rectangle([0, sy, W * S, H * S], fill=pal["bg_panel"])
    for cx, col in ((0.52, pal["error"]), (0.62, pal["string"]), (0.72, pal["search_stripe"]),
                    (0.82, pal["bookmark"]), (0.92, pal["number"])):
        d.rectangle([int(W * S * cx), sy + 8 * S, int(W * S * cx) + 10 * S, sy + 18 * S],
                    fill=col)
    draw_run(d, 12 * S, sy + 7 * S, "gutter 条纹：", SMALL * S, pal["fg_dim"])
    draw_run(d, 100 * S, sy + 7 * S, "错误 / 新增 / 查找 / 书签 / 数字", SMALL * S,
             pal["fg_dim"])
    return img.resize((W, H), Image.LANCZOS)


def _inline_deleted(d, pal, y, W):
    """画一行"修改行里的内联删除片段" —— 让 DELETED_TEXT_ATTRIBUTES 能被像素核对。

    这一条是评审 S1' 要求的：原来 diff 视图用正文色画删除行，预览比真机乐观。
    """
    d.rectangle([0, y, W * S, y + LINE_H * S], fill=pal["bg_diff_mod"])
    draw_run(d, 12 * S, y + 5 * S, "46", SMALL * S, pal["line_numbers"])
    cx = GUTTER_W * S + 8 * S
    cx = draw_run(d, cx, y + 5 * S, "     mean = values.", FONT_SIZE * S, pal["fg"])
    # 被删片段：暗红底 + 正文色 + 删除线
    frag = "average()"
    fw = run_width(d, frag, FONT_SIZE * S)
    d.rectangle([cx - 2 * S, y + 3 * S, cx + fw + 2 * S, y + LINE_H * S - 3 * S],
                fill=pal["bg_diff_del"])
    draw_run(d, cx, y + 5 * S, frag, FONT_SIZE * S, pal["fg"])
    d.line([cx - 2 * S, y + LINE_H * S / 2, cx + fw + 2 * S, y + LINE_H * S / 2],
           fill=pal["grey_underline"], width=S)
    cx += fw
    draw_run(d, cx, y + 5 * S, "();   // ← 内联删除片段（fg + 删除线）",
             FONT_SIZE * S, pal["fg"])
    return y + LINE_H * S


def render_debug(pal):
    """调试器视图：当前执行行 + 断点行 + 调用栈（栈顶/非栈顶）+ 变量表。"""
    W, H = 860, 372
    img, d = _window(W, H, pal, ["CarbonCalculator.java", "Plot.java"])
    # 左侧编辑器
    y = (TITLE_H + TAB_H) * S + PAD_TOP * S
    code = [
        (34, "public Map<String, Double> summarize(List<Plot> plots) {", None, None),
        (35, "    if (Objects.isNull(plots)) {", None, None),
        (36, '        throw new IllegalArgumentException("空");', None, None),
        (37, "    }", None, None),
        (38, "    this.calls++;", pal["bg_breakpoint"], "\u25cf"),
        (39, "    Map<String, Double> r = plots.stream().collect(", None, None),
        (40, "            Collectors.toMap(Plot::id, p -> p.biomass(coefficient)));",
         pal["bg_execution_point"], "\u25b6"),
    ]
    for ln, text, bg, mk in code:
        y = _code_line(d, pal, y, ln, text, W, bg=bg, marker=mk,
                       marker_col=(pal["error"] if mk == "\u25cf" else pal["number"]),
                       styles=[(text, "fg")])
    # 右侧面板：调用栈 + 变量
    px = 470 * S
    d.rectangle([px, (TITLE_H + TAB_H) * S, W * S, H * S], fill=pal["bg_panel"])
    d.line([px, (TITLE_H + TAB_H) * S, px, H * S], fill=pal["separator"], width=S)
    ty = (TITLE_H + TAB_H) * S + 10 * S
    draw_run(d, px + 12 * S, ty, "Frames", SMALL * S, pal["fg_dim"])
    frames = [("summarize:39", pal["bg_execution_point"], pal["fg"]),
              ("lambda$summarize$0:40", pal["bg_not_top_frame"], pal["fg_dim"]),
              ("collect:null", pal["bg_not_top_frame"], pal["fg_dim"]),
              ("main:12", pal["bg_not_top_frame"], pal["fg_dim"])]
    fy = ty + 20 * S
    for name, bg, fg in frames:
        d.rectangle([px + 8 * S, fy, W * S - 8 * S, fy + 20 * S], fill=bg)
        draw_run(d, px + 14 * S, fy + 3 * S, name, SMALL * S, fg)
        fy += 22 * S
    vy = fy + 14 * S
    draw_run(d, px + 12 * S, vy, "Variables", SMALL * S, pal["fg_dim"])
    vy += 20 * S
    for name, val, col, write in (("plots", "[Plot@1f2a, Plot@3c4b]", pal["fg"], False),
                                  ("coefficient", "0.48", pal["constant"], False),
                                  ("mean", "12.5", pal["number"], True),
                                  ("calls", "3", pal["constant"], False)):
        draw_run(d, px + 14 * S, vy + 3 * S, name, SMALL * S, col)
        draw_run(d, px + 150 * S, vy + 3 * S, val, SMALL * S, pal["number"])
        if write:
            # 重新赋值的变量：中性灰下划线（DEFAULT_REASSIGNED_*）
            d.line([px + 14 * S, vy + 18 * S, px + 140 * S, vy + 18 * S],
                   fill=pal["grey_underline"], width=S)
        vy += 22 * S
    # 执行点提示条
    d.rectangle([px + 8 * S, H * S - 34 * S, W * S - 8 * S, H * S - 14 * S],
                fill=pal["bg_execution_point"])
    draw_run(d, px + 16 * S, H * S - 30 * S, "\u25b6 当前执行点 / \u25cf 断点",
             SMALL * S, pal["fg"])
    return img.resize((W, H), Image.LANCZOS)


def main():
    ap = __import__("argparse").ArgumentParser()
    ap.add_argument("--outdir", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "preview"))
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    for key, tag in (("dark", "dark"), ("mineral", "mineral")):
        pal = PALETTES[key]
        for name, fn in (("diff", render_diff), ("debug", render_debug)):
            img = fn(pal)
            p = os.path.join(a.outdir, "%s-%s.png" % (name, tag))
            img.save(p)
            print("写入 %s%s" % (os.path.basename(p), img.size))
    return 0


if __name__ == "__main__":
    sys.exit(main())
