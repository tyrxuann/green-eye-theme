#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
渲染三套候选配色的对比图，供挑选方向。

输出:
    preview/candidates-swatches.png  色板矩阵（行=语义色，列=候选，带十六进制）
    preview/candidates-code.png      三套代码预览并排
    preview/candidate-A/B/C.png      每套的单独完整预览
"""
import argparse
import os
import sys
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from palette import DARK, contrast  # noqa: E402
from candidates import CANDIDATES  # noqa: E402
from render_preview import render, swatch, CODE, F, draw_run, run_width  # noqa: E402

S = 2
ROWS = ["bg_editor", "bg_panel", "bg_raised", "bg_selection", "bg_caret_row",
        "fg", "fg_dim", "comment", "keyword", "class_name", "type_param",
        "function", "string", "number", "constant", "annotation", "error",
        "warning", "todo", "hyperlink", "caret", "line_numbers",
        "indent_guide", "bg_diff_add", "bg_diff_del", "bg_diff_mod",
        "bg_matched_brace", "bg_inlay_hint",
        "bg_search_current", "bg_folded", "border", "separator"]
ZH = {
    "bg_editor": "编辑器底", "bg_panel": "面板/侧栏", "bg_raised": "弹窗/浮层",
    "bg_selection": "选中背景", "bg_caret_row": "当前行",
    "fg": "正文", "fg_dim": "次要文字", "comment": "注释", "keyword": "关键字",
    "class_name": "类名/类型", "type_param": "类型参数", "function": "函数/方法",
    "string": "字符串", "number": "数字", "constant": "常量/静态",
    "annotation": "注解/装饰器", "error": "错误", "warning": "警告",
    "todo": "TODO", "hyperlink": "链接", "caret": "光标/行号激活",
    "line_numbers": "行号", "indent_guide": "缩进参考线",
    "bg_diff_add": "新增行", "bg_diff_del": "删除行", "bg_diff_mod": "修改行",
    "bg_matched_brace": "匹配括号",
    "bg_inlay_hint": "参数提示芯片", "bg_search_current": "当前匹配",
    "bg_folded": "折叠区", "border": "浮层轮廓", "separator": "窗口发丝线",
}


def ink(bg_hex):
    """在给定底色上挑一个可读的文字色。"""
    return "#12181A" if contrast("#FFFFFF", bg_hex) > 4.5 else "#F2F6F3"


def swatch_matrix(pals, path, hi_res=True):
    lab_w, cell_w, row_h, head = 230, 330, 40, 104
    W = lab_w + cell_w * len(pals) + 24
    H = head + row_h * len(ROWS) + 16
    img = Image.new("RGB", (W * S, H * S), "#12181A")
    d = ImageDraw.Draw(img)
    f_small, f_head = F.get(13 * S), F.get(17 * S)
    f_cjk = F.get(13 * S, cjk=True)
    f_cjk2 = F.get(11 * S, cjk=True)
    pal_base = list(pals.values())[0]["bg_editor"]

    for i, (tag, p) in enumerate(pals.items()):
        x = (lab_w + cell_w * i + 12) * S
        d.text((x, 10 * S), "%s  %s" % (tag, p["label"]), font=f_cjk, fill="#F2F6F3")
        d.text((x, 36 * S), "底色 %s   正文对比 %.1f:1" %
               (p["bg_editor"], contrast(p["fg"], p["bg_editor"])),
               font=f_small, fill="#9AA8A2")
        d.text((x, 54 * S), "注释对比 %.1f:1   语法对比 %.1f~%.1f:1" % (
            contrast(p["comment"], p["bg_editor"]),
            min(contrast(p[k], p["bg_editor"]) for k in
                ("number", "constant", "annotation", "type_param")),
            max(contrast(p[k], p["bg_editor"]) for k in
                ("class_name", "keyword"))), font=f_small, fill="#9AA8A2")

    # 原版作为对照列
    y0 = head * S
    for r, key in enumerate(ROWS):
        y = y0 + r * row_h * S
        if r % 2 == 0:
            d.rectangle([0, y, W * S, y + row_h * S], fill="#181F1D")
        d.text((14 * S, y + 9 * S), ZH.get(key, key), font=f_cjk, fill="#C6D2C1")
        d.text((14 * S + 96 * S, y + 10 * S), key, font=f_small, fill="#66756F")
        for i, (tag, p) in enumerate(pals.items()):
            x = (lab_w + cell_w * i + 12) * S
            cw = (cell_w - 24) * S
            val = p.get(key)
            if val is None:
                d.rectangle([x, y + 4 * S, x + cw, y + (row_h - 5) * S],
                            fill=pal_base, outline="#4A5A52", width=S)
                d.text((x + 10 * S, y + 9 * S), "官方未定义", font=f_cjk2,
                       fill="#8FA398")
                continue
            d.rectangle([x, y + 4 * S, x + cw, y + (row_h - 5) * S], fill=val)
            d.text((x + 10 * S, y + 9 * S), val, font=f_small, fill=ink(val))
            if key == "fg":
                d.text((x + cw - 10 * S, y + 9 * S), "★ 正文", font=f_small,
                       fill=ink(p[key]), anchor="ra")
    img.resize((W, H), Image.LANCZOS).save(path)
    if hi_res:
        big = path.replace(".png", "@2x.png")
        img.resize((W * 2, H * 2), Image.LANCZOS).save(big)
        print("写入", os.path.basename(big), "（2×，便于逐值对账）")
    print("写入", os.path.basename(path))


def trio(pals, path):
    gap, lab = 16, 34
    shots = {t: render(p) for t, p in pals.items()}
    sws = {t: swatch(p) for t, p in pals.items()}
    first = next(iter(shots))
    W = (shots[first].width + gap) * len(pals) + gap
    H = lab + shots[first].height + sws[first].height + 16
    img = Image.new("RGB", (W, H), "#0C110F")
    d = ImageDraw.Draw(img)
    for i, (tag, p) in enumerate(pals.items()):
        x = gap + i * (shots[first].width + gap)
        title = "%s  %s   %s" % (tag, p["label"], p["bg_editor"])
        draw_run(d, x + (shots[first].width - run_width(d, title, 24)) / 2, 6,
                 title, 24, "#E6EDE9")
        img.paste(shots[tag], (x, lab))
        img.paste(sws[tag], (x, lab + shots[tag].height))
    img.save(path)
    print("写入", os.path.basename(path))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "preview"))
    args = ap.parse_args()
    out = os.path.abspath(args.outdir)
    os.makedirs(out, exist_ok=True)

    pals = dict(CANDIDATES)
    swatch_matrix(pals, os.path.join(out, "candidates-swatches.png"))
    trio(pals, os.path.join(out, "candidates-code.png"))
    for tag, p in pals.items():
        img = render(p)
        sw = swatch(p)
        comp = Image.new("RGB", (img.width, img.height + sw.height), p["bg_editor"])
        comp.paste(img, (0, 0))
        comp.paste(sw, (0, img.height))
        comp.save(os.path.join(out, "candidate-%s.png" % tag))
        print("写入 candidate-%s.png" % tag)


if __name__ == "__main__":
    main()
