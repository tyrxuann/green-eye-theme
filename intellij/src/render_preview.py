#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
渲染配色预览图（模拟 IntelliJ IDEA 编辑器窗口），用于在安装前直观检查护眼效果。

用法:
    python3 render_preview.py --outdir ../preview
"""
import argparse
import os
import re
import sys
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from palette import PALETTES  # noqa: E402

S = 2                      # 超采样倍数
FONT_SIZE = 14
LINE_H = 25
GUTTER_W = 58
PAD_TOP = 10
MONO = "/System/Library/Fonts/Menlo.ttc"
CJK = "/System/Library/Fonts/Hiragino Sans GB.ttc"
CODE_W = 980

CODE = '''# 项目：森林碳汇估算 forest_carbon.py
"""护眼绿色主题预览 —— 低饱和、低对比度，不用刺眼的荧光绿。"""

import math
from dataclasses import dataclass

TODO_LIMIT = 1_200.5
DEFAULT_SPECIES = "Pinus koraiensis"


@dataclass
class Plot:
    """一块固定样地。"""

    plot_id: str
    area_ha: float = 0.06
    trees: int = 0

    def biomass(self, coefficient: float = 0.48) -> float:
        # TODO: 换成按树种查表
        total = self.trees * coefficient * self.area_ha
        chars = ["\\\\t", "\\\\n", "\\u00b1"]
        return round(total, 3)
'''

GROUP = {
    "comment": "comment", "docstr": "doc_comment", "string": "string",
    "escape": "escape", "keyword": "keyword", "number": "number",
    "builtin": "constant", "defname": "function", "classname": "class_name",
    "call": "function_call", "cls": "class_name", "field": "field",
    "param": "parameter", "decorator": "annotation", "op": "operator",
    "brace": "brace", "punct": "punctuation",
}

MASTER = re.compile(r"""
    (?P<comment>\#[^\n]*)
  | (?P<docstr>\"\"\"[\s\S]*?\"\"\")
  | (?P<string>[fFrRbB]{0,2}\"(?:\\.|[^\"\\])*\"|[fFrRbB]{0,2}'(?:\\.|[^'\\])*')
  | (?P<field>self\.\w+)
  | (?P<decorator>@\w+)
  | (?P<defname>(?<=\bdef )\w+)
  | (?P<classname>(?<=\bclass )\w+)
  | (?P<keyword>\b(?:def|class|return|if|elif|else|for|while|in|not|and|or|import
        |from|as|with|try|except|finally|raise|yield|lambda|None|True|False|is
        |pass|break|continue|global|nonlocal|assert|async|await|del)\b)
  | (?P<number>\b\d[\d_]*(?:\.\d+)?\b)
  | (?P<param>\b(?:plots|coefficient|verbose|area_ha|trees|plot_id|self)\b)
  | (?P<builtin>\b(?:print|len|range|list|dict|set|str|int|float|bool|sum|min
        |max|enumerate|zip|sorted|isinstance|super|type|open|round|object)\b)
  | (?P<call>\b[A-Za-z_]\w*(?=\s*\())
  | (?P<cls>\b[A-Z]\w*\b)
  | (?P<escape>\\[tnru\\\"'])
  | (?P<op>[-+*/%=<>!&|^~]+)
  | (?P<brace>[(){}\[\]])
  | (?P<punct>[,:;.])
""", re.X)

CJK_RE = re.compile(r"[\u2e80-\u9fff\u3000-\u303f\uff00-\uffef\u00b1]")


def split_cjk(text):
    """把字符串切成 (片段, 是否中日韩) 序列，便于分别用两种字体绘制。"""
    out, buf, cur = [], "", None
    for ch in text:
        is_cjk = bool(CJK_RE.match(ch))
        if cur is None or is_cjk == cur:
            buf += ch
        else:
            out.append((buf, cur))
            buf = ch
        cur = is_cjk
    if buf:
        out.append((buf, cur))
    return out


# Menlo.ttc 里的四个面（index: 0=Regular 1=Bold 2=Italic 3=BoldItalic）
FACE_INDEX = {"": 0, "b": 1, "i": 2, "bi": 3}


class Fonts:
    def __init__(self):
        self.cache = {}

    def get(self, size, cjk=False, style=""):
        """style: ""=常规 b=粗体 i=斜体 bi=粗斜体（对应 .icls 的 FONT_TYPE 0/1/2/3）。

        之前渲染器只吃颜色，于是 FONT_TYPE 这一整个维度**在预览里看不见** ——
        keyword 该不该加粗、TODO 该不该斜体，两轮逐像素核对都没照到。现在接上。
        """
        key = (size, cjk, style if not cjk else "")
        if key not in self.cache:
            if cjk:
                f = ImageFont.truetype(CJK, size)
            else:
                try:
                    f = ImageFont.truetype(MONO, size, index=FACE_INDEX.get(style, 0))
                except Exception:
                    try:
                        f = ImageFont.truetype(MONO, size)
                    except Exception:
                        f = ImageFont.load_default()
            self.cache[key] = f
        return self.cache[key]


F = Fonts()


def draw_run(d, x, y, text, size, fill, style=""):
    """绘制一段可能混排中英文的文本，返回结束 x。style 见 Fonts.get()。"""
    latin, cjkf = F.get(size, style=style), F.get(size, cjk=True)
    for chunk, is_cjk in split_cjk(text):
        f = cjkf if is_cjk else latin
        d.text((x, y), chunk, font=f, fill=fill)
        x += d.textlength(chunk, font=f)
    return x


def run_width(d, text, size):
    latin, cjkf = F.get(size), F.get(size, cjk=True)
    w = 0
    for chunk, is_cjk in split_cjk(text):
        w += d.textlength(chunk, font=cjkf if is_cjk else latin)
    return w


def tokens(line):
    out, pos = [], 0
    for m in MASTER.finditer(line):
        if m.start() > pos:
            out.append((line[pos:m.start()], "fg"))
        out.append((m.group(), GROUP.get(m.lastgroup, "fg")))
        pos = m.end()
    if pos < len(line):
        out.append((line[pos:], "fg"))
    return out


def render(pal, code=CODE, line_tokens=None, caret_line=None, sel_lines=None,
           wave_line=None, breadcrumb="forest_carbon.py  ›  src  ›  models",
           tabs=("forest_carbon.py", "test_plots.py"), status_mid="Python 3.12",
           height=None, show_margin=True, sel_span=(-5, 300), wave_color=None,
           token_styles=None):
    """渲染一个仿 IDE 窗口。line_tokens 为预切分结果时，可渲染任意语言。"""
    W = CODE_W
    lines = code.split("\n")
    H = height or (30 + 34 + 26 + PAD_TOP + len(lines) * LINE_H + 44)
    if caret_line is None:
        caret_line = max(0, len(lines) - 1)
    if sel_lines is None:
        sel_lines = {len(lines) - 8, len(lines) - 7} if len(lines) > 10 else set()
    img = Image.new("RGB", (W * S, H * S), pal["bg_panel"])
    d = ImageDraw.Draw(img)
    fs = FONT_SIZE * S
    small = 11 * S
    title_h, tab_h, status_h = 30, 34, 26

    # 面包屑
    d.rectangle([0, 0, W * S, title_h * S], fill=pal["bg_panel"])
    draw_run(d, 14 * S, 8 * S, breadcrumb, small, pal["fg_dim"])

    # 标签页
    ty = title_h * S
    d.rectangle([0, ty, W * S, ty + tab_h * S], fill=pal["bg_panel"])
    tw = 170 * S
    d.rectangle([0, ty, tw, ty + tab_h * S], fill=pal["bg_editor"])
    d.rectangle([0, ty, tw, ty + 2 * S],
                fill=pal.get("tab_underline") or pal["line_numbers"])
    draw_run(d, 14 * S, ty + 9 * S, tabs[0], small, pal["fg"])
    draw_run(d, tw + 14 * S, ty + 9 * S, tabs[1], small, pal["fg_dim"])

    # 编辑区
    ey = ty + tab_h * S
    bottom = (H - status_h) * S
    d.rectangle([0, ey, W * S, bottom], fill=pal["bg_editor"])
    d.rectangle([0, ey, GUTTER_W * S, bottom], fill=pal["bg_gutter"])
    d.line([GUTTER_W * S, ey, GUTTER_W * S, bottom],
           fill=pal["indent_guide"], width=S)

    if show_margin:   # 官方深色主题默认不显示右边距线，深底上它像一道裂缝
        rx = (GUTTER_W + 88 * 7.2) * S
        d.line([rx, ey, rx, bottom], fill=pal["right_margin"], width=S)

    x0 = GUTTER_W * S + 10 * S
    for i, line in enumerate(lines):
        y = ey + PAD_TOP * S + i * LINE_H * S
        if i == caret_line:
            d.rectangle([GUTTER_W * S + S, y, W * S - S, y + LINE_H * S],
                        fill=pal["bg_caret_row"])
        if i in sel_lines:
            d.rectangle([x0 + sel_span[0] * S, y, x0 + sel_span[1] * S,
                         y + LINE_H * S], fill=pal["bg_selection"])
        active = i == caret_line
        d.text((x0 - 12 * S, y), str(i + 1), font=F.get(fs),
               fill=pal["line_numbers_active"] if active else pal["line_numbers"],
               anchor="ra")
        # 缩进参考线
        indent = len(line) - len(line.lstrip(" "))
        for k in range(4, indent + 1, 4):
            gx = x0 + k * 7.2 * S
            d.line([gx, y, gx, y + LINE_H * S], fill=pal["indent_guide"], width=S)
        cx = x0
        for text, key in (line_tokens[i] if line_tokens else tokens(line)):
            col = pal[key]
            if key == "comment" and "TODO" in text:
                col = pal["todo"]
            st = (token_styles or {}).get(key, "")
            cx = draw_run(d, cx, y, text, fs, col, style=st)

    # 光标
    cy = ey + PAD_TOP * S + caret_line * LINE_H * S
    d.rectangle([x0 + 4 * S, cy + 2 * S, x0 + 5 * S, cy + LINE_H * S - 2 * S],
                fill=pal["caret"])

    # 错误波浪线示意
    if wave_line is not None and 0 <= wave_line < len(lines):
        wy = ey + PAD_TOP * S + wave_line * LINE_H * S + LINE_H * S - 3 * S
        for k in range(0, 15 * 7 * S, 4 * S):
            d.line([x0 + k, wy, x0 + k + 2 * S, wy - 2 * S],
                   fill=wave_color or pal["error"], width=S)

    # 状态栏
    sy = bottom
    d.rectangle([0, sy, W * S, H * S], fill=pal["bg_panel"])
    d.line([0, sy, W * S, sy], fill=pal["indent_guide"], width=S)
    draw_run(d, 14 * S, sy + 6 * S, "  main    ✓ 0 errors   1 warning",
             small, pal["fg_dim"])
    draw_run(d, 300 * S, sy + 6 * S, status_mid + " · 护眼绿色主题",
             small, pal["fg_dim"])
    d.text((W * S - 14 * S, sy + 6 * S),
           "UTF-8   LF   Ln %d, Col 5" % (caret_line + 1), font=F.get(small),
           fill=pal["fg_dim"], anchor="ra")
    return img.resize((W, H), Image.LANCZOS)


SWATCH = ["bg_editor", "bg_panel", "bg_caret_row", "bg_selection",
          "line_numbers", "comment", "keyword", "string", "number",
          "class_name", "function", "function_call", "field", "constant",
          "escape", "annotation", "error", "warning"]


def swatch(pal, w=CODE_W):
    cols, cell_h, pad = 9, 56, 12
    rows = (len(SWATCH) + cols - 1) // cols
    h = 24 + rows * cell_h + 8
    img = Image.new("RGB", (w * S, h * S), pal["bg_editor"])
    d = ImageDraw.Draw(img)
    draw_run(d, 12 * S, 5 * S, "%s   ·   %s" % (pal["name"], pal["label"]),
             11 * S, pal["fg"])
    cw = (w - 2 * pad) / cols
    for i, name in enumerate(SWATCH):
        r, c = divmod(i, cols)
        x = (pad + c * cw) * S
        y = (26 + r * cell_h) * S
        d.rectangle([x, y, x + cw * S - 6 * S, y + 26 * S],
                    fill=pal[name], outline=pal["indent_guide"], width=S)
        d.text((x, y + 28 * S), name.replace("_", " "), font=F.get(9 * S),
               fill=pal["fg_dim"])
        d.text((x, y + 40 * S), pal[name].upper(), font=F.get(9 * S),
               fill=pal["line_numbers"])
    return img.resize((w, h), Image.LANCZOS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "preview"))
    args = ap.parse_args()
    out = os.path.abspath(args.outdir)
    os.makedirs(out, exist_ok=True)

    shots, sws = {}, {}
    for key, pal in PALETTES.items():
        shots[key] = render(pal)
        sws[key] = swatch(pal)
        comp = Image.new("RGB", (CODE_W, shots[key].height + sws[key].height),
                         pal["bg_editor"])
        comp.paste(shots[key], (0, 0))
        comp.paste(sws[key], (0, shots[key].height))
        comp.save(os.path.join(out, "preview-%s.png" % key))
        print("写入 preview-%s.png" % key)


if __name__ == "__main__":
    main()
