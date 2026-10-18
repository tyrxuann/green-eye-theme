#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
渲染"整站 UI"仿真图：左侧工具窗（项目树）+ 编辑器 + 补全弹窗 + 状态栏。
用来验证面板/弹窗是否真的被染色，而不只是编辑区。
"""
import argparse, os, sys
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from palette import PALETTES

PALETTE_KEY = "dark"   # 由 main 覆盖
from render_preview import F, S, LINE_H, PAD_TOP, GUTTER_W, FONT_SIZE, draw_run, run_width
from render_java import JAVA, JAVA_TOKENS

SMALL = 11 * S


def render_ui(pal, code=JAVA, toks=None, W=1180, H=620):
    ui_base = pal.get("ui_base", pal["bg_panel"])
    ui_surface = pal.get("ui_surface", pal["bg_raised"])
    ui_hover = pal.get("ui_hover", pal["bg_caret_row"])
    img = Image.new("RGB", (W * S, H * S), ui_base)
    d = ImageDraw.Draw(img)
    menubar, tab_h, status_h = 26, 32, 24
    tree_w = 258
    f_code = F.get(FONT_SIZE * S)

    # 菜单栏
    d.rectangle([0, 0, W * S, menubar * S], fill=ui_base)
    for i, t in enumerate(["File", "Edit", "View", "Navigate", "Code", "Run", "Tools"]):
        draw_run(d, (12 + i * 62) * S, 6 * S, t, SMALL, pal["fg_dim"])
    # 左上角三个圆点（macOS 交通灯占位）
    for i, c in enumerate(["#F97884", "#D8BE78", "#89BC90"]):
        d.ellipse([(12 + i * 16) * S, 8 * S, (20 + i * 16) * S, 16 * S], fill=c)

    # 工具窗（左侧）
    ty = menubar * S
    d.rectangle([0, ty, tree_w * S, (H - status_h) * S], fill=ui_base)
    d.line([tree_w * S, ty, tree_w * S, (H - status_h) * S], fill=pal["indent_guide"], width=S)
    d.text((10 * S, ty + 7 * S), "项目", font=F.get(SMALL, cjk=True), fill=pal["fg"])
    d.text((tree_w * S - 12 * S, ty + 7 * S), "⋯", font=F.get(SMALL), fill=pal["fg_dim"], anchor="ra")
    d.line([0, ty + 26 * S, tree_w * S, ty + 26 * S], fill=pal["indent_guide"], width=S)
    tree = [("▾ src", 0, "fg"), ("▾ forest", 1, "fg"), ("CarbonCalculator.java", 2, "fg"),
            ("Plot.java", 2, "fg"), ("PlotTest.java", 2, "fg_dim"),
            ("▸ resources", 1, "fg"), ("▾ test", 1, "fg")]
    sel_row = 2
    for i, (label, depth, col) in enumerate(tree):
        y = ty + (34 + i * 22) * S
        if i == sel_row:
            d.rectangle([4 * S, y - 3 * S, (tree_w - 4) * S, y + 19 * S], fill=pal["bg_selection"])
        d.text(((10 + depth * 14) * S, y), label, font=F.get(SMALL, cjk=True),
               fill=pal["fg_sel"] if i == sel_row else pal[col])

    # 编辑器区
    ex = tree_w
    d.rectangle([ex * S, ty, W * S, (H - status_h) * S], fill=pal["bg_editor"])
    # 标签页
    d.rectangle([ex * S, ty, W * S, ty + tab_h * S], fill=ui_base)
    for i, (name, active) in enumerate([("CarbonCalculator.java", True), ("Plot.java", False)]):
        tx = ex + i * 190
        if active:
            d.rectangle([tx * S, ty, (tx + 186) * S, (ty + tab_h * S)], fill=pal["bg_editor"])
            d.rectangle([tx * S, ty, (tx + 186) * S, ty + 2 * S], fill=pal["tab_underline"])
        d.text(((tx + 12) * S, ty + 9 * S), name, font=F.get(SMALL), fill=pal["fg"] if active else pal["fg_dim"])
    # 面包屑
    ey = ty + tab_h * S
    d.rectangle([ex * S, ey, W * S, ey + 22 * S], fill=pal["bg_editor"])
    d.text(((ex + 12) * S, ey + 5 * S), "CarbonCalculator  ›  summarize()", font=F.get(SMALL), fill=pal["fg_dim"])
    body = ey + 22 * S
    # 行号槽
    d.rectangle([ex * S, body, (ex + GUTTER_W) * S, (H - status_h) * S], fill=pal["bg_editor"])
    n = min(len(code.split("\n")), 19)
    in_code = False
    shown = 0
    for i, line in enumerate(code.split("\n")):
        if not in_code:
            if "summarize(List<Plot>" in line:
                in_code = True
            else:
                continue
        if shown >= n:
            break
        y = body + (PAD_TOP + shown * LINE_H) * S
        if shown == 3:
            d.rectangle([(ex + 1) * S, y, W * S, y + LINE_H * S], fill=pal["bg_caret_row"])
        d.text(((ex + GUTTER_W - 10) * S, y), str(i + 1), font=f_code,
               fill=pal["line_numbers_active"] if shown == 3 else pal["line_numbers"], anchor="ra")
        cx = (ex + GUTTER_W + 8) * S
        for text, key in toks[i]:
            cx = draw_run(d, cx, y, text, FONT_SIZE * S, pal[key])
        shown += 1

    # 提示：本图不画错误波浪线，避免与状态栏"1 warning"矛盾
    # 补全弹窗（浮层）—— 验证 bg_raised / 边框 / 选中行 是否被染色
    pw, ph = 380, 210
    px, py = ex + 300, body + 150 * S
    d.rectangle([px * S - S, py - S, (px + pw) * S, py + ph * S],
                fill=ui_surface, outline=pal["indent_guide"], width=S)
    d.text(((px + 12) * S, py + 8 * S), "补全", font=F.get(SMALL, cjk=True), fill=pal["fg_dim"])
    d.line([px * S, py + 26 * S, (px + pw) * S, py + 26 * S], fill=pal["indent_guide"], width=S)
    items = [("summarize", "Map<String, Double>", False), ("stream", "Stream<T>", False),
             ("size", "int", True), ("sort", "Stream<T>", False),
             ("spliterator", "Spliterator<T>", False), ("substring", "String", False)]
    for i, (name, typ, active) in enumerate(items):
        y = py + (32 + i * 27) * S
        if active:
            d.rectangle([(px + 2) * S, y - 3 * S, (px + pw - 2) * S, y + 21 * S], fill=pal["bg_selection"])
        draw_run(d, (px + 14) * S, y, name, SMALL, pal["fg_sel"] if active else pal["function"])
        draw_run(d, (px + 140) * S, y, typ, SMALL, pal["fg_dim"])
    d.text(((px + pw - 12) * S, py + 8 * S), "Ctrl+Space", font=F.get(SMALL), fill=pal["fg_dim"], anchor="ra")

    # 状态栏
    sy = (H - status_h) * S
    d.rectangle([0, sy, W * S, H * S], fill=ui_base)
    d.line([0, sy, W * S, sy], fill=pal["indent_guide"], width=S)
    d.text((12 * S, sy + 5 * S), "  master   ✓ 0 errors   1 warning", font=F.get(SMALL), fill=pal["fg_dim"])
    d.text((430 * S, sy + 5 * S), "Java 21 · 护眼绿色主题", font=F.get(SMALL, cjk=True), fill=pal["fg_dim"])
    d.text((W * S - 12 * S, sy + 5 * S), "UTF-8   LF   Ln 34, Col 5",
           font=F.get(SMALL), fill=pal["fg_dim"], anchor="ra")
    return img.resize((W, H), Image.LANCZOS)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "preview"))
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    # 两款主题各出一张整站图，便于比较 UI 层级而不只看代码颜色。
    for key in ("dark", "mineral"):
        img = render_ui(PALETTES[key], JAVA, JAVA_TOKENS)
        img.save(os.path.join(a.outdir, "ui-%s.png" % key))
        print("写入 ui-%s.png" % key, img.size)
