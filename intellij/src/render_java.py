#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
以 Java 代码为样例渲染对照图。

Java 是检验配色最苛刻的用例：类型引用、泛型、注解、Javadoc 密度都很高，
能直接暴露"类名用中性色"这条官方规律在 Java 里到底好不好看。

输出:
    preview/java-official-vs-new.png   官方 Islands Dark | 新版绿色 | 旧版 A
    preview/java-new.png               新版单独（含色板）
    preview/java-official.png          官方单独（含色板）
"""
import argparse
import os
import re
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from palette import contrast  # noqa: E402
from official_palette import OFFICIAL, GREEN  # noqa: E402
from candidates import CANDIDATES  # noqa: E402
from render_preview import render, swatch, S, F, draw_run, run_width  # noqa: E402

JAVA = '''package com.greeneye.forest;

import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.stream.Collectors;

/**
 * 碳汇估算器。
 *
 * @author greeneye
 */
public class CarbonCalculator implements Calculator<Plot> {

    /** 默认含碳系数。 */
    public static final double DEFAULT_COEFFICIENT = 0.48;

    private final double coefficient;
    private int calls;

    public CarbonCalculator(double coefficient) {
        this.coefficient = coefficient;
    }

    /**
     * 估算生物量。
     *
     * @param plots 样地列表
     * @param verbose 是否输出明细
     * @return 每公顷生物量 (t/ha)
     * @throws IllegalArgumentException 列表为空时
     */
    @Override
    public Map<String, Double> summarize(List<Plot> plots, boolean verbose) {
        if (Objects.isNull(plots) || plots.isEmpty()) {
            throw new IllegalArgumentException("样地列表不能为空: " + plots);
        }
        this.calls++;
        Map<String, Double> r = plots.stream().collect(
                Collectors.toMap(Plot::id, p -> p.biomass(coefficient)));
        double mean = r.values().stream().mapToDouble(Double::doubleValue)
                .average().orElse(0.0);   // TODO 空集合应返回 Optional
        if (verbose) {
            System.out.printf("样地 %d 块，均值 %.3f t/ha%n", r.size(), mean);
        }
        return r;
    }

    @Override
    public String toString() {
        return "CarbonCalculator[coef=" + coefficient + ", calls=" + calls + "]";
    }
}'''

KEYWORDS = """package import public private protected static final abstract class
interface enum record sealed permits extends implements new return if else for while
do switch case default break continue throw throws try catch finally instanceof
synchronized volatile transient native strictfp assert var void boolean byte short
int long float double char null true false this super yield""".split()

MASTER = re.compile(r"""
   (?P<doc>/\*\*[\s\S]*?\*/)
 | (?P<block>/\*[\s\S]*?\*/)
 | (?P<linecomment>//[^\n]*)
 | (?P<string>"(?:\\.|[^"\\])*")
 | (?P<char>'(?:\\.|[^'\\])*')
 | (?P<annotation>@[A-Za-z_]\w*)
 | (?P<number>\b(?:0[xX][0-9a-fA-F_]+|\d[\d_]*(?:\.\d+)?(?:[eE][-+]?\d+)?[fFdDlL]?)\b)
 | (?P<keyword>\b(?:%s)\b)
 | (?P<constant>\b[A-Z][A-Z0-9_]{1,}\b)
 | (?P<typeparam>(?<=<)[A-Z]\b)
 | (?P<mrefname>(?<=::)[A-Za-z_]\w*)
 | (?P<capital>\b[A-Z]\w*\b)
 | (?P<call>\b[a-z_]\w*(?=\s*\())
 | (?P<methodref>::)
 | (?P<arrow>->)
 | (?P<op>[-+*/%%=<>!&|^~?]+)
 | (?P<brk>[(){}\[\]])
 | (?P<punct>[,;.])
""" % "|".join(KEYWORDS), re.X)

# 正则组名 -> 调色板键
GROUP = {
    "doc": "doc_comment", "block": "comment", "linecomment": "comment",
    "string": "string", "char": "string", "annotation": "annotation",
    "number": "number", "keyword": "keyword", "constant": "constant",
    "typeparam": "type_param", "mrefname": "function", "capital": "class_name",
    "call": "function_call", "methodref": "operator", "arrow": "operator",
    "op": "operator", "brk": "brace", "punct": "punctuation",
}
# 只认反斜杠转义；printf 的 %d/%n 不算转义（真实 IDE 也不高亮它们）
ESCAPE_IN_STRING = re.compile(r"\\.")


def tokenize_java(code):
    """返回逐行的 [(文本, 调色板键), ...]；按"先占先得"处理优先级。"""
    n = len(code)
    keys = [None] * n

    def claim(s, e, key):
        for i in range(s, e):
            if keys[i] is None:
                keys[i] = key

    # 第一遍：Javadoc 里的 @tag 优先级最高，其次是字符串里的转义
    spans = []
    for m in MASTER.finditer(code):
        g = m.lastgroup
        if g == "doc":
            # Javadoc 的 @param/@return 是 doc_tag（官方 #67a37c，绿色注释家族），
            # 不是 annotation（#b3ae60，给 @Override 这类注解用）
            for sub in re.finditer(r"@\w+", m.group()):
                spans.append((m.start() + sub.start(), m.start() + sub.end(), "doc_tag"))
        elif g in ("string", "char"):
            for sub in ESCAPE_IN_STRING.finditer(m.group()):
                spans.append((m.start() + sub.start(), m.start() + sub.end(), "escape"))
        spans.append((m.start(), m.end(), GROUP.get(g, "fg")))
    # 高优先级的放前面：annotation/escape 先占
    pri = {"annotation": 0, "escape": 1}
    for s, e, k in sorted(spans, key=lambda x: pri.get(x[2], 9)):
        claim(s, e, k)

    # 字段名后处理：找出类级字段声明，把裸出现的字段名从"中性"改为 field（官方里字段是紫色）
    fields = set(re.findall(
        r"^\s*(?:public|private|protected)?\s*(?:static\s+)?(?:final\s+)?"
        r"[A-Za-z_][\w<>\[\], .]*?\s+([a-z_]\w*)\s*(?:=|;)", code, re.M))
    if fields:
        for i, k in enumerate(keys):
            if k == "fg":
                pass
        # 逐字符回填：仅把"中性"区间里正好等于字段名的连续标识符改成 field
        # 参数不是字段：① 签名行整行跳过；② 含 this. 的行只认 this. 后面的那个
        sig_lines, this_lines = set(), set()
        for ln, line_text in enumerate(code.split("\n")):
            if re.match(r"^\s*(?:public|private|protected|static|final|abstract|"
                        r"\w[\w<>\[\], .]*)\s+\w+\s*\(.*\)\s*\{?\s*$", line_text) \
                    and "=" not in line_text:
                sig_lines.add(ln)
            if "this." in line_text:
                this_lines.add(ln)
        line_of = [0] * (len(code) + 1)
        ln = 0
        for i, ch in enumerate(code):
            line_of[i] = ln
            if ch == "\n":
                ln += 1
        for m in re.finditer(r"\b([a-z_]\w*)\b", code):
            ln = line_of[m.start()]
            is_this = code[max(0, m.start() - 5):m.start()].endswith("this.")
            if m.group(1) in fields and ln not in sig_lines \
                    and (ln not in this_lines or is_this) \
                    and all(keys[i] in (None, "fg") for i in range(m.start(), m.end())):
                for i in range(m.start(), m.end()):
                    keys[i] = "field"

    # 第二遍：连续相同的字符合成一段
    out, i = [], 0
    per_line = [[]]
    while i < n:
        k = keys[i] or "fg"
        j = i
        while j < n and (keys[j] or "fg") == k:
            j += 1
        text = code[i:j]
        parts = text.split("\n")
        for idx, part in enumerate(parts):
            if idx:
                per_line.append([])
            if part:
                per_line[-1].append((part, k))
        i = j
    return per_line


def compose(items, path, gap=16, lab=34):
    """items: [(标题, 调色板)]；每列 = 代码窗口 + 色板。"""
    shots = {}
    for tag, p in items:
        shots[tag] = (render(p, JAVA, line_tokens=JAVA_TOKENS, caret_line=41,
                             sel_lines={17}, wave_line=37, sel_span=(170, 330),
                             show_margin=False,
                             breadcrumb="CarbonCalculator.java  ›  src  ›  forest",
                             tabs=("CarbonCalculator.java", "Plot.java"),
                             status_mid="Java 21"),
                       swatch(p))
    any_img = shots[items[0][0]][0]
    W = (any_img.width + gap) * len(items) + gap
    H = lab + any_img.height + shots[items[0][0]][1].height + 16
    img = Image.new("RGB", (W, H), "#0C110F")
    d = ImageDraw.Draw(img)
    for i, (tag, p) in enumerate(items):
        x = gap + i * (any_img.width + gap)
        title = "%s   %s   %s" % (tag, p["label"], p["bg_editor"])
        draw_run(d, x + (any_img.width - run_width(d, title, 24)) / 2, 6,
                 title, 24, "#E6EDE9")
        img.paste(shots[tag][0], (x, lab))
        img.paste(shots[tag][1], (x, lab + any_img.height))
    img.save(path)
    print("写入", os.path.basename(path))


# 渲染样式映射：与 themes/*.icls 里对应键的 FONT_TYPE 必须一致（由
# check_render_styles.py 强制校验，避免"渲染器和产物各说各话"）
STYLE_BY_KEY = {
    "doc_comment": "i",    # DEFAULT_DOC_COMMENT 官方斜体
    "todo": "i",           # 官方 TODO 斜体
    "constant": "i",       # 官方常量/静态成员斜体
}
# 说明：DEFAULT_STATIC_METHOD 官方是斜体，但 mock 的 tokenizer 分不清
# "静态方法调用"与"实例方法调用"，把全部方法名画成斜体是错的，所以这里不画；
# 这一条由 check_render_styles.py 记为"已知 mock 限制"。

JAVA_TOKENS = tokenize_java(JAVA)


def main():
    """渲染主线预览：同一段 Java 代码，官方 / 松林 / 矿彩三方并排。"""
    from palette import PALETTES
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "preview"))
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    cur = dict(PALETTES["dark"])
    cur["label"] = "松林"
    mineral = dict(PALETTES["mineral"])
    items = [("官方", OFFICIAL), ("松林", cur), ("矿彩", mineral)]
    compose(items, os.path.join(a.outdir, "current-vs-official.png"))
    from render_candidates import swatch_matrix
    swatch_matrix(dict(items), os.path.join(a.outdir, "current-swatches.png"))
    names = {"官方": "official", "松林": "current", "矿彩": "mineral"}
    for tag, p in items:
        img = render(p, JAVA, line_tokens=JAVA_TOKENS, caret_line=41, sel_lines={17},
                     wave_line=37, sel_span=(170, 330), show_margin=False,
                     wave_color=p.get("warning_stripe") or p.get("error"),
                     token_styles=STYLE_BY_KEY, breadcrumb="CarbonCalculator.java  ›  src  ›  forest",
                     tabs=("CarbonCalculator.java", "Plot.java"), status_mid="Java 21")
        sw = swatch(p)
        c = Image.new("RGB", (img.width, img.height + sw.height), p["bg_editor"])
        c.paste(img, (0, 0))
        c.paste(sw, (0, img.height))
        c.save(os.path.join(a.outdir, "java-%s.png" % names[tag]))
        print("写入 java-%s.png" % names[tag])
    # 1:1 局部裁剪：便于逐像素核对字段紫色与浮层
    from make_crops import make_crops
    make_crops(a.outdir)
    for label, pal in (("松林", cur), ("矿彩", mineral)):
        print("\n[%s] 各语义对比度（编辑器底 %s）：" % (label, pal["bg_editor"]))
        for k in ("fg", "fg_dim", "comment", "doc_comment", "keyword", "string", "number",
                  "function", "constant", "annotation", "warning", "todo", "error",
                  "caret", "line_numbers"):
            print("   %-12s %-9s %5.2f:1" % (k, pal[k], contrast(pal[k], pal["bg_editor"])))


if __name__ == "__main__":
    main()
