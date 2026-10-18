#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成 README 的「矿彩」设计说明：逐槽位写清"官方是什么 → 矿彩是什么 → 为什么换"。

「松林」的文档重点是"哪里有意偏离官方"（因为它的骨架就是官方的）；
「矿彩」不是从官方派生的，所以它的文档重点是**设计意图**：每个语义槽位为什么落在那个色相上。

这份文档曾经整段漂移：hex 由生成器实时读取，但"为什么"里的 H/S/ΔE 是手写的，
于是代码换过几轮色相后，文字还停留在旧版色相名。现在 H/S、ΔE、对比度
全部从 palette.py 实时计算，文字只保留不含数值的设计判断。
"""
import colorsys
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from palette import PALETTES, contrast, hex_to_rgb  # noqa: E402
from official_palette import OFFICIAL  # noqa: E402
from check_collisions import de2000  # noqa: E402

B = "<!-- MINERAL-DESIGN:BEGIN -->"
E = "<!-- MINERAL-DESIGN:END -->"


def hsl(color):
    r, g, b = [v / 255.0 for v in hex_to_rgb(color)]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return h * 360.0, s * 100.0, l * 100.0


def hue_gap(a, b):
    d = abs(hsl(a)[0] - hsl(b)[0])
    return min(d, 360.0 - d)


def why_keyword(m, o):
    oh = hsl(o)[0]
    h, s, _ = hsl(m["keyword"])
    return ("官方是**橙红**(H%.0f)，贴近「警告/危险」的语义；"
            "矿彩改用**金黄**(H%.0f S%.0f)，把「语言结构」与「出错」在色相上分开，"
            "同时更贴「矿物」这个主题词" % (oh, h, s))


def why_constant(m, o):
    oh = hsl(o)[0]
    h, s, _ = hsl(m["constant"])
    return ("官方是**紫**(H%.0f)，与字符串/函数都无关联；矿彩改用**赭石**(H%.0f S%.0f)，"
            "落在暖极深处 —— 与关键字拉开 ΔE %.1f、与错误拉开 %.1f，"
            "读起来像「沉淀下来的值」"
            % (oh, h, s, de2000(m["constant"], m["keyword"]),
               de2000(m["constant"], m["error"])))


def why_annotation(m, o):
    oh = hsl(o)[0]
    h, s, _ = hsl(m["annotation"])
    return ("官方是**橄榄**(H%.0f)，夹在关键字与字符串之间最容易被忽略；"
            "矿彩改用**玫瑰**(H%.0f S%.0f)，放到暖极的另一端，"
            "与关键字形成明确的「两端」关系。警告沿用同色（不自造色相）"
            % (oh, h, s))


def why_todo(m, o):
    oh = hsl(o)[0]
    h, s, _ = hsl(m["todo"])
    sh = hsl(m["string"])[0]
    return ("官方是黄绿(H%.0f)，与字符串绿撞车；矿彩移到**芥黄**(H%.0f S%.0f)，"
            "与字符串(冰青 H%.0f)拉开 %.1f°"
            % (oh, h, s, sh, hue_gap(m["todo"], m["string"])))


def why_string(m, o):
    oh = hsl(o)[0]
    h, s, _ = hsl(m["string"])
    bh = hsl(m["bg_editor"])[0]
    return ("官方是标准绿(H%.0f)，在绿底上「绿叠绿」；矿彩改用**冰青**(H%.0f S%.0f)，"
            "与底色 H%.0f 拉开 **%.1f°**，靠色相而不是只靠亮度站住"
            % (oh, h, s, bh, hue_gap(m["string"], m["bg_editor"])))


def why_number(m, o):
    oh, os_, _ = hsl(o)
    h, s, _ = hsl(m["number"])
    fh = hsl(m["function"])[0]
    return ("官方是**电光青**(H%.0f S%.0f)；矿彩改用**紫晶**(H%.0f S%.0f)，"
            "从「发光」变成「矿石的反光」，与函数(玉青 H%.0f)分开 %.1f°"
            % (oh, os_, h, s, fh, hue_gap(m["number"], m["function"])))


def why_function(m, o):
    oh, os_, _ = hsl(o)
    h, s, _ = hsl(m["function"])
    nh = hsl(m["number"])[0]
    return ("官方是**电光蓝**(H%.0f S%.0f)。函数是出现频率最高的彩色 token，"
            "高饱和最伤眼 —— 矿彩降到 **S%.0f**，仍与数字(紫晶 H%.0f)分开 %.1f°"
            % (oh, os_, s, nh, hue_gap(m["function"], m["number"])))


def why_doc_tag(m, o):
    h, s, _ = hsl(m["doc_tag"])
    near = min(de2000(m["doc_tag"], m["comment"]),
               de2000(m["doc_tag"], m["doc_comment"]))
    return ("早期把它放在冷极，结果与数字几乎同色；现在改用**苔石色**(H%.0f S%.0f)，"
            "归入注释层：Javadoc 标签本来就是注释的一部分，"
            "与数字拉开 ΔE %.1f，与注释/文档注释的最小 ΔE 为 %.1f"
            % (h, s, de2000(m["doc_tag"], m["number"]), near))


def why_comment(m, o):
    h, s, _ = hsl(m["comment"])
    return ("官方是中性灰。矿彩把注释做成**冷石色**(H%.0f S%.0f)：正文是暖墨、注释是冷石，"
            "同一屏里两种「温度」自然分层，注释不需要靠「更暗」来退后" % (h, s))


def why_doc_comment(m, o):
    return ("同上，冷石色 + 斜体，明度压到 %.2f:1，长 Javadoc 不会「发光」"
            % contrast(m["doc_comment"], m["bg_editor"]))


def why_bg_selection(m, o):
    oh = hsl(o)[0]
    h, s, _ = hsl(m["bg_selection"])
    sh = hsl(m["bg_search"])[0]
    return ("官方是蓝(H%.0f)。矿彩把选中定为**同相深绿**(H%.0f S%.0f)：选中是「焦点」信号，"
            "与底色同相、只靠明度抬起（%.2f:1），不引入第三套色相；"
            "查找改用琥珀(H%.0f)，用冷暖对照把两种状态分开"
            % (oh, h, s, contrast(m["bg_selection"], m["bg_editor"]), sh))


def why_bg_search(m, o):
    h, s, _ = hsl(m["bg_search"])
    return ("★ 这是矿彩最大胆的一处：官方/松林都用绿色命中；矿彩改用**琥珀**(H%.0f S%.0f)，"
            "像荧光笔划过一样明确，且与「绿底」不再互相干扰。文字在琥珀上仍有 %.1f:1"
            % (h, s, contrast(m["fg_search"], m["bg_search"])))


# (槽位, 中文名, 落在哪一极, 为什么这么定)
ROWS = [
    ("keyword", "关键字", "暖极·最亮", why_keyword),
    ("constant", "常量 / 字段", "暖极·最深", why_constant),
    ("annotation", "注解 / 警告", "暖极·另一端", why_annotation),
    ("todo", "TODO", "暖极·偏黄", why_todo),
    ("string", "字符串", "冷极·冰青", why_string),
    ("number", "数字", "冷极·紫晶", why_number),
    ("function", "函数 / 方法", "冷极·深处", why_function),
    ("doc_tag", "Javadoc 标签", "注释层·苔石", why_doc_tag),
    ("comment", "注释", "文本层·冷石", why_comment),
    ("doc_comment", "文档注释", "文本层·冷石", why_doc_comment),
    ("bg_selection", "选中", "同相·深绿", why_bg_selection),
    ("bg_search", "查找命中", "暖信号·琥珀", why_bg_search),
]


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "README.md"
    m = PALETTES["mineral"]
    lines = ["### 「矿彩」的设计意图（逐槽位）", "",
             "「矿彩」不是从官方派生的，所以这里写的不是「偏离」，而是**为什么这样定**。", "",
             "| 槽位 | 官方 Islands Dark | 矿彩 | 落在 | 为什么 |",
             "|---|---|---|---|---|"]
    for key, name, pole, why in ROWS:
        off = OFFICIAL[key]
        v = m[key]
        off_h, off_s, _ = hsl(off)
        my_h, my_s, _ = hsl(v)
        ratio = contrast(v, m["bg_editor"])
        lines.append("| **%s** %s | `%s` · H%.0f S%.0f "
                     "| `%s` · H%.0f S%.0f · %.2f:1 | %s | %s |"
                     % (name, key, off, off_h, off_s, v, my_h, my_s,
                        ratio, pole, why(m, off)))
    lines.append("")
    lines.append("**贯穿两款的一条线**：底色 `#1F3027` 不动，对比度标准不动"
                 "（正文 9:1 / 强调 6–7:1 / 注释 ~4.4:1 / 光标 10.7:1 / 行号 2.2:1），"
                 "变的是**色相怎么分配给语义**。")
    block = B + "\n" + "\n".join(lines) + "\n" + E
    s = open(path, encoding="utf-8").read()
    if B not in s:
        print("README 缺少 %s 标记" % B)
        return 1
    s = re.sub(re.escape(B) + r".*?" + re.escape(E), block, s, count=1, flags=re.S)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(s)
    print("README「矿彩设计意图」已生成（%d 个槽位）" % len(ROWS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
