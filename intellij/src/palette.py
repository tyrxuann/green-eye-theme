#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Green Eye 正式调色板（深色「松林」）。

设计来源与依据
--------------
结构照 JetBrains 官方 **Islands Dark**（从安装包内的官方方案原文实测而来），
每个语义的**色相与饱和度直接沿用官方**，只把**明度按官方的对比度重新求解**
以适配绿色背景 —— 官方原始背景是 `#191A1C`（近黑），本主题是 `#1F302B`（墨绿）。

官方规律（本主题遵守）：
  1. 绝大多数代码是**同一个中性色**：标识符、类名引用、括号、分号、运算符、标签
     官方全用 `#bcbec4` 一个色（159 个键里只有 76 种颜色，该色被复用 16 次）。
  2. **重点色比正文暗**：中性正文 9.37:1，重点色只有 5.9~6.9:1，注释 4.27:1。
  3. **重点色偏深偏浓**：明度 44%~65%、饱和度 28%~91%，靠饱和度跳出背景而不是靠亮度。
  4. **关键字不加粗**；只有静态成员/常量/文档注释/TODO 用斜体（样式在 gen_icls.py）。

"绿色身份"由**皮肤**承载，不由关键字承载：
    背景 `#1F302B` / 面板 / 浮层 / 选中 / 正文 `#CBD2CF` / 注释 / 缩进参考线
代码里的绿主要由**字符串** `#89BC90`（Java 里到处都是）体现。

对照表（官方 → 本主题，色相/饱和度一致，仅明度适配）：
    关键字    #cf8e6d 橙 S51  → #D9A58B 橙 S51     6.40:1
    字符串    #6aab73 绿 S28  → #89BC90 绿 S28     6.37:1
    数字      #2aacb8 青 S63  → #2FC1CF 青 S63     6.37:1
    函数      #56a8f5 蓝 S89  → #81BEF8 蓝 S89     7.03:1
    字段/常量  #c77dbb 紫 S40  → #D296C8 紫 S40     5.90:1
    注解      #b3ae60 橄榄 S35 → #C6C288 橄榄 S35   7.57:1
    错误      #f75464 红 S91  → #F97884 红 S91     5.31:1
    注释      #7a7e85 灰      → #82958C 绿灰       4.37:1
    正文      #bcbec4 中性    → #CBD2CF 绿灰       9.01:1
"""
import os
import colorsys as _colorsys


DARK = {
    "label": "松林",
    "name": "Green Eye Dark",
    "parent": "Darcula",
    "dark": True,
    "bg_editor": "#1F3027",
    "bg_panel": "#1B211D",        # S≈10%：与编辑器(S22%)形成色度梯度，"绿岛"才成立
    "bg_raised": "#2E4739",
    "bg_gutter": "#1F3027",
    "bg_console": "#1B211D",      # 与面板同底（官方控制台底也等于基色）
    "bg_folded_text": "#35523F",  # 折叠片段：官方 1.55×，本主题给独立比(caret row 仍保持极淡)
    "bg_folded": "#283D32",
    "bg_caret_row": "#283D32",
    "bg_selection": "#335662",   # 松林保留青蓝选中态，避免与调试背景撞色
    "bg_search": "#2D5440",      # 绿相 H150，与 diff 新增(H131)拉开
    "search_border": "#57966A",
    "search_stripe": "#C9A94E",        # 查找命中的滚动条条纹
    "search_current_stripe": "#E0C24F",   # 仅 UI 层使用（编辑器层改用两档背景）
    "bg_identifier_caret": "#3E4A50",   # 光标标识符：官方有底色(#373b39)+下划线，我改成绿灰族
    "bg_identifier_write": "#45383A",   # 写入态另给一色（官方 #402f33），与读取态区分
    "bg_execution_point": "#2A5091",    # 调试器当前执行行（官方同值）
    "bg_breakpoint": "#5A3E42",         # 断点行（官方 #40252b 的绿底适配）
    "bg_not_top_frame": "#33445F",      # 调用栈非栈顶帧（官方 #273552）
    "bg_doc_code": "#454948",           # Javadoc 内联代码（官方 #343539）
    "bg_doc_code_block": "#1B2620",     # Javadoc 代码块（官方 #26292c）
    "bg_breadcrumb": "#2A3A32",         # 面包屑当前/悬停（官方 #2b2d30）
    "bg_injected": "#304C52",           # 注入语言片段（官方 #293c40）
    "bg_smart_cast": "#366048",         # Kotlin smart cast（官方 #1a3b2d）
    "bg_matched_tag": "#4A504B",        # XML 配对标签（官方 #3f4045）
    "bg_matched_brace": "#565A50",   # 暖中性暗框（匹配括号，低频）
    "bg_inlay_hint": "#2E4739",
    "bg_inlay_hint_highlighted": "#37503F",  # 高亮参数提示：官方 1.82×，单独一档
    "bg_inlay_hint_current": "#356875",  # 当前参数提示：官方换色相不换明度（蓝 #35538f），本主题用青 H192
    "bg_search_current": "#3C6B4A",    # 当前匹配：靠背景区分（官方也不用描边）
    "bg_diff_add": "#2E4A2A",
    "bg_diff_del": "#673838",
    "bg_diff_mod": "#2E4059",
    "accent": "#396F54",          # 品牌按钮/焦点环：与正文配合，不抢语法色
    "accent_hover": "#468563",
    "ui_base": "#171D1A",         # IDEA 工作台底：比编辑器更中性，避免整屏发绿
    "ui_surface": "#232E29",     # 控件/弹窗表面
    "ui_hover": "#2A3933",       # 悬停与次级强调
    "border": "#3B5847",        # 只给浮层（弹窗/对话框/提示）用
    "separator": "#2C3D35",     # 窗口内发丝线（面板/工具窗之间）
    "indent_guide": "#2C3D35",
    "right_margin": "#293A31",
    "whitespace": "#33443A",     # 与缩进线区分
    "tab_underline": "#4E6B58",
    "fg": "#D1D0CA",
    "fg_dim": "#908D82",
    "fg_sel": "#E8E6DC",
    "fg_search": "#EDEBE2",
    "caret": "#E3E2DE",
    "line_numbers": "#61605A",
    "line_numbers_active": "#D1D0CA",
    "keyword": "#D9A58B",
    "string": "#8BBD84",
    "attr_value": "#89BC90",
    "escape": "#D9A58B",
    "number": "#2FC1CF",
    "constant": "#D296C8",
    "static_field": "#D296C8",
    "field": "#D296C8",
    "info": "#85BDF1",
    "function": "#85BDF1",
    "function_call": "#85BDF1",
    "annotation": "#B8B476",
    "doc_tag": "#85B295",       # Javadoc 的 @param/@return：官方让它留在绿色注释家族（不是注解橄榄）
    "grey_underline": "#7A7D77",  # "重新赋值/可变"这类中性灰下划线
    "hint_current": "#CACEE8",   # 坐在当前提示芯片上，按**芯片底**反解（4.0:1），按编辑器底会只有 2.05:1
    "implicit_ec": "#9E6294",     # 隐式匿名类参数的下划线色（比其前景暗一档）
    "vcs_conflict": "#C96A6F",   # 合并冲突：官方给红（#DE6A66），不能降级成琥珀
    "vcs_deleted": "#8A8F88",    # 已删除：官方给中性灰（#6F737A），删一堆文件时不该满屏红
    "doc_link": "#4FA3B8",       # Javadoc {@link}：官方给 teal（#3887A1），与超链接分开
    "bg_error_hint": "#5A2E2E",  # 官方这个键是背景色（暗红 #402929）
    "info_stripe": "#8A7548",    # 官方 #857042
    "typo_stripe": "#7FC08A",    # 官方 #7ec482
    "removal_stripe": "#E86A72", # 官方 #f75464
    "error": "#F97884",
    "breakpoint": "#F97884",
    "warning": "#B8B476",          # 不自造色相：与注解同色（官方也未定义警告前景）
    "warning_stripe": "#E8D48A",   # 警告的波浪线/条纹色，比前景明显更亮
    "todo": "#A7C73D",
    "bookmark": "#A7C73D",
    "hyperlink": "#78A89D",
    "followed_link": "#9ABBB2",
    "class_name": "#D1D0CA",
    "interface_name": "#D1D0CA",
    "enum_name": "#D1D0CA",
    "type_param": "#D1D0CA",
    "parameter": "#D1D0CA",
    "local_var": "#D1D0CA",
    "operator": "#D1D0CA",
    "brace": "#D1D0CA",
    "punctuation": "#D1D0CA",
    "tag": "#D1D0CA",
    "attr_name": "#D1D0CA",
    "comment": "#93918A",   # H48：与正文同为暖中性文本层（暖中性=文本 / 绿=内容 / 其余=语义）
    "doc_comment": "#658C7C",
    "deprecated": "#908D82",
    "con_black": "#18241E",
    "con_red": "#F97884",
    "con_green": "#89BC90",
    "con_yellow": "#D8C685",
    "con_blue": "#85BDF1",
    "con_magenta": "#D296C8",
    "con_cyan": "#2FC1CF",
    "con_gray": "#908D82",
    "con_darkgray": "#62605A",
    "con_lightgray": "#D1D0CA",
    "con_lightred": "#FBA9B0",
    "con_lightgreen": "#A8D8AE",
    "con_lightyellow": "#E8DCA4",
    "con_lightblue": "#ACD4FA",
    "con_lightmagenta": "#E0B6D9",
    "con_lightcyan": "#54CDD8",
    "con_white": "#E8E6DC",
}

PALETTES = {"dark": DARK}


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    return "#%02X%02X%02X" % tuple(max(0, min(255, int(round(c)))) for c in rgb)


def _lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def rel_luminance(h):
    r, g, b = hex_to_rgb(h)
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def contrast(fg, bg):
    a, b = rel_luminance(fg), rel_luminance(bg)
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)


def scheme_stem(pal):
    """方案在磁盘上的文件名主干：Green-Eye-Dark / Green-Eye-Mineral。"""
    return pal["name"].split(" (")[0].replace(" ", "-")


def icls_path(pal, themes_dir=None):
    themes_dir = themes_dir or os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                            "..", "themes")
    return os.path.join(themes_dir, scheme_stem(pal) + ".icls")


def hsl_hex(h, s, l):
    """(色相°, 饱和度%, 明度%) -> #RRGGBB。用于按"色相+饱和度+目标对比度"反解色值。"""
    import colorsys as _cs
    r, g, b = _cs.hls_to_rgb((h % 360) / 360.0, l / 100.0, s / 100.0)
    return rgb_to_hex([r * 255, g * 255, b * 255])


def mix(h1, h2, t):
    a, b = hex_to_rgb(h1), hex_to_rgb(h2)
    return rgb_to_hex([a[i] + (b[i] - a[i]) * t for i in range(3)])


# ===========================================================================
# 第二款主题：Green Eye Mineral「矿彩」
# ---------------------------------------------------------------------------
# 设计语言：**暖矿结构 + 冷矿内容**（与「松林」是类别差别，不是色阶差别）
#
#   结构层（暖极）  关键字 琥珀 H42 → 常量/字段 赭石 H20 → 注解/警告 玫瑰 H338
#                   → TODO 芥黄 H62
#   内容层（冷极）  字符串 冰青 H196 → 函数 玉青 H168 → 数字 紫晶 H272
#                   → doc_link 兰紫 H300
#   注释层（冷石）  comment H170 / doc_comment H158 / doc_tag H140
#   正文层          暖中性墨 H50（彩色只留给语义）
#
# 与「松林」的关键差别不是"再挪一点色相"，而是**角色互换**：
#   松林 = 绿串 / 青数 / 电光蓝函数（整体暖黄绿）
#   矿彩 = 冰青串 / 紫晶数 / 玉青函数（暖结构 + 冷内容）
# 只挪色相做不到这一点 —— 冷极 180–300° 只有 120°，要塞下 5 个成员且两两 ΔE≥12
# 最多只能塞 3 个。这是第 2 轮评审给出的数学约束，也是"变体 vs 类别差别"的分界。
#
# 对比度是设计约束：每个色由 (色相, 饱和度, 目标对比度) 反解明度。
# 身份达标由 check_identity.py 守：novelty ≥15、频率加权 ≥16、主力 ≥5/8。
#
# 与官方的偏离：结构层/内容层的色相分配是原创（官方是橙关键字/绿串/青数/蓝函数/紫常量）；
# 装饰编码（EFFECT_TYPE/EFFECT_COLOR/BACKGROUND/FONT_TYPE）仍逐键对照官方，
# 由 check_attribute_parity.py 的 9 条规则守着。
# ===========================================================================

MINERAL_SPEC = {
    # ---- 文本层：暖中性墨（彩色留给语义） ----
    "fg":                    (50,  7, 9.00),
    "fg_dim":                (50,  6, 4.20),
    "caret":                 (50,  8, 10.73),
    "line_numbers":          (50,  4, 2.20),
    "deprecated":            (50,  6, 4.20),
    "grey_underline":        (50,  3, 3.35),
    # ---- 注释层：冷石色 ----
    "comment":               (170, 6, 4.35),
    "doc_comment":           (158, 24, 3.70),
    # ---- 暖极：语言结构 ----
    "keyword":               (42, 55, 7.40),   # 与松林的关键字拉开更多身份裕度
    "escape":                (42, 55, 6.60),
    "annotation":            (338, 40, 6.60),
    "warning":               (338, 40, 6.60),
    # 常量压到 4.20:1：既与关键字拉开，也让红绿色盲下与"错误"可区分（2.2 → 7.5）
    "constant":              (20, 34, 4.20),
    "todo":                  (62, 48, 7.00),
    "bookmark":              (62, 48, 7.00),
    "warning_stripe":        (48, 70, 9.40),
    "removal_stripe":        (358, 70, 4.50),
    "vcs_conflict":          (358, 50, 4.20),
    "info_stripe":           (38, 35, 3.20),
    # ---- 冷极：数据 ----
    "string":                (196, 30, 6.60),   # 冰青：内容层整体移到冷极
    "attr_value":            (196, 30, 6.60),
    "number":                (272, 42, 6.40),   # 紫晶
    "function":              (168, 50, 6.98),   # 玉青
    "info":                  (168, 50, 6.98),
    # Javadoc 标签：放进"注释层"（苔石族）而不是数据层，避免与数字撞色
    "doc_tag":               (140, 14, 6.90),
    "hyperlink":             (168, 18, 4.90),
    "followed_link":         (168, 14, 5.60),
    "hint_current":          (232, 60, 4.60),
    "implicit_ec":           (12, 30, 3.60),
    "doc_link":              (168, 14, 4.60),   # UI 链接与文档链接统一为灰青色
    "typo_stripe":           (130, 35, 6.50),
    "vcs_deleted":           (100, 4, 4.20),
    # ---- 语义状态 ----
    "error":                 (358, 70, 5.40),
    "breakpoint":            (358, 70, 5.40),
}
# 语义别名（与「松林」同样的一色多槽，保证同类 token 同色）
# 注意：ANSI 的 con_* **不在这里**。它们由显式的 (色相,饱和度,对比度) 生成，
# 因为控制台语义（green 要是绿、blue 要是蓝）不能别名到语法 token ——
# 内容层一换色相，别名就会把 con_magenta 变成土黄色、con_blue 变成玉青。
MINERAL_ALIAS = {
    "line_numbers_active": "fg",
    "static_field": "constant", "field": "constant",
    "con_white": "fg", "con_lightgray": "fg",
    "con_red": "error", "con_gray": "fg_dim", "con_darkgray": "line_numbers",
    "function_call": "function",
    "class_name": "fg", "interface_name": "fg", "enum_name": "fg",
    "type_param": "fg", "parameter": "fg", "local_var": "fg",
    "operator": "fg", "brace": "fg", "punctuation": "fg",
    "tag": "fg", "attr_name": "fg",
}
# 背景 / 结构色：同样由 (色相, 饱和度, 对编辑器底的对比度) 反解
MINERAL_BG = {
    "bg_editor":             "#1F3027",   # ★ 与「松林」同一块地：这是用户指定的中心
    "bg_gutter":             None,        # = bg_editor
    "bg_panel":              (158, 11, 1.18, "dark"),
    "bg_console":            None,        # = bg_panel
    "bg_raised":             (155, 20, 1.37),
    "bg_inlay_hint":         None,        # = bg_raised
    "bg_caret_row":          (150, 19, 1.19),
    "bg_folded":             None,        # = bg_caret_row
    "bg_folded_text":        (152, 20, 1.61),
    "bg_selection":          (150, 24, 1.75),
    "bg_search":             (48, 42, 1.70),
    "bg_search_current":     (48, 48, 2.35),
    "search_border":         (48, 55, 3.90),
    "search_stripe":         (48, 58, 6.10),
    "search_current_stripe": (48, 62, 7.60),
    "bg_matched_brace":      (60, 6, 1.90),
    "bg_identifier_caret":   (205, 13, 1.52),
    "bg_identifier_write":   (350, 11, 1.24),
    "bg_execution_point":    (196, 62, 1.76),
    "bg_breakpoint":         (358, 20, 1.46),
    "bg_not_top_frame":      (242, 42, 1.22),   # 与 diff 修改行(H224)分开
    "bg_doc_code":           (165, 3, 1.52),
    "bg_doc_code_block":     (150, 15, 1.12, "dark"),
    "bg_breadcrumb":         (152, 15, 1.16),
    "bg_injected":           (190, 26, 1.51),
    "bg_smart_cast":         (285, 30, 1.41),   # 紫水晶：与 diff 新增行(H122)彻底分开
    "bg_matched_tag":        (100, 4, 1.68),
    "bg_inlay_hint_highlighted": (152, 18, 1.58),
    "bg_inlay_hint_current": (196, 38, 2.24),
    "bg_diff_add":           (122, 32, 1.41),
    "bg_diff_del":           (358, 30, 1.46),
    "bg_diff_mod":           (224, 32, 1.32),
    "bg_error_hint":         (358, 32, 1.23),
    "border":                (150, 20, 1.77),
    "separator":             (152, 16, 1.21),
    "indent_guide":          None,        # = separator
    "right_margin":          (150, 17, 1.15),
    "whitespace":            (148, 14, 1.34),
    "tab_underline":         (145, 16, 2.36),
}


def _spec_hex(h, s, bg, target, mode="light", lo=6.0, hi=92.0):
    """由 (色相, 饱和度, 目标对比度) 反解明度 —— 对比度因此是设计约束。

    mode 控制解在哪一侧：对比度是对称量，不约束方向会解出"比底色更暗"的色。
      light = 高亮族（当前行/选中/查找/提示芯片/缩进线…）必须比底色亮
      dark  = 凹陷族（面板/控制台/文档代码块）允许比底色暗
    """
    _, _, base_l = _rgb_to_hsl(hex_to_rgb(bg)) if False else (0, 0, _l_of(bg))
    lo2 = max(lo, base_l + 0.4) if mode == "light" else lo
    hi2 = base_l - 0.4 if mode == "dark" else hi
    if hi2 <= lo2:                      # 目标对比度在指定方向达不到时，退回全区间
        lo2, hi2 = lo, hi
    best, bd, l = (lo2 + hi2) / 2, 1e9, lo2
    while l <= hi2 + 1e-9:
        c = hsl_hex(h, s, l)
        d = abs(contrast(c, bg) - target)
        if d < bd:
            best, bd = l, d
        l += 0.2
    return hsl_hex(h, s, round(best, 2))


def _l_of(h):
    """HSL 意义上的明度（用于判断"更亮/更暗"）。"""
    import colorsys as _cs
    r, g, b = [v / 255 for v in hex_to_rgb(h)]
    return _cs.rgb_to_hls(r, g, b)[1] * 100


def build_mineral():
    bg = MINERAL_BG["bg_editor"]
    p = {"label": "矿彩", "name": "Green Eye Mineral", "parent": "Darcula", "dark": True}
    for k, (h, s, t) in MINERAL_SPEC.items():
        p[k] = _spec_hex(h, s, bg, t)
    for k, v in MINERAL_BG.items():
        if isinstance(v, str):
            p[k] = v
        elif v:
            mode = v[3] if len(v) > 3 else "light"
            p[k] = _spec_hex(v[0], v[1], bg, v[2], mode)
    # 结构色别名
    p["bg_gutter"] = p["bg_editor"]
    p["bg_console"] = p["bg_panel"]
    p["bg_inlay_hint"] = p["bg_raised"]
    p["bg_folded"] = p["bg_caret_row"]
    p["indent_guide"] = p["separator"]
    # ANSI 亮色（控制台需要 16 色，语义必须正确）
    # ANSI 16 色：**语义绑定**（green 必须看着是绿、cyan 是青、blue 是蓝、magenta 是品红），
    # 不能别名到语法 token —— 否则内容层一换色相，控制台语义就错
    # （实测：别名时 con_magenta 会变成土黄色）
    for k, (h, s, t) in {"con_green": (135, 32, 6.50), "con_cyan": (188, 45, 6.40),
                         "con_blue": (215, 50, 6.98), "con_magenta": (300, 40, 6.60),
                         "con_lightred": (358, 70, 7.60), "con_lightgreen": (135, 32, 8.70),
                         "con_lightyellow": (48, 58, 10.10), "con_lightblue": (215, 50, 8.97),
                         "con_lightmagenta": (300, 40, 7.85), "con_lightcyan": (188, 45, 7.35),
                         "con_yellow": (48, 55, 8.17)}.items():
        p[k] = _spec_hex(h, s, bg, t)
    p["con_black"] = _spec_hex(150, 20, bg, 1.15)
    for k, src in MINERAL_ALIAS.items():
        p[k] = p[src]
    p["fg_sel"] = _spec_hex(50, 12, p["bg_selection"], 7.20, "light")
    p["fg_search"] = _spec_hex(50, 12, p["bg_search"], 7.60, "light")
    # hint_current 坐在"当前提示芯片"上，必须按**芯片底**反解，否则芯片上只有 2:1
    p["hint_current"] = _spec_hex(232, 45, p["bg_inlay_hint_current"], 4.00, "light")
    p["con_lightgray"] = p["fg"]
    p["con_white"] = _spec_hex(50, 20, bg, 11.11)
    return p


MINERAL = build_mineral()
MINERAL["accent"] = "#477970"       # 矿彩 UI 用克制的青矿色，避免整站仍是一片森林绿
MINERAL["accent_hover"] = "#588F84"
MINERAL["ui_base"] = "#181E1C"       # 工作台基底：近中性的墨灰绿
MINERAL["ui_surface"] = "#252F2B"
MINERAL["ui_hover"] = "#2C3A35"
PALETTES["mineral"] = MINERAL

# 自检：两款主题必须覆盖同一批语义槽位
_missing = set(DARK) - set(MINERAL)
assert not _missing, "矿彩缺少槽位: %s" % sorted(_missing)
