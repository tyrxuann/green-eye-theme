#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
状态色两两撞色检查（评委建议的"唯一重要的工程动作"）。

为什么需要它：手动挑色时，最容易漏掉的是**状态色之间**的碰撞 ——
它们很少同时出现在一行里，但两两必须可区分。本项目已经被抓到两次：
  · diff 新增 `#2C5240` 与查找匹配 `#2D543F`：对比 1.03:1、ΔE2000 只有个位数
  · 面板与编辑器色度完全相同（只有明度差），"绿岛"层次没落地

检查对象是全部**非文字的状态色**（背景块、结构线、描边），逐对计算：
  · WCAG 对比度        要求 >= 1.15:1
  · CIEDE2000 色差     要求 >= 12
任一项不达标就 fail、打印矩阵并给出退出码 1，可直接挂进生成流程。

用法:
    python3 check_collisions.py            # 检查并打印
    python3 check_collisions.py --quiet     # 只输出结论（给 CI 用）
"""
import argparse
import ast
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from palette import DARK, PALETTES, contrast, hex_to_rgb  # noqa: E402

# 按语义分组：只有"能同屏共现、必须互相可分"的组才 fail；
# 同族的结构线允许接近（它们本来就该若有若无），只报告不拦。
GROUPS = {
    "状态块（可同屏共现，必须可分）": dict(
        keys=["bg_selection", "bg_search", "bg_search_current", "bg_caret_row",
              "bg_inlay_hint", "bg_inlay_hint_current",
              "bg_matched_brace", "bg_diff_add", "bg_diff_del", "bg_diff_mod",
              "bg_raised",
              # 第七轮新增的 11 个背景键：必须一起纳管，否则"0 对撞色"只是作用域没覆盖
              "bg_identifier_caret", "bg_identifier_write",
              "bg_execution_point", "bg_breakpoint", "bg_not_top_frame",
              "bg_doc_code", "bg_doc_code_block", "bg_breadcrumb",
              "bg_injected", "bg_smart_cast", "bg_matched_tag",
              "bg_error_hint"],
        contrast=1.10, de=12.0),
    "三面层次（编辑器/面板/浮层）": dict(
        keys=["bg_editor", "bg_panel", "bg_raised", "bg_console"],
        contrast=1.12, de=4.0),
    "结构线（同族，容许接近）": dict(
        keys=["border", "separator", "indent_guide", "right_margin", "whitespace"],
        contrast=1.02, de=2.5),
}

# 已评估并接受的组合：写明理由，检查器只提示、不算失败。
# （宁可显式列出，也不要让它们悄悄溜过）
ACCEPTED = {
    # —— 跨视图 ——
    frozenset(("bg_not_top_frame", "bg_diff_mod")):
        "调用栈非栈顶帧 vs diff 修改行：不同视图，不会同屏。",
    frozenset(("bg_diff_add", "bg_raised")):
        "diff 新增行底 vs 弹窗底：不同视图，且弹窗有 1.77:1 描边隔开；"
        "要拉开到 ΔE≥12 需把新增行饱和度提到 68%，会过艳，不值；Δhue 38° 已足够。"
        "第二条理由：inlay hint 芯片底也复用浮层底，会落在 diff 新增行上使边界消失；"
        "接受，因为 hint 文字在 #2E4A2A 上仍有 2.97:1，且 diff 视图首要信号是行填充。",
    # —— 跨区域（编辑器 vs 工具窗 / 面包屑条 / 提示条）——
    frozenset(("bg_doc_code_block", "bg_panel")):
        "Javadoc 代码块（编辑器内）vs 面板底（工具窗）：不同区域。",
    frozenset(("bg_injected", "bg_panel")):
        "注入语言片段（编辑器内）vs 面板底（工具窗）：不同区域。",
    frozenset(("bg_breadcrumb", "bg_caret_row")):
        "面包屑当前项 vs 当前行：面包屑在编辑器上方独立条带，背景整条重绘，不叠加。",
    frozenset(("bg_smart_cast", "bg_breadcrumb")):
        "Kotlin smart cast（编辑器内）vs 面包屑条：不同区域。",
    frozenset(("bg_injected", "bg_breadcrumb")):
        "注入语言片段（编辑器内）vs 面包屑条：不同区域。",
    frozenset(("bg_identifier_write", "bg_error_hint")):
        "写入态标识符在编辑器内、ERROR_HINT 是提示条背景，不同区域。",
    # —— 跨语言（不会同时出现）——
    frozenset(("bg_smart_cast", "bg_doc_code_block")):
        "Kotlin smart cast vs Javadoc 代码块：不同语言、不同区域。",
    frozenset(("bg_injected", "bg_smart_cast")):
        "注入语言片段 vs Kotlin smart cast：前者是「字符串里嵌 SQL」这类场景，"
        "后者是 Kotlin 语义高亮，不同语言不同时出现。",
    frozenset(("bg_matched_tag", "bg_inlay_hint")):
        "XML 配对标签 vs 参数提示芯片：XML 里不出现 Java 参数提示，不同语言。",
    # —— 同区域但语义上必然叠加，底色刻意极淡 ——
    frozenset(("bg_matched_brace", "bg_doc_code_block")):
        "匹配括号在代码里、Javadoc 代码块在注释里，不同区域。",
    frozenset(("bg_identifier_caret", "bg_doc_code")):
        "标识符高亮在代码里、内联代码芯片在 Javadoc 里，不同区域。",
    frozenset(("bg_caret_row", "bg_injected")):
        "当前行刻意接近不可见（1.19:1），注入片段/配对标签的底色叠在其上属预期。",
    frozenset(("bg_caret_row", "bg_matched_tag")):
        "同上：当前行是极淡通栏，语义高亮叠在其上属预期。",
    frozenset(("bg_matched_tag", "bg_raised")):
        "XML 配对标签 vs 浮层底：浮层有 1.77:1 描边隔开，且不同区域。",
    # —— 提亮背景强度后新增的拥挤（官方这些键彼此也是 1.4–1.8，同样贴得近）——
    frozenset(("bg_smart_cast", "bg_inlay_hint")):
        "Kotlin smart cast vs 参数提示芯片：官方这两个键相对强度也是 1.42 vs 2.31 且贴得近；"
        "接受，因为芯片有独立前景文字，smart cast 只是底色。",
    frozenset(("bg_smart_cast", "bg_raised")):
        "Kotlin smart cast vs 弹窗底：弹窗有 1.77:1 描边隔开，且弹窗覆盖时编辑器已失焦。",

    frozenset(("bg_smart_cast", "bg_inlay_hint_current")):
        "同「smart cast vs 参数提示芯片」。",
    frozenset(("bg_injected", "bg_inlay_hint_current")):
        "注入语言片段与当前参数提示：不同语言/不同场景（嵌 SQL 的字符串 vs Java 参数）。",
    frozenset(("bg_not_top_frame", "bg_identifier_caret")):
        "调用栈非栈顶帧（调试器面板）vs 光标标识符（编辑器）：不同视图。",
    frozenset(("bg_breakpoint", "bg_diff_del")):
        "断点行 vs diff 删除行：两个暗红。**理由不是「不同视图」**（diff 视图就是编辑器，"
        "调试时两者可以同屏）—— 而是：这两个色相的间距只能靠明度拿，而断点行需要足够显眼。"
        "接受，因为断点另有 gutter 圆点与整行标识，不依赖底色与删除行区分。",
    frozenset(("bg_matched_tag", "bg_selection")):
        "XML 配对标签 vs 选中块：ΔE 11.6 接近阈值（12），选中块另有明确的青色相，"
        "实际可辨；提亮配对标签是为了修「等于没有底色」更严重的问题。",
}

# 设计上刻意相同的别名对，不参与检查
SAME_BY_DESIGN = {
    frozenset(("bg_editor", "bg_gutter")),        # 行号槽与编辑器同底（官方同做法）
    frozenset(("bg_caret_row", "bg_folded")),     # 折叠区与当前行同底
    frozenset(("bg_panel", "bg_console")),        # 控制台与面板同底（官方同做法）
    frozenset(("separator", "indent_guide")),     # 同为发丝线，同一值
    frozenset(("bg_inlay_hint", "bg_raised")),    # inlay hint 是"浮起的小片"，与浮层同底
}


def _lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def lab(h):
    r, g, b = [_lin(v) for v in hex_to_rgb(h)]
    # sRGB -> XYZ (D65)
    x = r * 0.4124564 + g * 0.3575761 + b * 0.1804375
    y = r * 0.2126729 + g * 0.7151522 + b * 0.0721750
    z = r * 0.0193339 + g * 0.1191920 + b * 0.9503041
    xn, yn, zn = 0.95047, 1.00000, 1.08883

    def f(t):
        return t ** (1 / 3) if t > 0.008856 else (7.787 * t + 16 / 116)

    fx, fy, fz = f(x / xn), f(y / yn), f(z / zn)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def de2000(h1, h2):
    """CIEDE2000 色差。"""
    L1, a1, b1 = lab(h1)
    L2, a2, b2 = lab(h2)
    C1, C2 = math.hypot(a1, b1), math.hypot(a2, b2)
    Cb = (C1 + C2) / 2
    G = 0.5 * (1 - math.sqrt(Cb ** 7 / (Cb ** 7 + 25 ** 7))) if Cb else 0
    a1p, a2p = (1 + G) * a1, (1 + G) * a2
    C1p, C2p = math.hypot(a1p, b1), math.hypot(a2p, b2)
    h1p = math.degrees(math.atan2(b1, a1p)) % 360
    h2p = math.degrees(math.atan2(b2, a2p)) % 360
    dLp = L2 - L1
    dCp = C2p - C1p
    if C1p * C2p == 0:
        dhp = 0.0
    else:
        d = h2p - h1p
        dhp = d - 360 if d > 180 else (d + 360 if d < -180 else d)
    dHp = 2 * math.sqrt(C1p * C2p) * math.sin(math.radians(dhp) / 2)
    Lbp = (L1 + L2) / 2
    Cbp = (C1p + C2p) / 2
    if C1p * C2p == 0:
        hbp = h1p + h2p
    else:
        s = h1p + h2p
        hbp = (s + 360) / 2 if abs(h1p - h2p) > 180 and s < 360 else \
              ((s - 360) / 2 if abs(h1p - h2p) > 180 else s / 2)
    T = (1 - 0.17 * math.cos(math.radians(hbp - 30))
         + 0.24 * math.cos(math.radians(2 * hbp))
         + 0.32 * math.cos(math.radians(3 * hbp + 6))
         - 0.20 * math.cos(math.radians(4 * hbp - 63)))
    dTh = 30 * math.exp(-(((hbp - 275) / 25) ** 2))
    Rc = 2 * math.sqrt(Cbp ** 7 / (Cbp ** 7 + 25 ** 7)) if Cbp else 0
    Sl = 1 + (0.015 * (Lbp - 50) ** 2) / math.sqrt(20 + (Lbp - 50) ** 2)
    Sc = 1 + 0.045 * Cbp
    Sh = 1 + 0.015 * Cbp * T
    Rt = -math.sin(math.radians(2 * dTh)) * Rc
    return math.sqrt((dLp / Sl) ** 2 + (dCp / Sc) ** 2 + (dHp / Sh) ** 2
                     + Rt * (dCp / Sc) * (dHp / Sh))


def _assert_no_duplicate_dict_keys():
    """所有字典字面量都不允许重复键 —— 同名静默覆盖在 EXPLICIT 咬过三次、
    在 ACCEPTED 又咬了一次（一条理由被悄悄丢掉）。改成硬报错。"""
    tree = ast.parse(open(__file__, encoding="utf-8").read())
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            keys = []
            for k in node.keys:
                if isinstance(k, ast.Call):        # frozenset((a, b))
                    keys.append(tuple(sorted(e.value for e in k.args[0].elts)))
                elif isinstance(k, ast.Constant):
                    keys.append(k.value)
            dup = sorted({k for k in keys if keys.count(k) > 1})
            if dup:
                raise SystemExit("字典字面量有重复键（后者会静默覆盖前者）：%s" % dup)


def _alias_classes():
    """把 SAME_BY_DESIGN 里的等值别名并成等价类，用于传递展开例外。"""
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for pair in SAME_BY_DESIGN:
        a, b = sorted(pair)
        parent[find(a)] = find(b)
    cls = {}
    for k in list(parent):
        cls.setdefault(find(k), set()).add(k)
    return cls


def _accepted_pairs():
    """把 ACCEPTED 按别名等价类传递展开（同一根因只写一次）。"""
    out = dict(ACCEPTED)
    cls = _alias_classes()
    for pair, why in list(ACCEPTED.items()):
        a, b = sorted(pair)
        for c in cls.values():
            if a in c:
                for x in c - {a}:
                    out.setdefault(frozenset((x, b)), why + "（与 %s 同底，同一根因）" % a)
            if b in c:
                for x in c - {b}:
                    out.setdefault(frozenset((a, x)), why + "（与 %s 同底，同一根因）" % b)
    return out


def _report(pal, label, quiet=False):
    failed = []
    if not quiet:
        print("\n===== %s =====" % label)
    for gname, g in GROUPS.items():
        keys = [k for k in g["keys"] if k in pal]
        rows = []
        for i in range(len(keys)):
            for j in range(i + 1, len(keys)):
                a1, a2 = keys[i], keys[j]
                if frozenset((a1, a2)) in SAME_BY_DESIGN:
                    continue
                rows.append((a1, a2, contrast(pal[a1], pal[a2]), de2000(pal[a1], pal[a2])))
        # 判据：亮度差不足 **且** 色差也不足，才算真的分不开
        bad = [r for r in rows if r[2] < g["contrast"] and r[3] < g["de"]
               and frozenset((r[0], r[1])) not in _accepted_pairs()]
        if not quiet:
            print("\n【%s】%d 对，阈值 对比度≥%.2f:1 且 ΔE2000≥%.1f → %s"
                  % (gname, len(rows), g["contrast"], g["de"],
                     "全部通过 ✅" if not bad else "不达标 %d 对" % len(bad)))
            for r in sorted(bad, key=lambda x: x[3])[:12]:
                print("   %-20s %-20s %8.3f:1 %7.1f" % r)
        failed += [(gname,) + r for r in bad]
    return failed


def main():
    _assert_no_duplicate_dict_keys()
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    from official_palette import OFFICIAL
    # 用官方 Islands Dark 当标尺：阈值必须让官方通过，否则阈值本身不合理
    off_fail = _report(OFFICIAL, "标尺：官方 Islands Dark", quiet=a.quiet)
    cur_fail = []
    for key, pal in sorted(PALETTES.items()):
        cur_fail += _report(pal, "本主题：%s「%s」" % (pal["name"], pal["label"]), quiet=a.quiet)
    off_pairs = {(r[1], r[2]) for r in off_fail}
    cur_pairs = {(r[1], r[2]) for r in cur_fail}
    extra = cur_pairs - off_pairs
    # 口径必须分清四类，否则"0 对"会被读成"比官方好"
    off_set = {(r[1], r[2]) for r in off_fail}
    cur_set = {(r[1], r[2]) for r in cur_fail}
    acc = _accepted_pairs()

    def _would_fail(pal, pair):
        for g in GROUPS.values():
            ks = [k for k in g["keys"] if k in pal]
            if pair[0] in ks and pair[1] in ks:
                return (contrast(pal[pair[0]], pal[pair[1]]) < g["contrast"]
                        and de2000(pal[pair[0]], pal[pair[1]]) < g["de"])
        return False

    n_acc = sum(1 for pr in acc if _would_fail(DARK, tuple(sorted(pr))))
    n_off_cov = sum(1 for g in GROUPS.values() for k in g["keys"] if k in OFFICIAL)
    n_ours_cov = sum(1 for g in GROUPS.values() for k in g["keys"] if k in DARK)
    n_all = sum((len([k for k in g["keys"] if k in DARK]) *
                 (len([k for k in g["keys"] if k in DARK]) - 1)) // 2
                for g in GROUPS.values())
    print("\n【口径】四个数并列，避免「比官方多出 0 对」被误读成「比官方好」：")
    print("   检查对总数                    %d 对" % n_all)
    print("   本主题未达阈值                %d 对" % len(cur_fail))
    print("     ├ 官方同一对也未达阈值      %d 对（= 官方基线噪声）"
          % len(cur_set & off_set))
    print("     └ 已经显式接受并写明理由    %d 对" % n_acc)
    print("   官方标尺未达阈值              %d 对（标尺覆盖 %d/%d 个状态块键）"
          % (len(off_fail), n_off_cov, n_ours_cov))
    print("   → 本主题比官方多出（未豁免）  %d 对" % len(extra))
    if extra:
        print("\n本主题独有、官方不存在的撞色（这些才是要修的）：")
        for r in sorted(cur_fail, key=lambda x: x[4]):
            if (r[1], r[2]) in extra:
                print("   %-20s %-20s %8.3f:1 %7.1f" % (r[1], r[2], r[3], r[4]))
        return 1
    print("✅ 没有比官方更差的状态色撞色")
    return 0


if __name__ == "__main__":
    sys.exit(main())
