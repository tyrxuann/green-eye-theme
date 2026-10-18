#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成 CVD（红/绿色盲）对比色板：normal / protanopia / deuteranopia 并排。

用于判断 CVD 变体是走"只改几对"还是"整屏重做"；不参与发布包。
需要 Pillow；`green_eye.py build --no-preview` 不会生成它。
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
INTELLIJ = HERE.parent
ROOT = INTELLIJ.parent
sys.path.insert(0, HERE)
sys.path.insert(0, str(ROOT / "shared" / "tools"))

from PIL import Image, ImageDraw  # noqa: E402

from colorlib import contrast, simulate_cvd  # noqa: E402
from render_preview import F, draw_run  # noqa: E402

PALETTE = ROOT / "shared" / "palette.json"
DEFAULT_OUT = INTELLIJ / "preview" / "cvd-compare.png"
TOKENS = ["fg", "comment", "doc_comment", "keyword", "string", "number",
          "function", "constant", "annotation", "todo", "error", "doc_tag"]
KINDS = (("正常", None), ("protanopia", "protanopia"),
         ("deuteranopia", "deuteranopia"))


def text_color(bg):
    return "#101010" if contrast(bg, "#FFFFFF") > contrast(bg, "#000000") else "#FFFFFF"


def cell(draw, x, y, w, h, color, label):
    draw.rounded_rectangle([x, y, x + w, y + h], radius=6, fill=color,
                           outline="#2C3D35", width=1)
    draw.text((x + 8, y + (h - 12) / 2), label, font=F.get(10),
              fill=text_color(color))


def generate(outdir=None):
    data = json.loads(PALETTE.read_text(encoding="utf-8"))
    margin, label_w, gap = 28, 132, 12
    width = 1120
    cell_w = (width - 2 * margin - label_w - 3 * gap) // 3
    row_h, title_h, header_h = 38, 38, 28
    section_h = title_h + header_h + row_h * len(TOKENS) + 18
    height = margin * 2 + 40 + section_h * len(data["themes"])

    img = Image.new("RGB", (width, height), "#121814")
    d = ImageDraw.Draw(img)
    draw_run(d, margin, 10, "Green Eye · CVD 对比（Machado 2009，severity 1.0）",
             22, "#D1D0CA")

    y = margin + 30
    for theme in data["themes"]:
        pal = theme["colors"]
        d.rounded_rectangle([margin, y, width - margin, y + section_h - 10],
                            radius=10, fill=pal["bg_editor"],
                            outline=pal["separator"], width=1)
        draw_run(d, margin + 14, y + 8,
                 "%s「%s」" % (theme["name"], theme["label"]), 18, pal["fg"])
        y += title_h
        for i, (label, kind) in enumerate(KINDS):
            x = margin + label_w + gap + i * (cell_w + gap)
            draw_run(d, x + 8, y, label, 13, pal["fg_dim"])
        y += header_h
        for token in TOKENS:
            base = pal[token]
            d.text((margin + 14, y + 11), token, font=F.get(11), fill=pal["fg"])
            for i, (_, kind) in enumerate(KINDS):
                color = base if kind is None else simulate_cvd(base, kind)
                x = margin + label_w + gap + i * (cell_w + gap)
                cell(d, x, y + 3, cell_w, row_h - 6, color, color.upper())
            y += row_h
        y += 18

    out = Path(outdir).expanduser() / "cvd-compare.png" if outdir else DEFAULT_OUT
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    print("写入 %s (%dx%d)" % (out, width, height))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="生成 CVD 对比色板")
    ap.add_argument("--outdir")
    args = ap.parse_args(argv)
    return generate(args.outdir)


if __name__ == "__main__":
    sys.exit(main())
