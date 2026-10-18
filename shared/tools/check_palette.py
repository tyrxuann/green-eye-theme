#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
平台无关的调色板验收：读 `shared/palette.json`，只按色值判定。

新平台（VS Code / Vim / 终端…）只要消费同一份 palette.json，就应该能过这套检查 ——
它检查的是**色值本身**，与平台怎么组织主题文件无关。

四类判据：
  1. 对比度下限（按语义角色）
  2. 状态色两两可分（亮度差不足 **且** 色差也不足 = 分不开）
  3. 前景 token 两两可分（含"不得比参考更近"的严格口径）
  4. 主题身份：任两款主题之间必须"一眼可分"
"""
import itertools
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
from colorlib import contrast, de2000, simulate_cvd  # noqa: E402

# ---- 判据 1：对比度下限（对各自编辑器底） ----
FLOORS = {
    "fg": ("≥", 9.0), "caret": ("≥", 9.0),
    "keyword": ("≥", 6.0), "string": ("≥", 6.0), "number": ("≥", 6.0),
    "function": ("≥", 6.0), "constant": ("≥", 4.0), "annotation": ("≥", 6.0),
    "doc_tag": ("≥", 4.5), "error": ("≥", 4.5), "todo": ("≥", 6.0),
    "comment": ("≥", 3.5), "doc_comment": ("≥", 3.0),
    "line_numbers": ("≤", 2.8),
}
# ---- 判据 2：状态色（能同屏共现的块） ----
STATE = ["bg_selection", "bg_search", "bg_search_current", "bg_caret_row",
         "bg_matched_brace", "bg_diff_add", "bg_diff_del", "bg_diff_mod",
         "bg_raised", "bg_inlay_hint", "bg_identifier_caret", "bg_execution_point",
         "bg_breakpoint", "bg_not_top_frame", "bg_doc_code", "bg_breadcrumb"]
STATE_MIN_CONTRAST, STATE_MIN_DE = 1.10, 12.0
# ---- 判据 3：前景 token ----
TOKENS = ["fg", "comment", "doc_comment", "keyword", "string", "number",
          "function", "constant", "annotation", "todo", "error", "doc_tag"]
TOKEN_MIN_DE = 12.0
# ---- 判据 4：主题身份（权重取自真实 Java 样例的冻结计数） ----
IDENTITY_WEIGHTS = {"keyword": 31, "doc_comment": 19, "function_call": 15,
                    "field": 13, "comment": 8, "string": 5, "doc_tag": 5,
                    "annotation": 2, "number": 2, "function": 2, "constant": 1}
NOVELTY = ["string", "number", "function"]
IDENT = {"novelty_min": 15.0, "weighted": 16.0, "main_min": 5}
MAIN = ["keyword", "string", "number", "function", "constant", "annotation",
        "todo", "comment"]


def load():
    p = os.path.join(ROOT, "palette.json")
    if not os.path.exists(p):
        p = os.path.join(HERE, "..", "palette.json")
    return json.load(open(p, encoding="utf-8"))


EPS = 0.02   # 浮点容差：9.00:1 不该因为舍入被判不达标


def _exceptions(doc):
    e = doc.get("exceptions", {})
    same = {frozenset(p) for p in e.get("same_by_design", [])}
    acc = {frozenset(a["pair"]) for a in e.get("accepted_pairs", [])}
    ref = e.get("reference_token_de", {})
    return same, acc, ref


def main():
    doc = load()
    themes = doc["themes"]
    SAME, ACC, REF_TOK = _exceptions(doc)
    print("契约自带例外：同值别名 %d 组 · 已接受配对 %d 条 · token 参考基线 %d 对"
          % (len(SAME), len(ACC), len(REF_TOK)))
    bad = 0
    print("平台无关调色板验收（%s，%d 款主题）" % (doc.get("schema"), len(themes)))

    for t in themes:
        c, name = t["colors"], "%s「%s」" % (t["name"], t["label"])
        bg = t["bg_editor"]
        print("\n【%s】底 %s" % (name, bg))
        # 1 对比度
        v1 = []
        for k, (op, th) in FLOORS.items():
            if k not in c:
                continue
            r = contrast(c[k], bg)
            if (op == "≥" and r < th - EPS) or (op == "≤" and r > th + EPS):
                v1.append((k, round(r, 2), "%s %.1f" % (op, th)))
        print("  对比度下限：%s" % ("✅" if not v1 else "❌ %s" % v1))
        bad += len(v1)
        # 2 状态色
        v2 = []
        for a, b in itertools.combinations([k for k in STATE if k in c], 2):
            if c[a].upper() == c[b].upper() or frozenset((a, b)) in SAME \
                    or frozenset((a, b)) in ACC:
                continue
            if contrast(c[a], c[b]) < STATE_MIN_CONTRAST and de2000(c[a], c[b]) < STATE_MIN_DE:
                v2.append((a, b, round(de2000(c[a], c[b]), 1)))
        print("  状态色两两可分：%s" % ("✅" if not v2 else "❌ %s" % v2[:4]))
        bad += len(v2)
        # 3 前景 token
        v3 = []
        for a, b in itertools.combinations([k for k in TOKENS if k in c], 2):
            if c[a].upper() == c[b].upper() or frozenset((a, b)) in SAME:
                continue
            # 参考自己也贴得近的配对 → 要求"不得比参考更近"
            need = REF_TOK.get("|".join(sorted((a, b))), TOKEN_MIN_DE)
            d = de2000(c[a], c[b])
            if d < need - EPS:
                v3.append((a, b, round(d, 1), "需≥%.1f" % need))
        print("  前景 token 可分：%s" % ("✅" if not v3 else "❌ %s" % v3[:4]))
        bad += len(v3)
        # 色觉（报告，不判失败）
        cvd = sum(1 for a, b in itertools.combinations([k for k in TOKENS if k in c], 2)
                  if de2000(c[a], c[b]) >= TOKEN_MIN_DE
                  and min(de2000(simulate_cvd(c[a], k2), simulate_cvd(c[b], k2))
                          for k2 in ("protanopia", "deuteranopia")) < TOKEN_MIN_DE)
        print("  色觉缺陷下塌陷：%d 对（报告项，官方靠发布 CVD 变体解决）" % cvd)

    # 4 主题身份
    for x, y in itertools.combinations(themes, 2):
        a, b = x["colors"], y["colors"]
        de = {k: de2000(a[k], b[k]) for k in a if k in b}
        novelty = min(de[k] for k in NOVELTY if k in de)
        neutral = {x["bg_editor"], y["bg_editor"], a.get("fg"), b.get("fg")}
        ranked = [(k, de[k], IDENTITY_WEIGHTS[k]) for k in de
                  if k in IDENTITY_WEIGHTS and a.get(k) not in neutral]
        tot = sum(w for _, _, w in ranked) or 1
        weighted = sum(d * w for _, d, w in ranked) / tot
        hits = sum(1 for k in MAIN if de.get(k, 0) >= 12)
        ok = (novelty >= IDENT["novelty_min"] and weighted >= IDENT["weighted"]
              and hits >= IDENT["main_min"])
        print("\n【%s vs %s】身份：%s" % (x["label"], y["label"], "✅ 一眼可分" if ok else "❌ 太像"))
        print("  novelty %.1f（≥%.0f）· 频率加权 %.1f（≥%.0f）· 主力 %d/8（≥%d）"
              % (novelty, IDENT["novelty_min"], weighted, IDENT["weighted"],
                 hits, IDENT["main_min"]))
        bad += 0 if ok else 1

    print("\n%s" % ("✅ 全部通过" if not bad else "❌ 共 %d 项不达标" % bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
