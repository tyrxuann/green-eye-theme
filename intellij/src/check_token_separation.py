#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
前景 token 两两可分性检查（第 7 条维度）。

为什么需要它：`check_collisions.py` 只覆盖**背景/状态色**（选中的块、查找的块…），
但真正天天看的是**前景 token**：关键字、字符串、数字、函数、常量、注解、TODO。
这些色如果彼此太近，代码就"糊"成一片 —— 而且这种问题在缩略图上尤其看不出来。

判据（严格版，以官方为标尺）：
  · 官方该配对 ΔE ≥ 12  → 我们也必须 ≥ 12；
  · 官方该配对 ΔE < 12  → 我们**不得比官方更近**（官方自己也贴得近的那些，说明可接受，
    但不能更糟）。这一条比"按配对名放行"严谨：后者会让"官方 11.7、我们 6.4"漏过去。
"""
import itertools
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from palette import PALETTES, contrast  # noqa: E402
from check_collisions import de2000  # noqa: E402

# 参与检查的前景 token（都是会在同一屏里同时出现的语义）
TOKENS = ["fg", "comment", "doc_comment", "keyword", "string", "number",
          "function", "constant", "annotation", "todo", "error", "doc_tag",
          "escape", "attr_value"]
LABEL = {"fg": "正文", "comment": "注释", "doc_comment": "文档注释", "keyword": "关键字",
         "string": "字符串", "number": "数字", "function": "函数", "constant": "常量/字段",
         "annotation": "注解", "todo": "TODO", "error": "错误", "doc_tag": "Javadoc标签",
         "escape": "转义", "attr_value": "属性值"}
DE_MIN = 12.0

# 色觉缺陷模拟（Machado et al. 2009，severity 1.0 的线性 RGB 矩阵）。
# 官方 Islands Dark 有 71 个 option 带 deuteranopia/protanopia 变体，我们一个都没有 ——
# 这是真实的可达性差距，所以至少要能**看见**它：正常色觉可分、色盲下塌陷的配对必须报出来。
CVD_MATRIX = {
    "protanopia": ((0.152286, 1.052583, -0.204868),
                   (0.114503, 0.786281, 0.099216),
                   (-0.003882, -0.048116, 1.051998)),
    "deuteranopia": ((0.367322, 0.860646, -0.227968),
                     (0.280085, 0.672501, 0.047413),
                     (-0.011820, 0.042940, 0.968881)),
}


def _srgb_to_lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _lin_to_srgb(c):
    c = max(0.0, min(1.0, c))
    v = c * 12.92 if c <= 0.0031308 else 1.055 * (c ** (1 / 2.4)) - 0.055
    return max(0, min(255, int(round(v * 255))))


def simulate_cvd(hex_color, kind):
    """把颜色按指定色觉类型模拟一遍，返回 #RRGGBB。"""
    from palette import hex_to_rgb
    r, g, b = (_srgb_to_lin(v) for v in hex_to_rgb(hex_color))
    m = CVD_MATRIX[kind]
    out = [m[i][0] * r + m[i][1] * g + m[i][2] * b for i in range(3)]
    return "#%02X%02X%02X" % tuple(_lin_to_srgb(v) for v in out)


def dmap(pal, keys):
    return {(a, b): de2000(pal[a], pal[b])
            for a, b in itertools.combinations([k for k in keys if k in pal], 2)}


def violations(pal, base_d, keys):
    """严格规则：返回 {配对: (我方ΔE, 要求值)}。"""
    out = {}
    for k, v in dmap(pal, keys).items():
        need = DE_MIN if base_d.get(k, 99) >= DE_MIN else base_d[k]
        if v < need - 0.05:
            out[k] = (v, need)
    return out


def cvd_collapses(pal, keys, need=DE_MIN):
    """返回"正常色觉下可分、色盲下塌陷"的配对。"""
    out = {}
    for kind in CVD_MATRIX:
        sim = {k: simulate_cvd(pal[k], kind) for k in keys if k in pal}
        for a, b in itertools.combinations(sorted(sim), 2):
            if de2000(pal[a], pal[b]) < need:      # 正常色觉本来就近，不算新问题
                continue
            d = de2000(sim[a], sim[b])
            if d < need:
                out.setdefault((a, b), []).append((kind, d))
    return out
    """严格规则：返回 {配对: (我方ΔE, 要求值)}。"""
    out = {}
    for k, v in dmap(pal, keys).items():
        need = DE_MIN if base_d.get(k, 99) >= DE_MIN else base_d[k]
        if v < need - 0.05:
            out[k] = (v, need)
    return out


def main():
    from official_palette import OFFICIAL
    base_d = dmap(OFFICIAL, TOKENS)
    base = {k: v for k, v in base_d.items() if v < DE_MIN}
    print("前景 token 可分性检查（%d 个 token，阈值 ΔE2000 ≥ %.0f）" % (len(TOKENS), DE_MIN))
    print("标尺：官方 Islands Dark 自身有 %d 对低于阈值（这 %d 对的要求改成「不得比官方更近」）"
          % (len(base), len(base)))
    total = 0
    for key, pal in sorted(PALETTES.items()):
        v = violations(pal, base_d, TOKENS)
        print("\n【%s「%s」】违规 %d 对" % (pal["name"], pal["label"], len(v)))
        for (a, b), (dv, need) in sorted(v.items(), key=lambda x: x[1][0]):
            print("   ❌ %-10s ↔ %-10s ΔE %5.1f（要求 ≥ %.1f）对比 %.2f:1"
                  % (LABEL.get(a, a), LABEL.get(b, b), dv, need, contrast(pal[a], pal[b])))
        total += len(v)
        # 只看"不同值"的配对（同值别名会把榜单占满），并显示**我们的** ΔE
        near = sorted(((de2000(pal[a], pal[b]), a, b)
                       for a, b in itertools.combinations([k for k in TOKENS if k in pal], 2)
                       if pal[a].upper() != pal[b].upper()))[:3]
        print("   最接近的三对：" + "；".join(
            "%s↔%s ΔE %.1f" % (LABEL.get(a, a), LABEL.get(b, b), d) for d, a, b in near))
    # 色觉缺陷：正常可分、模拟后塌陷的配对
    cvd_total = 0
    print("\n色觉缺陷模拟（Machado 2009，severity 1.0）")
    off_col = cvd_collapses(OFFICIAL, TOKENS)
    print("  基线：官方 Islands Dark 自身就有 %d 对在色盲下塌陷"
          "（官方另发布 deuteranopia/protanopia 变体来弥补，我们暂未提供）" % len(off_col))
    for key, pal in sorted(PALETTES.items()):
        col = cvd_collapses(pal, TOKENS)
        print("  【%s「%s」】正常可分但色盲下塌陷：%d 对" % (pal["name"], pal["label"], len(col)))
        for (a, b), kinds in sorted(col.items(), key=lambda x: min(k[1] for k in x[1])):
            detail = "；".join("%s ΔE %.1f" % (k, d) for k, d in kinds)
            print("     ⚠️  %-10s ↔ %-10s 正常 ΔE %4.1f → %s"
                  % (LABEL.get(a, a), LABEL.get(b, b), de2000(pal[a], pal[b]), detail))
        cvd_total += len(col)
    if total:
        print("\n❌ %d 对前景 token 间距不足" % total)
        return 1
    if cvd_total:
        print("\n⚠️  %d 对色盲下塌陷（官方有 71 个 CVD 变体，我们目前没有；"
              "先报出来，是否加变体由取舍决定）" % cvd_total)
    print("\n✅ 前景 token 可分性不劣于官方")
    return 0


if __name__ == "__main__":
    sys.exit(main())
