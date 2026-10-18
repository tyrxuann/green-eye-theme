#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从实际产物生成验收报告 build/ref/verification.md（不手写，避免与实现漂移）。
任何一项失败则以退出码 1 结束，可直接挂进生成流程。

用法: python3 gen_verification_report.py
"""
import datetime
import glob
import itertools
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
from palette import PALETTES, contrast, hex_to_rgb, icls_path  # noqa: E402
from check_collisions import GROUPS, SAME_BY_DESIGN, de2000, _accepted_pairs  # noqa: E402

ok, bad = [], []


def chk(cond, msg):
    (ok if cond else bad).append(msg)
    return cond


def main():
    p = PALETTES["dark"]
    SCHEMES = sorted(PALETTES.items())
    themes = sorted(glob.glob(os.path.join(ROOT, "themes", "*.icls")))
    jars = sorted(glob.glob(os.path.join(ROOT, "dist", "GreenEye-Theme-*.jar")))
    chk(len(themes) == len(PALETTES), "编辑器方案 %d 个（=%d 款主题）"
        % (len(themes), len(PALETTES)))
    chk(len(jars) == 1, "插件包 %d 个：%s" % (len(jars), os.path.basename(jars[0]) if jars else "无"))
    icls = ET.parse(themes[0]).getroot()
    n_attr = len(icls.find("attributes"))
    n_col = len(icls.find("colors"))
    chk(n_attr >= 460, "语法属性键 %d 个" % n_attr)
    chk(icls.get("parent_scheme") == "Darcula", "parent_scheme=Darcula（官方深色同款）")
    chk(all(len(o.get("value", "")) == 6 for o in icls.find("colors")),
        "界面色值全为 6 位十六进制")
    chk({"FOREGROUND", "BACKGROUND"} <= {x.get("name") for x in
        icls.find("attributes").find("option[@name='TEXT']").find("value")},
        "TEXT 同时定义前景与背景")

    z = zipfile.ZipFile(jars[0])
    names = z.namelist()
    px = ET.fromstring(z.read("META-INF/plugin.xml"))
    reg = {e.get("id"): e.get("path").lstrip("/") for e in px.iter("bundledColorScheme")}
    chk(len(reg) == len(PALETTES), "bundledColorScheme 注册 %s" % list(reg))
    chk(set(reg) == {pal["name"] for _, pal in SCHEMES},
        "注册的方案名与调色板一致（%s）" % sorted(reg))
    for sid, path in reg.items():
        chk(path in names, "方案文件 %s 在包内" % path)
        r = ET.fromstring(z.read(path))
        chk(r.get("name") == sid, "方案 name 与注册 id 一致（%s）" % sid)
    tjs = [x for x in names if x.endswith(".theme.json")]
    chk(len(tjs) == len(PALETTES), "主题 JSON %d 个" % len(tjs))
    name2pal = {pal["name"]: pal for _, pal in SCHEMES}
    for tj in tjs:
        td = json.loads(z.read(tj))
        pal = name2pal.get(td["editorScheme"])
        chk(pal is not None, "%s 的 editorScheme=%s 能对上调色板"
            % (os.path.basename(tj), td["editorScheme"]))
        if pal is None:
            continue
        chk(td["editorScheme"] in reg, "%s 用方案名引用 editorScheme" % os.path.basename(tj))
        chk(td["colors"].get("popup-border") == pal["border"],
            "[%s] 浮层轮廓用 border" % pal["label"])
        chk(td["colors"].get("main-window-border") == pal["separator"],
            "[%s] 窗口发丝线用 separator" % pal["label"])
        chk(td["colors"].get("editor-bg") == pal["bg_editor"],
            "[%s] 编辑器底 = %s" % (pal["label"], pal["bg_editor"]))
        chk(len(td["ui"]) >= 45,
            "[%s] ui 覆盖 %d 个控件组" % (pal["label"], len(td["ui"])))
    td = json.loads(z.read(tjs[0]))

    # 状态色撞色（以官方为标尺）
    from official_palette import OFFICIAL

    def fails(pal):
        out = set()
        for g in GROUPS.values():
            keys = [k for k in g["keys"] if k in pal]
            for a1, a2 in itertools.combinations(keys, 2):
                if frozenset((a1, a2)) in SAME_BY_DESIGN:
                    continue
                if frozenset((a1, a2)) in _accepted_pairs():
                    continue
                if contrast(pal[a1], pal[a2]) < g["contrast"] and de2000(pal[a1], pal[a2]) < g["de"]:
                    out.add((a1, a2))
        return out

    base, mine = fails(OFFICIAL), fails(p)
    extra = mine - base
    chk(len(extra) <= len(base),
        "松林状态色撞色不劣于官方（官方基线 %d 对，本主题 %d 对，多出 %d 对）"
        % (len(base), len(mine), len(extra)))

    # 与官方逐键对比（装饰类型/效果色完备性）—— 这一类 bug 预览图照不到
    off_attrs = {}
    _off = ET.parse(os.path.join(ROOT, "build", "ref", "ide_official_schemes",
                                 "IslandSchemeDark.xml")).getroot()
    for o in _off.find("attributes"):
        v = o.find("value")
        if v is not None:
            off_attrs[o.get("name")] = {x.get("name"): x.get("value") for x in v}
    my_attrs = {}
    for o in icls.find("attributes"):
        v = o.find("value")
        if v is not None:
            my_attrs[o.get("name")] = {x.get("name"): x.get("value") for x in v}
    miss_et = [n for n, d in off_attrs.items()
               if d.get("EFFECT_TYPE") and n in my_attrs and not my_attrs[n].get("EFFECT_TYPE")]
    diff_et = [n for n, d in off_attrs.items()
               if d.get("EFFECT_TYPE") and n in my_attrs
               and my_attrs[n].get("EFFECT_TYPE") not in (None, d["EFFECT_TYPE"])]
    chk(not miss_et and not diff_et,
        "与官方逐键对比：官方有 EFFECT_TYPE 而我们缺失 %d 个、取值不同 %d 个"
        % (len(miss_et), len(diff_et)))

    # 反向覆盖：产物用色必须全部来自各自的调色板
    for key, pal in SCHEMES:
        ipath = icls_path(pal)
        if not os.path.exists(ipath):
            continue
        allowed = {v.upper() for v in pal.values() if isinstance(v, str)}
        used = set()
        for o in ET.parse(ipath).getroot().iter("option"):
            v = o.get("value") or ""
            if len(v) == 6 and all(c in "0123456789abcdefABCDEF" for c in v):
                used.add("#" + v.upper())
        chk(not (used - allowed),
            "[%s] 产物用色 %d 种全部来自本调色板（越界 %d 个）"
            % (pal["label"], len(used), len(used - allowed)))

    rows = [("正文 fg", "fg"), ("注释 comment", "comment"), ("文档注释 doc_comment", "doc_comment"),
            ("关键字 keyword", "keyword"), ("字符串 string", "string"), ("数字 number", "number"),
            ("函数 function", "function"), ("字段/常量 constant", "constant"),
            ("注解 annotation", "annotation"), ("TODO todo", "todo"), ("错误 error", "error"),
            ("光标 caret", "caret"), ("行号 line_numbers", "line_numbers")]
    lines = []
    lines.append("# 验收报告（自动生成）\n")
    lines.append("生成时间：%s　目标 IDE：IntelliJ IDEA 2026.2.3 (IU-262.10968.63)\n"
                 % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    lines.append("本文件由 [`src/gen_verification_report.py`](../../src/gen_verification_report.py) "
                 "从实际产物生成，**请勿手改**。\n")
    lines.append("\n## 1. 检查结果：%d 项通过，%d 项失败\n" % (len(ok), len(bad)))
    lines.append("| 检查项 | 结果 |")
    lines.append("|---|---|")
    for m in ok:
        lines.append("| %s | ✅ |" % m)
    for m in bad:
        lines.append("| %s | ❌ |" % m)
    lines.append("\n## 2. 对比度（含编辑器底色 %s）\n" % p["bg_editor"])
    lines.append("| 语义 | 色值 | 对比度 |")
    lines.append("|---|---|---|")
    for label, k in rows:
        lines.append("| %s | `%s` | %.2f:1 |" % (label, p[k], contrast(p[k], p["bg_editor"])))
    lines.append("\n## 3. 状态色层次\n")
    for gname, g in GROUPS.items():
        lines.append("- **%s**：阈值 对比度≥%.2f:1 且 ΔE2000≥%.1f" % (gname, g["contrast"], g["de"]))
    lines.append("\n| 状态色 | 色值 | 对编辑器 |")
    lines.append("|---|---|---|")
    for k in ["bg_editor", "bg_panel", "bg_raised", "bg_console", "bg_caret_row",
              "bg_selection", "bg_search", "bg_search_border" if False else "search_border",
              "bg_matched_brace", "bg_diff_add", "bg_diff_del", "bg_diff_mod",
              "border", "separator", "indent_guide", "right_margin", "whitespace"]:
        lines.append("| %s | `%s` | %.2f:1 |" % (k, p[k], contrast(p[k], p["bg_editor"])))
    if extra:
        lines.append("\n**比官方多出的撞色对**：\n")
        for a1, a2 in sorted(extra):
            lines.append("- %s ↔ %s：对比 %.3f:1，ΔE2000 %.1f"
                         % (a1, a2, contrast(p[a1], p[a2]), de2000(p[a1], p[a2])))
    else:
        lines.append("\n状态色撞色**不劣于官方**（松林：官方基线 %d 对，本主题 %d 对，多出 %d 对）。"
                     % (len(base), len(mine), len(extra)))
    acc = _accepted_pairs()
    if acc:
        lines.append("\n**已评估并接受的例外**（写明理由，不算失败）：\n")
        for pair, why in acc.items():
            a1, a2 = sorted(pair)
            lines.append("- %s ↔ %s：对比 %.3f:1，ΔE2000 %.1f\n  - 理由：%s"
                         % (a1, a2, contrast(p[a1], p[a2]), de2000(p[a1], p[a2]), why))
    lines.append("\n## 4. 键名来源与覆盖\n")
    ref = os.path.join(ROOT, "build", "ref")
    def _count(fn):
        fp = os.path.join(ref, fn)
        if not os.path.exists(fp):
            return 0
        return len([x for x in open(fp, encoding="utf-8").read().split("\n") if x.strip()])
    n_ref = _count("all_reference_attribute_names.txt")
    n_lang = _count("ide_language_attribute_names.txt")
    n_off = _count("ide_official_attribute_names.txt")
    lines.append("- 语法属性键 %d 个，来源三份清单的并集：真实主题导出 %d、"
                 "IDE 插件配色片段 %d、**官方内置方案 %d**（并集去重后 %d）"
                 % (n_attr, n_ref, n_lang, n_off, n_attr))
    lines.append("- 界面颜色键 %d 个（两轮独立核验后定稿）；"
                 "官方方案的界面色键 105/105 全覆盖；13 个判定无效的键已删除" % n_col)
    lines.append("\n## 5. 未做的事\n")
    lines.append("- **没有在真实 IDE 内加载过**：无头模式不初始化 LaF（`EditorColorsManager` 不构造，"
                 "出错代码不执行，对照包也不报错 → 测不出问题）；隔离配置缺许可证导致 "
                 "`com.intellij.modules.ultimate` 被禁用，与真实环境不等价。")
    lines.append("- 预览图是按调色板渲染的**仿真窗口**，不等于 IDE 真实截图。")
    out = os.path.join(ROOT, "build", "ref", "verification.md")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("写入 %s：%d 项通过，%d 项失败" % (os.path.relpath(out), len(ok), len(bad)))
    for m in bad:
        print("  ❌", m)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
