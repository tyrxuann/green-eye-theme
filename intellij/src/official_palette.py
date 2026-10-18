#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一、把官方 Islands Dark 的真实配色还原成一个调色板（用于渲染对照，证明"学到了什么"）
    数据源：
      build/ref/ide_official_schemes/IslandSchemeDark.xml  —— 编辑器语义色 + <colors> 界面色
      build/ref/ide2026/themes/islands/ManyIslandsDark.theme.json —— UI 颜色 token（含别名，需解析）

二、按官方规律重做一版"绿色版 Islands Dark"：
    规律（来自 analyze_official.py 的统计）：
      · 绝大多数语义用同一个中性色，不逐个染色
      · 重点色比正文暗（中性正文 ~9.4:1，重点色 5.9~6.9:1，注释 ~4.3:1）
      · 重点色明度 44%~65%、饱和度 28%~90%，偏深偏浓而不是粉彩
      · 关键字不加粗；只有静态成员/常量/文档注释/TODO 用斜体
    绿色化方式：背景、中性文字、注释、关键字全部走绿；
                字符串/数字/函数/字段常量/注解保留官方那套"少量互补色相"的结构。
"""
import colorsys
import json
import os
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(HERE, "..", "build", "ref")
sys.path.insert(0, HERE)
from palette import contrast, hex_to_rgb  # noqa: E402


def hsl(h, s, l):
    r, g, b = colorsys.hls_to_rgb((h % 360) / 360.0, l / 100.0, s / 100.0)
    return "#%02X%02X%02X" % tuple(round(c * 255) for c in (r, g, b))


def hls(h):
    r, g, b = [v / 255 for v in hex_to_rgb(h)]
    H, L, S = colorsys.rgb_to_hls(r, g, b)
    return H * 360, S * 100, L * 100


def solve(hue, sat, bg, target, lo=30.0, hi=90.0):
    """按目标对比度反解明度。"""
    best, bd = (lo + hi) / 2, 1e9
    l = lo
    while l <= hi + 1e-9:
        d = abs(contrast(hsl(hue, sat, l), bg) - target)
        if d < bd:
            best, bd = l, d
        l += 0.25
    return round(best, 2)


def hx(v):
    return ("#" + v) if v and len(v) == 6 else None


# ---------------------------------------------------------------------------
# 一、还原官方 Islands Dark
# ---------------------------------------------------------------------------
def resolve_tokens(path):
    """解析 theme json 的 colors：把 token 别名链一路解到十六进制。"""
    raw = json.load(open(path, encoding="utf-8"))["colors"]

    def res(k, depth=0):
        v = raw.get(k)
        if v is None or depth > 12:
            return None
        if isinstance(v, str) and v.startswith("#"):
            return v
        return res(v, depth + 1) if isinstance(v, str) else None

    return {k: res(k) for k in raw}, raw


def build_official():
    root = ET.parse(os.path.join(REF, "ide_official_schemes", "IslandSchemeDark.xml")).getroot()
    A = {}
    for o in root.find("attributes").findall("option"):
        val = o.find("value")
        if val is None:
            continue
        A[o.get("name")] = {x.get("name"): x.get("value") for x in val}
    C = {o.get("name"): o.get("value") for o in root.find("colors").findall("option")}
    tok, _ = resolve_tokens(os.path.join(REF, "ide2026", "themes", "islands",
                                         "ManyIslandsDark.theme.json"))
    fg = hx(A["TEXT"]["FOREGROUND"]) or "#bcbec4"
    bg = hx(A["TEXT"]["BACKGROUND"]) or "#191A1C"
    g = lambda k, d=None: hx(A.get(k, {}).get("FOREGROUND")) or d
    b = lambda k, d=None: hx(A.get(k, {}).get("BACKGROUND")) or d
    p = {
        "label": "官方 Islands Dark", "name": "Official Islands Dark",
        "bg_editor": bg, "bg_panel": tok.get("main-window-bg") or bg,
        "bg_raised": tok.get("layer-2-bg") or bg,
        "bg_gutter": bg, "bg_console": hx(C.get("CONSOLE_BACKGROUND_KEY")) or bg,
        "bg_folded": hx(C.get("FOLDED_TEXT_BORDER_COLOR")) or bg,
        "bg_caret_row": hx(C.get("CARET_ROW_COLOR")) or bg,
        "bg_selection": tok.get("selection-bg-active") or "#2A4371",
        "bg_search": b("SEARCH_RESULT_ATTRIBUTES") or "#2d543f",
        "bg_matched_brace": b("MATCHED_BRACE_ATTRIBUTES") or "#43454a",
        "bg_diff_add": hx(C.get("ADDED_LINES_COLOR")) or "#375239",
        "bg_diff_del": hx(C.get("DELETED_LINES_COLOR")) or "#5e3838",
        "bg_diff_mod": hx(C.get("MODIFIED_LINES_COLOR")) or "#34415e",
        "fg": fg, "fg_dim": tok.get("text-secondary") or fg,
        "fg_sel": tok.get("text-default") or fg, "fg_search": fg,
        "caret": hx(C.get("CARET_COLOR")) or fg,
        "line_numbers": hx(C.get("LINE_NUMBERS_COLOR")) or "#4b5059",
        "line_numbers_active": hx(C.get("LINE_NUMBER_ON_CARET_ROW_COLOR")) or fg,
        "tab_underline": "#8C9099",
        "indent_guide": hx(C.get("INDENT_GUIDE")) or "#323438",
        "right_margin": hx(C.get("RIGHT_MARGIN_COLOR")) or "#323438",
        "whitespace": hx(C.get("WHITESPACES")) or "#323438",
        "keyword": g("DEFAULT_KEYWORD"), "string": g("DEFAULT_STRING"),
        "escape": g("DEFAULT_VALID_STRING_ESCAPE"),
        "number": g("DEFAULT_NUMBER"),
        "constant": g("DEFAULT_CONSTANT"), "class_name": g("DEFAULT_CLASS_REFERENCE"),
        "interface_name": g("DEFAULT_CLASS_REFERENCE"),
        "enum_name": g("DEFAULT_CLASS_REFERENCE"),
        "type_param": g("DEFAULT_CLASS_REFERENCE"),
        "function": g("DEFAULT_FUNCTION_DECLARATION"),
        "function_call": g("DEFAULT_INSTANCE_METHOD"),
        "parameter": fg, "local_var": fg, "field": g("DEFAULT_INSTANCE_FIELD"),
        "static_field": g("DEFAULT_STATIC_FIELD"),
        "annotation": g("DEFAULT_METADATA"), "tag": g("DEFAULT_TAG", fg),
        # 官方把 Javadoc tag 单独定义成绿色（与注解橄榄不同色）
        "doc_tag": g("DEFAULT_DOC_COMMENT_TAG") or g("DEFAULT_METADATA"),
        "followed_link": g("FOLLOWED_HYPERLINK_ATTRIBUTES") or g("HYPERLINK_ATTRIBUTES"),
        "warning_stripe": g("WARNING_ATTRIBUTES") or "#f2c55c",
        "hint_current": g("INLINE_PARAMETER_HINT_CURRENT") or g("DEFAULT_CLASS_REFERENCE"),
        "grey_underline": g("DEFAULT_REASSIGNED_LOCAL_VARIABLE") or "#84868c",
        # 标尺要覆盖与本主题**同一批**状态块键，否则"比官方多出 0 对"是空转
        "bg_matched_brace": b("MATCHED_BRACE_ATTRIBUTES", "#2E3134"),
        "bg_identifier_caret": b("IDENTIFIER_UNDER_CARET_ATTRIBUTES", "#373b39"),
        "bg_identifier_write": b("WRITE_IDENTIFIER_UNDER_CARET_ATTRIBUTES", "#402f33"),
        "bg_execution_point": b("EXECUTIONPOINT_ATTRIBUTES", "#2a5091"),
        "bg_breakpoint": b("BREAKPOINT_ATTRIBUTES", "#40252b"),
        "bg_not_top_frame": b("NOT_TOP_FRAME_ATTRIBUTES", "#273552"),
        "bg_doc_code": b("DOC_CODE_INLINE", "#343539"),
        "bg_doc_code_block": b("DOC_CODE_BLOCK", "#26292c"),
        "bg_breadcrumb": b("BREADCRUMBS_CURRENT", "#2b2d30"),
        "bg_injected": b("INJECTED_LANGUAGE_FRAGMENT", "#293c40"),
        "bg_smart_cast": b("KOTLIN_SMART_CAST_RECEIVER", "#1a3b2d"),
        "bg_matched_tag": b("MATCHED_TAG_NAME", "#3f4045"),
        "bg_inlay_hint": b("INLINE_PARAMETER_HINT", "#393b40"),
        "bg_inlay_hint_current": b("INLINE_PARAMETER_HINT_CURRENT", "#35538f"),
        "bg_search": b("SEARCH_RESULT_ATTRIBUTES", "#114957"),
        "bg_search_current": b("TEXT_SEARCH_RESULT_ATTRIBUTES", "#114957"),
        "attr_name": g("DEFAULT_TAG", fg), "attr_value": g("DEFAULT_STRING"),
        "operator": g("DEFAULT_OPERATION_SIGN", fg),
        "brace": g("DEFAULT_BRACES", fg), "punctuation": g("DEFAULT_SEMICOLON", fg),
        "comment": g("DEFAULT_LINE_COMMENT"), "doc_comment": g("DEFAULT_DOC_COMMENT"),
        "error": g("UNMATCHED_BRACE_ATTRIBUTES") or "#f75464",
        "warning": g("WARNING_ATTRIBUTES") or "#cf8e6d",
        "info": g("INFORMATION_HINT") or fg,
        "todo": g("TODO_DEFAULT_ATTRIBUTES") or "#8bb33d",
        "deprecated": tok.get("text-secondary") or fg,
        "hyperlink": g("HYPERLINK_ATTRIBUTES") or "#548af7",
        "bookmark": g("TODO_DEFAULT_ATTRIBUTES") or "#8bb33d",
        "breakpoint": g("UNMATCHED_BRACE_ATTRIBUTES") or "#f75464",
    }
    # 控制台 ANSI：官方 <colors> 里有 CONSOLE_* 的直接用
    for name, key in [("black", "CONSOLE_BLACK"), ("red", "CONSOLE_RED"),
                      ("green", "CONSOLE_GREEN"), ("yellow", "CONSOLE_YELLOW"),
                      ("blue", "CONSOLE_BLUE"), ("magenta", "CONSOLE_MAGENTA"),
                      ("cyan", "CONSOLE_CYAN"), ("gray", "CONSOLE_GRAY"),
                      ("darkgray", "CONSOLE_DARKGRAY"), ("lightgray", "CONSOLE_LIGHTGRAY"),
                      ("lightred", "CONSOLE_LIGHTRED"), ("lightgreen", "CONSOLE_LIGHTGREEN"),
                      ("lightyellow", "CONSOLE_LIGHTYELLOW"), ("lightblue", "CONSOLE_LIGHTBLUE"),
                      ("lightmagenta", "CONSOLE_LIGHTMAGENTA"), ("lightcyan", "CONSOLE_LIGHTCYAN"),
                      ("white", "CONSOLE_WHITE")]:
        p["con_" + name] = hx(C.get(key)) or p["fg"]
    for k in list(p):
        if p[k] is None:
            p[k] = p["fg"]
    return p


# ---------------------------------------------------------------------------
# 二、绿色版：结构照官方，色相换成绿系
#    (色相, 饱和度, 目标对比度)  —— 目标对比度直接取自官方实测值
# ---------------------------------------------------------------------------
BG = "#1F302B"          # A 与 C 的中点（用户选定的背景位置）
SPEC = {
    # 中性主体：官方用 #bcbec4 一个色覆盖了 16 个键，这里换成绿灰
    "neutral":   (148, 9, 9.4),
    # 主题身份：关键字用绿（官方是橙）
    "keyword":   (132, 48, 6.6),
    # 字符串改琥珀（官方字符串是绿、关键字是橙，这里把两者的冷暖对调）
    "string":    (38, 48, 6.4),
    "escape":    (38, 58, 6.6),
    "number":    (186, 58, 6.4),
    "constant":  (310, 38, 5.9),
    "function":  (212, 70, 6.9),
    "type_param": (200, 40, 6.6),
    "annotation": (58, 38, 7.0),
    "comment":   (150, 8, 4.3),
    "doc_comment": (150, 15, 4.1),
    "todo":      (80, 46, 7.0),
    "error":     (354, 65, 5.3),
    "warning":   (45, 52, 7.0),
    "hyperlink": (215, 65, 5.3),
}


def build_green():
    # 明度上下限照官方区间：重点色 44%~68%（官方 44~65），注释更低
    # 中性正文要亮（照官方 #bcbec4 的 9.4:1）；重点色偏深；注释最暗
    CLAMP = {"neutral": (72, 90), "comment": (44, 58), "doc_comment": (42, 56)}
    c = {}
    for k, (h, sa, t) in SPEC.items():
        lo, hi = CLAMP.get(k, (44.0, 70.0))
        c[k] = hsl(h, sa, solve(h, sa, BG, t, lo, hi))
    neutral = c["neutral"]
    p = {
        "label": "绿色版（照官方结构）", "name": "Green Eye Official-style",
        "bg_editor": BG, "bg_panel": "#1A2621", "bg_raised": "#25382F",
        "bg_gutter": BG, "bg_console": "#182420",
        "bg_folded": "#243528", "bg_caret_row": "#243328",
        "bg_selection": "#2F4A3C", "bg_search": "#2D543F",
        "bg_matched_brace": "#3A4740",
        "bg_diff_add": "#2A4433", "bg_diff_del": "#4A3232", "bg_diff_mod": "#2A3A48",
        "fg": neutral, "fg_dim": "#93A79A", "fg_sel": "#E4EDE6", "fg_search": "#E4EDE6",
        "caret": "#93A79A",
        "line_numbers": "#536057", "line_numbers_active": neutral,
        "indent_guide": "#31423A", "right_margin": "#31423A", "whitespace": "#2B3C34",
        "tab_underline": "#5C7A66",
        "keyword": c["keyword"], "string": c["string"], "escape": c["escape"],
        "number": c["number"], "constant": c["constant"],
        # 官方把类引用、标签也当中性色，这里照做
        "class_name": neutral, "interface_name": neutral, "enum_name": neutral,
        "type_param": c["type_param"],
        "function": c["function"], "function_call": c["function"],
        "parameter": neutral, "local_var": neutral, "field": c["constant"],
        "static_field": c["constant"], "annotation": c["annotation"],
        "tag": neutral, "attr_name": neutral, "attr_value": c["string"],
        "operator": neutral, "brace": neutral, "punctuation": neutral,
        "comment": c["comment"], "doc_comment": c["doc_comment"],
        "error": c["error"], "warning": c["warning"], "info": c["constant"],
        "todo": c["todo"], "deprecated": "#93A79A", "hyperlink": c["hyperlink"],
        "bookmark": c["todo"], "breakpoint": c["error"],
    }
    p.update({
        "con_black": p["bg_panel"], "con_red": c["error"], "con_green": c["keyword"],
        "con_yellow": c["warning"], "con_blue": c["function"],
        "con_magenta": c["constant"], "con_cyan": c["number"],
        "con_gray": p["fg_dim"], "con_darkgray": p["line_numbers"],
        "con_lightgray": p["fg"], "con_lightred": "#f97b7b",
        "con_lightgreen": "#8fd39a", "con_lightyellow": "#d9c07a",
        "con_lightblue": "#7fb2f0", "con_lightmagenta": "#d99cc9",
        "con_lightcyan": "#5fc4d0", "con_white": "#e4ede6",
    })
    return p


# ===========================================================================
# V3：在官方结构基础上解决两个具体问题
#   1) 关键字"太亮的绿"：根因是绿色主导 WCAG 亮度，要 6.4:1 就必须亮。
#      官方自己的绿其实是**低饱和**的（字符串 #6aab73 只有 28% 饱和）。
#      所以 V3 改成"降饱和、不降亮度"，关键字饱和度压到 34%。
#   2) 整体不够统一：V3 把所有重点色的饱和度收进 30%~48%、
#      明度收进 50%~68% 的窄带，避免有的艳有的灰。
#   types_colored=False → 类型/类名保持中性（官方原味）
#   types_colored=True  → 类型/类名给一个柔和的淡金
# ===========================================================================
SPEC_V3 = {
    "neutral":     (148, 7, 9.0, (74, 88)),
    "keyword":     (130, 34, 5.6, (48, 60)),
    "string":      (40, 38, 6.2, (54, 66)),
    "escape":      (32, 46, 6.2, (54, 66)),
    "number":      (186, 40, 5.8, (50, 62)),
    "constant":    (310, 30, 5.6, (56, 68)),
    "function":    (212, 44, 6.0, (56, 68)),
    "type_param":  (200, 32, 5.8, (54, 66)),
    "annotation":  (58, 32, 6.4, (52, 64)),
    "comment":     (152, 9, 4.3, (46, 56)),
    "doc_comment": (152, 13, 4.1, (44, 54)),
    "todo":        (82, 34, 6.0, (52, 62)),
    "error":       (354, 48, 4.9, (56, 68)),
    "warning":     (45, 38, 6.4, (54, 66)),
    "hyperlink":   (215, 42, 5.8, (54, 66)),
}
TYPE_GOLD = (48, 36, 6.3, (56, 66))


def build_v3(types_colored=False):
    c = {}
    for k, (h, sa, t, (lo, hi)) in SPEC_V3.items():
        c[k] = hsl(h, sa, solve(h, sa, BG, t, lo, hi))
    if types_colored:
        c["class_name"] = hsl(*TYPE_GOLD[:2], solve(TYPE_GOLD[0], TYPE_GOLD[1], BG,
                                                    TYPE_GOLD[2], *TYPE_GOLD[3]))
    else:
        c["class_name"] = c["neutral"]
    neutral = c["neutral"]
    p = {
        "label": "V3 类型中性" if not types_colored else "V3 类型淡金",
        "name": "Green Eye V3",
        "bg_editor": BG, "bg_panel": "#1A2621", "bg_raised": "#25382F",
        "bg_gutter": BG, "bg_console": "#182420",
        "bg_folded": "#243528", "bg_caret_row": "#243328",
        "bg_selection": "#2F4A3C", "bg_search": "#2D543F",
        "bg_matched_brace": "#3A4740",
        "bg_diff_add": "#2A4433", "bg_diff_del": "#4A3232", "bg_diff_mod": "#2A3A48",
        "fg": neutral, "fg_dim": "#8FA398", "fg_sel": "#E4EDE6", "fg_search": "#E4EDE6",
        "caret": "#8FA398", "line_numbers": "#536057",
        "line_numbers_active": neutral, "tab_underline": "#4E6B58",
        "indent_guide": "#31423A", "right_margin": "#31423A", "whitespace": "#2B3C34",
        "keyword": c["keyword"], "string": c["string"], "escape": c["escape"],
        "number": c["number"], "constant": c["constant"],
        "class_name": c["class_name"], "interface_name": c["class_name"],
        "enum_name": c["class_name"], "type_param": c["type_param"],
        "function": c["function"], "function_call": c["function"],
        "parameter": neutral, "local_var": neutral, "field": c["constant"],
        "static_field": c["constant"], "annotation": c["annotation"],
        "tag": neutral, "attr_name": neutral, "attr_value": c["string"],
        "operator": neutral, "brace": neutral, "punctuation": neutral,
        "comment": c["comment"], "doc_comment": c["doc_comment"],
        "error": c["error"], "warning": c["warning"], "info": c["constant"],
        "todo": c["todo"], "deprecated": "#8FA398", "hyperlink": c["hyperlink"],
        "bookmark": c["todo"], "breakpoint": c["error"],
    }
    p.update({
        "con_black": p["bg_panel"], "con_red": c["error"], "con_green": c["keyword"],
        "con_yellow": c["warning"], "con_blue": c["function"],
        "con_magenta": c["constant"], "con_cyan": c["number"],
        "con_gray": p["fg_dim"], "con_darkgray": p["line_numbers"],
        "con_lightgray": p["fg"], "con_lightred": _light(c["error"], 10),
        "con_lightgreen": _light(c["keyword"], 9), "con_lightyellow": _light(c["warning"], 9),
        "con_lightblue": _light(c["function"], 9), "con_lightmagenta": _light(c["constant"], 9),
        "con_lightcyan": _light(c["number"], 9), "con_white": p["fg_sel"],
    })
    return p


def _light(hexcolor, d):
    r, g, b = [v / 255 for v in hex_to_rgb(hexcolor)]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return hsl(h * 360, s * 100, min(96.0, l * 100 + d))


V3A = build_v3(False)
V3B = build_v3(True)


# ===========================================================================
# V4：绿皮官方 —— 代码颜色直接沿用官方色相，只把"皮肤"换成绿色
#   理由：官方是"中性背景 + 高饱和重点色"，重点色靠饱和度跳出背景。
#   V3 把所有重点色都去饱和了，配上绿背景就整体发闷。
#   V4 保留官方每个语义的**色相与饱和度**，只把明度按官方的**对比度**重解，
#   以适配稍浅的绿色背景（官方原始背景是 #191A1C）。
#   绿色身份改由背景 / 中性文字 / 注释 / 界面边框承载。
# ===========================================================================
OFFICIAL_TARGET = {          # 语义 -> 官方实测对比度（在 #191A1C 上）
    "fg": 9.37, "keyword": 6.42, "string": 6.37, "escape": 6.42, "number": 6.38,
    "function": 7.05, "constant": 5.87, "annotation": 7.58, "comment": 4.27,
    "doc_comment": 4.06, "todo": 7.14, "error": 5.31, "hyperlink": 5.27,
    "warning": 6.40,
}


def build_v4(types_colored=False):
    c = {}
    # "皮肤"部分（正文/注释）改用绿色色相，重点色保留官方色相
    SKIN = {"fg": 148, "comment": 150}
    for k, target in OFFICIAL_TARGET.items():
        src = OFFICIAL[k]
        H, S, _ = hls(src)
        if k in SKIN:
            H, S = SKIN[k], 7.0 if k == "fg" else 8.0
        c[k] = hsl(H, S, solve(H, S, BG, target, 34, 88))
    # 官方把类型/类名/标签/括号/运算符/参数/局部变量都当中性色
    for k in ("class_name", "interface_name", "enum_name", "type_param",
              "parameter", "local_var", "operator", "brace", "punctuation",
              "tag", "attr_name"):
        c.setdefault(k, c["fg"])
    # 类型/类名：官方原味是中性色；可选给一个柔和的淡金
    type_color = c["fg"]
    if types_colored:
        type_color = hsl(48, 34, solve(48, 34, BG, 6.0, 56, 66))
    for k in ("class_name", "interface_name", "enum_name", "type_param"):
        c[k] = type_color
    p = {
        "label": "V4 类型淡金" if types_colored else "V4 类型中性",
        "name": "Green Eye V4",
        "bg_editor": BG, "bg_panel": "#1A2621", "bg_raised": "#25382F",
        "bg_gutter": BG, "bg_console": "#182420",
        "bg_folded": "#243528", "bg_caret_row": "#243328",
        "bg_selection": "#2F4A3C", "bg_search": "#2D543F",
        "bg_matched_brace": "#3A4740",
        "bg_diff_add": "#2A4433", "bg_diff_del": "#4A3232", "bg_diff_mod": "#2A3A48",
        "fg": c["fg"], "fg_dim": "#8FA398", "fg_sel": "#E4EDE6", "fg_search": "#E4EDE6",
        "caret": "#8FA398", "line_numbers": "#536057",
        "line_numbers_active": c["fg"], "tab_underline": "#4E6B58",
        "indent_guide": "#31423A", "right_margin": "#31423A", "whitespace": "#2B3C34",
        "keyword": c["keyword"], "string": c["string"], "escape": c["escape"],
        "number": c["number"], "constant": c["constant"],
        "class_name": c["class_name"], "interface_name": c["class_name"],
        "enum_name": c["class_name"], "type_param": c["type_param"],
        "function": c["function"], "function_call": c["function"],
        "parameter": c["fg"], "local_var": c["fg"], "field": c["constant"],
        "static_field": c["constant"], "annotation": c["annotation"],
        "tag": c["fg"], "attr_name": c["fg"], "attr_value": c["string"],
        "operator": c["fg"], "brace": c["fg"], "punctuation": c["fg"],
        "comment": c["comment"], "doc_comment": c["doc_comment"],
        "error": c["error"], "warning": c["warning"], "info": c["constant"],
        "todo": c["todo"], "deprecated": "#8FA398", "hyperlink": c["hyperlink"],
        "bookmark": c["todo"], "breakpoint": c["error"],
    }
    p.update({
        "con_black": p["bg_panel"], "con_red": p["error"], "con_green": p["keyword"],
        "con_yellow": p["warning"], "con_blue": c["function"],
        "con_magenta": c["constant"], "con_cyan": c["number"],
        "con_gray": p["fg_dim"], "con_darkgray": p["line_numbers"],
        "con_lightgray": p["fg"], "con_lightred": _light(p["error"], 10),
        "con_lightgreen": _light(p["keyword"], 9), "con_lightyellow": _light(p["warning"], 9),
        "con_lightblue": _light(c["function"], 9), "con_lightmagenta": _light(c["constant"], 9),
        "con_lightcyan": _light(c["number"], 9), "con_white": p["fg_sel"],
    })
    return p



OFFICIAL = build_official()
GREEN = build_green()

if __name__ == "__main__":
    print("官方 Islands Dark 还原结果（关键项）：")
    for k in ("bg_editor", "bg_panel", "bg_raised", "bg_selection", "bg_caret_row",
              "fg", "comment", "keyword", "string", "number", "function",
              "constant", "annotation", "class_name", "tag", "operator",
              "line_numbers", "indent_guide", "caret"):
        print("   %-14s %s" % (k, OFFICIAL[k]))
    print()
    print("绿色版（照官方结构 + 目标对比度反解）：")
    print("   %-12s %-9s %6s %5s %5s %7s" % ("语义", "色值", "色相", "饱和", "明度", "对比"))
    for k in ("fg", "comment", "doc_comment", "keyword", "string", "number",
              "function", "constant", "annotation", "type_param", "todo",
              "error", "warning", "hyperlink"):
        H, S, L = hls(GREEN[k])
        print("   %-12s %-9s %5.0f° %4.0f%% %4.0f%% %6.2f:1"
              % (k, GREEN[k], H, S, L, contrast(GREEN[k], GREEN["bg_editor"])))
    print()
    print("背景 %s  正文对比 %.2f:1" % (GREEN["bg_editor"], contrast(GREEN["fg"], GREEN["bg_editor"])))


V4 = build_v4(False)
V4B = build_v4(True)
