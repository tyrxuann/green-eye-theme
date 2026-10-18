#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三套深色候选配色，用于挑选方向。

针对原版「松林墨」被指出的四个问题：
  1. 语义色相撞车：关键字/类名/类型参数/标签全挤在 60°~90°，看代码分不出层次。
     → 三套共用一套"8 色相骨架"，把语义摊到整圈：
        error 0° / number 22° / string 42° / class 68° / keyword 105° /
        function 172° / constant&type 200° / annotation 285°
  2. 背景过灰发闷：原版饱和度 10.3%、明度 15.3%。→ 提到 15%~21% / 14%~18%。
  3. 对比度偏低：原版数字 6.6:1、注释 4.58:1。
     → 改为**按目标对比度反解明度**，三套都做到正文 ≥10:1、语法 6.5~8:1、注释 ≥4.9:1。
  4. 关键字变荧光绿的风险：高对比 + 高饱和在绿色上会互相顶（绿通道主导亮度），
     所以给明度加了上下钳制，并把关键字的目标对比度单独压低，
     换成"浓郁但不刺眼"的中明度绿。

三套的差别：
  A 松林·清  冷调墨绿底 H≈156°  —— 均衡，绿意明确
  B 苔原·暖  暖黄绿底 H≈99°    —— 最亮最柔，暖色系语法
  C 深潭·锐  深青绿底 H≈172°   —— 底色最浓、对比最高，最清晰
"""
import colorsys
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from palette import hex_to_rgb, contrast  # noqa: E402


def hsl(h, s, l):
    r, g, b = colorsys.hls_to_rgb((h % 360) / 360.0, l / 100.0, s / 100.0)
    return "#%02X%02X%02X" % tuple(round(c * 255) for c in (r, g, b))


def _adj(hexcolor, dh=0.0, ds=1.0, dl=0.0):
    r, g, b = [v / 255 for v in hex_to_rgb(hexcolor)]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return hsl(h * 360 + dh, min(100.0, s * 100 * ds), min(100.0, max(0.0, l * 100 + dl)))


# ---------------------------------------------------------------------------
# 8 色相骨架：(色相, 饱和度%, 目标对比度, 明度下限, 明度上限)
#   明度由目标对比度反解，再用上下限钳制：下限防"发黑"，上限防"发白/发荧光"。
#   关键字的目标对比度特意压低到 6.6 —— 绿通道主导亮度，硬追 9:1 只会得到荧光绿。
# ---------------------------------------------------------------------------
SKELETON = {
    "comment":      (150, 14, 4.9, 45, 62),
    "keyword":      (132, 55, 7.2, 52, 74),
    "string":       (42, 55, 7.6, 52, 76),
    "escape":       (30, 68, 7.2, 52, 76),
    "number":       (25, 65, 7.0, 52, 76),
    "constant":     (265, 52, 7.2, 52, 78),
    "class_name":   (75, 62, 7.4, 52, 76),
    "type_param":   (215, 48, 7.2, 52, 78),
    "function":     (186, 58, 7.4, 52, 78),
    "annotation":   (305, 50, 7.4, 52, 80),
    "attr_name":    (42, 55, 7.6, 52, 76),
    "error":        (0, 68, 6.4, 50, 74),
    "warning":      (45, 65, 7.4, 52, 76),
    "todo":         (28, 65, 7.4, 52, 76),
    "hyperlink":    (215, 58, 7.4, 52, 78),
    "field":        (160, 26, 8.2, 52, 82),
    "parameter":    (140, 16, 9.6, 60, 88),
    "local_var":    (140, 12, 11.0, 70, 94),
    "fg":           (140, 12, 10.8, 70, 92),
    "fg_dim":       (150, 14, 6.4, 55, 74),
    "fg_sel":       (140, 14, 12.6, 80, 98),
    "operator":     (150, 18, 6.8, 52, 78),
    "brace":        (150, 14, 6.2, 48, 76),
    "punctuation":  (150, 16, 7.0, 50, 78),
    "line_numbers": (150, 14, 3.4, 44, 60),
}


def solve_light(hue, sat, bg_hex, target, lmin, lmax):
    """按目标对比度反解明度，并钳制在 [lmin, lmax] 内。"""
    best, bestd = (lmin + lmax) / 2, 1e9
    l = lmin
    while l <= lmax + 1e-9:
        d = abs(contrast(hsl(hue, sat, l), bg_hex) - target)
        if d < bestd:
            best, bestd = l, d
        l += 0.25
    return best


DIRECTIONS = {
    "A": dict(
        label="松林·清", name="Green Eye Dark A", dh=0.0, ds=1.00, tgt=1.00,
        bg=["#24332D", "#1D2925", "#2C3D36", "#1B2622"],
        chrome=["#2A3A33", "#37584C", "#6E7F3C", "#3D5A4A", "#6E837A", "#2E403A", "#2B3C36"],
        diff=["#27412F", "#4A2E2E", "#263B47"],
    ),
    "B": dict(
        label="苔原·暖", name="Green Eye Dark B", dh=-12.0, ds=0.92, tgt=0.96,
        bg=["#2E3729", "#262E22", "#364030", "#232B20"],
        chrome=["#343E2E", "#44563C", "#6E7638", "#485A3E", "#7A8470", "#3A4431", "#353F2D"],
        diff=["#2E422A", "#4A3230", "#2C3A3E"],
    ),
    "C": dict(
        label="深潭·锐", name="Green Eye Dark C", dh=6.0, ds=1.08, tgt=1.06,
        bg=["#1B2C29", "#15211E", "#233733", "#131E1B"],
        chrome=["#213331", "#2D5D54", "#6E7F2E", "#345C51", "#6B8881", "#253936", "#213532"],
        diff=["#1E4235", "#4A2C2C", "#1E3B4A"],
    ),
}


def build(d):
    p = {"label": d["label"], "name": d["name"], "parent": "Darcula", "dark": True}
    for key, (h, s, target, lmin, lmax) in SKELETON.items():
        hh, ss = h + d["dh"], min(100.0, s * d["ds"])
        p[key] = hsl(hh, ss, solve_light(hh, ss, d["bg"][0], target * d["tgt"], lmin, lmax))
    bg, ch = d["bg"], d["chrome"]
    p.update({
        "bg_editor": bg[0], "bg_panel": bg[1], "bg_raised": bg[2],
        "bg_gutter": bg[0], "bg_console": bg[3],
        "bg_folded": ch[0], "bg_caret_row": ch[0],
        "bg_selection": ch[1], "bg_search": ch[2], "bg_matched_brace": ch[3],
        "indent_guide": ch[5], "right_margin": ch[5], "whitespace": ch[6],
        "caret": p["keyword"], "line_numbers_active": p["keyword"],
        "bg_diff_add": d["diff"][0], "bg_diff_del": d["diff"][1],
        "bg_diff_mod": d["diff"][2],
        "doc_comment": _adj(p["comment"], dl=6),
        "interface_name": p["class_name"], "enum_name": p["class_name"],
        "function_call": p["function"], "static_field": p["constant"],
        "tag": p["keyword"], "attr_value": p["string"],
        "info": p["constant"], "deprecated": p["fg_dim"],
        "bookmark": p["warning"], "breakpoint": p["error"],
        "fg_search": p["fg_sel"],
    })
    p["line_numbers"] = ch[4]
    p.update({
        "con_black": bg[1], "con_red": p["error"], "con_green": p["keyword"],
        "con_yellow": p["warning"], "con_blue": p["constant"],
        "con_magenta": p["annotation"], "con_cyan": p["function"],
        "con_gray": p["fg_dim"], "con_darkgray": ch[4], "con_lightgray": p["fg"],
        "con_lightred": _adj(p["error"], dl=9),
        "con_lightgreen": _adj(p["keyword"], dl=7),
        "con_lightyellow": _adj(p["warning"], dl=7),
        "con_lightblue": _adj(p["constant"], dl=7),
        "con_lightmagenta": _adj(p["annotation"], dl=7),
        "con_lightcyan": _adj(p["function"], dl=7),
        "con_white": p["fg_sel"],
    })
    return p


CANDIDATES = {k: build(v) for k, v in DIRECTIONS.items()}

# ---------------------------------------------------------------------------
# A → C 之间的中间点：背景、界面色、语法力度一起插值
# ---------------------------------------------------------------------------
def _hls(hexcolor):
    r, g, b = [v / 255 for v in hex_to_rgb(hexcolor)]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return h * 360, s * 100, l * 100


def _lerp_hex(h1, h2, t):
    """在 HLS 空间插值两个颜色（色相走近路，避免绕圈）。"""
    h1v, s1, l1 = _hls(h1)
    h2v, s2, l2 = _hls(h2)
    dh = ((h2v - h1v + 540) % 360) - 180
    return hsl(h1v + dh * t, s1 + (s2 - s1) * t, l1 + (l2 - l1) * t)


def _between(t):
    a, c = DIRECTIONS["A"], DIRECTIONS["C"]
    return dict(
        label="中间 %d%%" % round(t * 100), name="Green Eye Dark M%d" % round(t * 100),
        dh=a["dh"] + (c["dh"] - a["dh"]) * t,
        ds=a["ds"] + (c["ds"] - a["ds"]) * t,
        tgt=a["tgt"] + (c["tgt"] - a["tgt"]) * t,
        bg=[_lerp_hex(x, y, t) for x, y in zip(a["bg"], c["bg"])],
        chrome=[_lerp_hex(x, y, t) for x, y in zip(a["chrome"], c["chrome"])],
        diff=[_lerp_hex(x, y, t) for x, y in zip(a["diff"], c["diff"])],
    )


MID_POINTS = {"M1": 0.30, "M2": 0.50, "M3": 0.70}
MIDS = {k: build(_between(t)) for k, t in MID_POINTS.items()}
