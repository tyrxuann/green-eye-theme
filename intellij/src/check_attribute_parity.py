#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
与官方内置方案做"同名属性块"逐键对比（评委建议的第二条工程规则）。

这一条规则一次关闭了两类只能靠逐键对比发现的 bug：
  · 第一类：ET 取值整体错位（官方 2=波浪线，我们写成 1=实线下划线），32 个块受影响；
  · 第二类：官方有 EFFECT_TYPE 而我们**完全没写** → 真机里下划线/波浪线直接消失
    （渲染管线只画自己那条波浪线，永远照不到）。

规则（严格版，不再是"两边都有才比"）：
  1. 官方定义了 EFFECT_TYPE 的键，我们必须也有，且取值相同；
  2. 官方**同时**定义了 EFFECT_TYPE 与 EFFECT_COLOR 的键，我们必须也有效果色；
     官方只写 EFFECT_COLOR 而没有 ET 的（等于不生效），不要求（避免自造无效配置）。
  3. 官方定义了 BACKGROUND 的键，我们必须也有 —— 这一条抓出了 17 个缺口，
     其中"调试器当前执行行/断点行/调用栈非栈顶帧"本来被当成"需真机走查"，
     其实完全静态可查。

用法: python3 check_attribute_parity.py
"""
import os
import re
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
OFFICIAL = os.path.join(ROOT, "build", "ref", "ide_official_schemes", "IslandSchemeDark.xml")
MINE = os.path.join(ROOT, "themes", "Green-Eye-Dark.icls")
# 官方与我们都未定义、或语义上允许不同的键（写明理由）
ALLOW_DIFFERENT = {
    "WRONG_REFERENCES_ATTRIBUTES": "官方为 None（从 Darcula 继承波浪线），我显式写 2，等价",
}
SPY_EXEMPT = set()

# 参考方案（官方 ∪ Darcula）有底色、而我们**有意不给**的键 —— 逐条写理由。
# 这一批是"把标尺扩到 Darcula"之后才浮现的（此前对所有检查器隐身）。
BG_EXEMPT = {k: "控制台/终端按颜色分级：Darcula 给每级单独铺暗底，"
                "本主题改为一律用控制台底色 + 分级前景色（日志更干净，也随主题走）"
             for k in (
    "CONSOLE_BLACK_OUTPUT", "CONSOLE_RED_OUTPUT", "CONSOLE_GREEN_OUTPUT",
    "CONSOLE_YELLOW_OUTPUT", "CONSOLE_BLUE_OUTPUT", "CONSOLE_MAGENTA_OUTPUT",
    "CONSOLE_CYAN_OUTPUT", "CONSOLE_GRAY_OUTPUT", "CONSOLE_WHITE_OUTPUT",
    "CONSOLE_DARKGRAY_OUTPUT", "CONSOLE_RED_BRIGHT_OUTPUT",
    "CONSOLE_GREEN_BRIGHT_OUTPUT", "CONSOLE_YELLOW_BRIGHT_OUTPUT",
    "CONSOLE_BLUE_BRIGHT_OUTPUT", "CONSOLE_MAGENTA_BRIGHT_OUTPUT",
    "CONSOLE_CYAN_BRIGHT_OUTPUT",
)}
BG_EXEMPT.update({k: "调试/求值/终端块的暗底由本主题的浮层底色承载，不再逐级铺底"
                  for k in ("SPY-JS.PROGRAM_SCOPE", "SPY-JS.FUNCTION_SCOPE",
                            "SPY-JS.PATH_LEVEL_ONE", "SPY-JS.EXCEPTION",
                            "EVALUATED_EXPRESSION_ATTRIBUTES",
                            "EVALUATED_EXPRESSION_EXECUTION_LINE_ATTRIBUTES",
                            "TERMINAL_COMMAND_TO_RUN_USING_IDE",
                            "VELOCITY_SCRIPTING_BACKGROUND",
                            "HAML_RUBY_CODE")})
BG_EXEMPT["DUPLICATE_FROM_SERVER"] = "服务器重复文件的提示底，本主题用前景色+条纹表达"
# JS 分析器（SPY-JS.*）来自 JS/Debugger 插件而非官方深色方案：本主题不给它铺底/描边，
# 让它用编辑器的常规底色与前景（该视图很少用，且逐键铺底会引入一串与主题无关的暗色）
SPY_EXEMPT.update({"SPY-JS.PATH_LEVEL_ONE", "SPY-JS.PATH_LEVEL_TWO",
                   "SPY-JS.FUNCTION_SCOPE", "SPY-JS.PROGRAM_SCOPE", "SPY-JS.EXCEPTION"})

# 背景强度低于官方 0.85× 但有意保留的（写明理由）
STRENGTH_EXEMPT = {
    "EXECUTIONPOINT_ATTRIBUTES": "官方 2.20×，本主题 1.76×（0.80）—— 绿底上再亮会盖住代码",
    "SEARCH_RESULT_ATTRIBUTES": "官方 2.03×，本主题 1.62×（0.80）—— 查找命中已靠当前匹配的第二档背景区分",
}
# diff 三行底色刻意比 Darcula 更含蓄（Darcula 的 2.0–2.2× 在绿底上会盖住代码）
STRENGTH_EXEMPT.update({
    "DIFF_DELETED": "Darcula 1.95×，本主题 1.46×（0.75）—— 绿底上更亮的红块会压过语法色",
    "DIFF_MODIFIED": "Darcula 2.24×，本主题 1.32×（0.59）—— 同上，修改行只需与新增/删除可区分",
})
STRENGTH_MIN = 0.85

# 规则 10：**风格家族**一致性。真机渲染查的是语言专用键（JavaHighlightingColors.KEYWORD
# 注册的是 "JAVA_KEYWORD"），所以只把 DEFAULT_KEYWORD 改成常规是没用的 ——
# 上一次就是这样漏掉了 69 个语言键（Java 关键字在真机上依然是粗体）。
# 与生成器**同一份**分类正则（第 4 轮评审：两处各写一遍必然再漂移）。
# 直接从 gen_icls 取，避免"关键字有两套定义"。
FAMILIES = [
    # 正则取评审给的确切写法（不再从生成器拉整张规则表 —— 那样会把 Markdown/代码引用一并卷进来）
    ("DEFAULT_KEYWORD", r"KEYWORD|MODIFIER|PRIMITIVE|RESERVED|PSEUDO_INSTRUCTION|INSTRUCTION"),
    ("DEFAULT_LINE_COMMENT", r"(LINE|BLOCK|MULTI_LINE)_COMMENT"),
    ("DEFAULT_DOC_COMMENT", r"^DOC_COMMENT$"),
    ("DEFAULT_STATIC_FIELD", r"STATIC_(FINAL_)?FIELD"),
    ("DEFAULT_STATIC_METHOD", r"(STATIC_METHOD|PHP_STATIC_METHOD)"),
    # CONSTANT 族**故意不设**：官方对 DEFAULT_CONSTANT 是斜体，但对 GO_BUILTIN_CONSTANT /
    # BASH.VAR_USE_BUILTIN 这类语言键没有定义排版 —— 强行拉齐会变成"两种规则并存"
    # （第 4 轮评审给的两个选项里选"删掉"）。
    ("TODO_DEFAULT_ATTRIBUTES", r"^TODO"),
    ("DEFAULT_TAG", r"TAG"),
    ("DEFAULT_VALID_STRING_ESCAPE", r"ESCAPE"),
    ("INLAY_DEFAULT", r"^(INLAY|INVISIBLE_INLAY)"),
]
# 例外：① 参考方案自身不一致的键；② 生成器里**已写明有意理由**的键（FONT_INTENT）
def _intent_keys():
    try:
        from gen_icls import FONT_INTENT
        return set(FONT_INTENT)
    except Exception:
        return set()


FAMILY_EXEMPT = {
    "DEFAULT_DOC_COMMENT_TAG", "DEFAULT_DOC_COMMENT_TAG_VALUE",  # 官方常规 / Darcula 粗斜体
    "GO_COMMENT_REFERENCE",                                      # 注释内的引用，不属注释排版族
    "PY.DOC_COMMENT_TAG",
    "REGEXP.CHAR_CLASS", "REGEXP.REDUNDANT_ESCAPE",   # 官方定义成粗体，族规则不与之打架
    # 语言专用标签键：生成器把它们归入 tag 族（palette 键是 tag/attr_name），
    # 与规范键 DEFAULT_TAG 的"标签加粗"意图一致，只是键名不匹配 TAG 正则
    "HTML_CUSTOM_TAG_NAME", "PHP_TAG", "XML_CUSTOM_TAG_NAME",
    # 参考（Darcula）对这些键的排版与通用族不同 —— 保真优先，故不参与族强制：
    #   VELOCITY_KEYWORD = 加粗（Darcula），HAML_TAG = 不加粗（Darcula）
    "VELOCITY_KEYWORD", "HAML_TAG",
} | _intent_keys()
# 例外：参考方案自身不一致或语义特殊的键，不参与族强制
FAMILY_EXEMPT = {
    # XML/HTML 标签刻意不加粗：Windows 上 FiraCode 缺少匹配 bold 时会
    # 合成/回退，导致 pom.xml 看起来像换了字体；颜色已足够区分标签
    "XML_TAG", "XML_TAG_NAME", "XML_TAG_DATA", "XML_CUSTOM_TAG_NAME",
    "HTML_TAG", "HTML_TAG_NAME", "HTML_CUSTOM_TAG_NAME",
    "DEFAULT_DOC_COMMENT_TAG", "DEFAULT_DOC_COMMENT_TAG_VALUE",   # 官方常规 / Darcula 粗斜体，参考本身打架
    "GO_COMMENT_REFERENCE",      # 注释内的引用，不属于注释排版族
    "PY.DOC_COMMENT_TAG",
    "REGEXP.CHAR_CLASS", "REGEXP.REDUNDANT_ESCAPE",   # 官方定义成粗体，族规则不与之打架
    # 语言专用标签键：生成器把它们归入 tag 族（palette 键是 tag/attr_name），
    # 与规范键 DEFAULT_TAG 的"标签加粗"意图一致，只是键名不匹配 TAG 正则
    "HTML_CUSTOM_TAG_NAME", "PHP_TAG", "XML_CUSTOM_TAG_NAME",
    # 参考（Darcula）对这些键的排版与通用族不同 —— 保真优先，故不参与族强制：
    #   VELOCITY_KEYWORD = 加粗（Darcula），HAML_TAG = 不加粗（Darcula）
    "VELOCITY_KEYWORD", "HAML_TAG",
}


def read(path):
    """读方案。**保留 baseAttributes** —— 官方有 13 个键只用它定义
    （ANNOTATION_NAME_ATTRIBUTES / DEFAULT_FUNCTION_CALL / REGEXP.* 等），
    旧实现直接 `continue` 掉，于是这 13 个键对所有检查器隐身（评审第 4 轮指出）。"""
    root = ET.parse(path).getroot()
    out = {}
    for o in root.find("attributes"):
        v = o.find("value")
        if v is None:
            out[o.get("name")] = {"__base__": o.get("baseAttributes")}
            continue
        out[o.get("name")] = {x.get("name"): x.get("value") for x in v}
    return out


def resolve(d, name, seen=None):
    """展开 baseAttributes 链。"""
    seen = seen or set()
    if name in seen or name not in d:
        return {}
    seen.add(name)
    e = d[name]
    if "__base__" in e:
        base = e["__base__"]
        return resolve(d, base, seen) if base else {}
    return dict(e)


def effective(own, parent, name):
    """真机语义：**键在就用自己（缺字段=清空），键不在才整块取父方案**。"""
    if name in own:
        return resolve(own, name)
    return resolve(parent, name) if name in parent else {}


def load_reference():
    """标尺 = effective(官方 Islands Dark, Darcula)。Darcula 是代码注册的，
    从 IDE 的 DefaultColorSchemesManager.xml 里抽出来（build/ref/Darcula.xml）。"""
    off = read(OFFICIAL)
    dpath = os.path.join(ROOT, "build", "ref", "Darcula.xml")
    dar = read(dpath) if os.path.exists(dpath) else {}
    return off, dar


def _is_hex(v):
    return bool(v) and len(v) == 6 and all(c in "0123456789abcdefABCDEF" for c in v)


def _ratio(bg, editor_bg):
    """某背景相对其编辑器底的对比度。"""
    def lum(h):
        r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
        f = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
        r, g, b = f(r), f(g), f(b)
        return 0.2126 * r + 0.7152 * g + 0.0722 * b
    a, b2 = lum(bg), lum(editor_bg)
    hi, lo = max(a, b2), min(a, b2)
    return (hi + 0.05) / (lo + 0.05)


def check_one(off, mine, scheme_name, verbose=True, dar=None):
    """对一套方案跑六条对账规则，返回问题清单。"""
    dar = dar or {}
    # 标尺按 effective(官方, Darcula) 展开 —— 覆盖官方未定义、Darcula 定义的键
    ref = {k: effective(off, dar, k) for k in set(off) | set(dar)}
    mine_eff = {k: effective(mine, dar, k) for k in set(mine) | set(dar)}
    off = {k: v for k, v in ref.items() if v}
    mine = {k: v for k, v in mine_eff.items() if v}
    missing_et, diff_et, missing_ec, absent, missing_bg = [], [], [], [], []
    diff_ft, missing_stripe, weak_own = [], [], []
    dar = dar or {}
    # 标尺按 effective(官方, Darcula) 展开 —— 覆盖官方未定义、Darcula 定义的键
    ref = {k: effective(off, dar, k) for k in set(off) | set(dar)}
    mine_eff = {k: effective(mine, dar, k) for k in set(mine) | set(dar)}
    off = {k: v for k, v in ref.items() if v}
    mine = {k: v for k, v in mine_eff.items() if v}
    missing_et, diff_et, missing_ec, absent, missing_bg = [], [], [], [], []
    diff_ft, missing_stripe, weak_own = [], [], []
    for name, d in off.items():
        if name not in mine:
            # 键"完全没定义"= 真机里从 Darcula 继承，是最该报的一类
            absent.append((name, d.get("EFFECT_TYPE"), d.get("FOREGROUND")))
            continue
        m = mine[name]
        if name in SPY_EXEMPT:
            continue
        o_et, m_et = d.get("EFFECT_TYPE"), m.get("EFFECT_TYPE")
        if o_et is not None:
            if m_et is None:
                missing_et.append((name, o_et))
            elif m_et != o_et and name not in ALLOW_DIFFERENT:
                diff_et.append((name, o_et, m_et))
        if (d.get("EFFECT_COLOR") is not None and d.get("EFFECT_TYPE") is not None
                and m.get("EFFECT_COLOR") is None):
            missing_ec.append(name)
        if _is_hex(d.get("BACKGROUND")) and not _is_hex(m.get("BACKGROUND")) \
                and name not in BG_EXEMPT:
            missing_bg.append((name, d["BACKGROUND"]))
        # 规则 7：FONT_TYPE（粗体/斜体）—— 这一类在渲染管线里曾经完全不可见
        o_ft, m_ft = d.get("FONT_TYPE"), m.get("FONT_TYPE")
        if o_ft is not None and m_ft != o_ft:
            diff_ft.append((name, o_ft, m_ft))
        # 规则 8：ERROR_STRIPE_COLOR（滚动条/边栏条纹）—— 键在但字段丢了 = 条纹不画
        if "ERROR_STRIPE_COLOR" in d and "ERROR_STRIPE_COLOR" not in m:
            missing_stripe.append((name, d["ERROR_STRIPE_COLOR"]))
    if verbose:
        print("  [%s]" % scheme_name)
        print("    官方有 EFFECT_TYPE 而我缺失：%d %s" % (len(missing_et), missing_et or "✅"))
        print("    EFFECT_TYPE 取值不同：%d %s" % (len(diff_et), diff_et or "✅"))
        print("    官方有 EFFECT_COLOR 而我缺失：%d %s" % (len(missing_ec), missing_ec or "✅"))
        print("    官方定义了而我**完全缺失**的键：%d %s" % (len(absent), absent or "✅"))
        print("    官方有 BACKGROUND 而我缺失：%d %s" % (len(missing_bg), missing_bg or "✅"))
    # 规则 9：我们"自建"的键（官方没定义）也要自洽 —— 官方没定义就没人替我们把关，
    # 这是继承自 Darcula 的那一片盲区（Darcula 是代码注册的，拿不到原文）
    own_bg = mine.get("TEXT", {}).get("BACKGROUND", "1f3027")
    for name, m in mine.items():
        if name in off:
            continue
        bgv = m.get("BACKGROUND")
        if _is_hex(bgv) and _ratio(bgv, own_bg) < 1.10:
            weak_own.append((name, bgv, round(_ratio(bgv, own_bg), 3)))

    # 第 6 条：背景强度（相对各自编辑器底）不得低于官方 0.85×
    off_bg = off.get("TEXT", {}).get("BACKGROUND", "191a1c")
    my_bg = mine.get("TEXT", {}).get("BACKGROUND", "1f3027")
    weak = []
    for name, d in off.items():
        m = mine.get(name)
        if not m or not _is_hex(d.get("BACKGROUND")) or not _is_hex(m.get("BACKGROUND")):
            continue
        if name in STRENGTH_EXEMPT:
            continue
        # 只对"我们自选的色"判强度：逐字照抄官方 hex 的键，相对强度会因
        # 底色更亮而天然下降（同一 hex 在 #191A1C 与 #1F3027 上比值不同），
        # 那不是我们的选择，不该按同一标准判失败。
        if m["BACKGROUND"].lower() == d["BACKGROUND"].lower():
            continue
        ro = _ratio(d["BACKGROUND"], off_bg)
        rm = _ratio(m["BACKGROUND"], my_bg)
        if rm < ro * STRENGTH_MIN:
            weak.append((name, d["BACKGROUND"], round(ro, 2), m["BACKGROUND"], round(rm, 2),
                         round(rm / ro, 2)))
    # 规则 10：风格家族一致性
    fam_bad = []
    for canon, pat in FAMILIES:
        if canon not in mine:
            continue
        want = mine[canon].get("FONT_TYPE")
        for name, m in mine.items():
            if name == canon or not re.search(pat, name) or name in FAMILY_EXEMPT:
                continue
            if m.get("FONT_TYPE") != want:
                fam_bad.append((name, want, m.get("FONT_TYPE")))
    if verbose:
        print("    风格家族不一致（同族键的 FONT_TYPE 必须与规范键相同）：%d %s"
              % (len(fam_bad), fam_bad[:6] or "✅"))
        print("    FONT_TYPE 与官方不同：%d %s" % (len(diff_ft), diff_ft or "✅"))
        print("    官方有 ERROR_STRIPE_COLOR 而我缺失：%d %s"
              % (len(missing_stripe), missing_stripe or "✅"))
        print("    自建键（官方未定义）里底色过弱(<1.10:1)：%d %s"
              % (len(weak_own), weak_own or "✅"))
        n_ex = len(STRENGTH_EXEMPT)
        if weak:
            print("    背景强度低于官方 %.2f×：%d 个（其中 %d 个已豁免）"
                  % (STRENGTH_MIN, len(weak), n_ex))
            for w in weak:
                print("      - %s 官方 %s(%.2f×) → 本主题 %s(%.2f×)，比值 %.2f"
                      % (w[0], w[1], w[2], w[3], w[4], w[5]))
        else:
            print("    背景强度低于官方 %.2f×：0 个（豁免表 %s）"
                  % (STRENGTH_MIN, "空" if n_ex == 0 else "仍有 %d 条：%s"
                     % (n_ex, list(STRENGTH_EXEMPT))))
    return {"missing_et": missing_et, "diff_et": diff_et, "missing_ec": missing_ec,
            "absent": absent, "missing_bg": missing_bg, "weak": weak,
            "diff_ft": diff_ft, "missing_stripe": missing_stripe, "weak_own": weak_own,
            "fam_bad": fam_bad}


def main():
    from palette import PALETTES, icls_path
    off, dar = load_reference()
    print("同名属性块对比（标尺：effective(官方 Islands Dark, Darcula)，含 baseAttributes 展开）")
    total = 0
    for key, pal in sorted(PALETTES.items()):
        path = icls_path(pal)
        if not os.path.exists(path):
            print("  [%s] 缺少产物 %s（先跑 gen_icls.py）" % (key, os.path.relpath(path)))
            return 1
        res = check_one(off, read(path), "%s「%s」" % (pal["name"], pal["label"]), dar=dar)
        n = sum(len(v) for v in res.values())
        total += n
        if n:
            print("    ❌ 与官方存在 %d 处差异" % n)
    if total:
        print("\n❌ 两款方案合计 %d 处差异" % total)
        return 1
    print("\n✅ 两款方案都与官方逐键一致（装饰类型 / 效果色 / 底色 / 背景强度 全 0 差异）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
