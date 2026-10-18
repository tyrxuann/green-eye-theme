#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 1:1 与 2× 局部裁剪图，便于逐像素核对（评委要求）。"""
import os, sys
from PIL import Image

# 代码窗口几何（render_preview 的常量，缩放前单位）
CODE_TOP = 30 + 34 + 10      # 标题栏 + 标签栏 + 内边距
LINE_H = 25


def crop_line_band(src, dst1, dst2, line_from, line_to, x0=0, x1=760):
    im = Image.open(src)
    y0 = CODE_TOP + line_from * LINE_H
    y1 = CODE_TOP + line_to * LINE_H
    box = (x0, max(0, y0), min(x1, im.width), min(y1, im.height))
    c = im.crop(box)
    c.save(dst1)
    c.resize((c.width * 2, c.height * 2), Image.NEAREST).save(dst2)
    print("   %s (%dx%d) / %s (2x)" % (os.path.basename(dst1), c.width, c.height,
                                      os.path.basename(dst2)))


def crop_box(src, dst1, dst2, box):
    im = Image.open(src)
    c = im.crop(box)
    c.save(dst1)
    c.resize((c.width * 2, c.height * 2), Image.NEAREST).save(dst2)
    print("   %s (%dx%d) / %s (2x)" % (os.path.basename(dst1), c.width, c.height,
                                      os.path.basename(dst2)))


def make_crops(outdir):
    print("  局部裁剪：")
    for tag, suffix in (("current", ""), ("mineral", "-mineral")):
        src = os.path.join(outdir, "java-%s.png" % tag)
        if not os.path.exists(src):
            continue
        # 字段/常量：Java 样例第 14~23 行
        crop_line_band(src, os.path.join(outdir, "crop-java-fields%s.png" % suffix),
                       os.path.join(outdir, "crop-java-fields%s-2x.png" % suffix), 13, 23)
        # 状态色对照：当前行 + 选中 + 注释 + Javadoc
        crop_line_band(src, os.path.join(outdir, "crop-java-states%s.png" % suffix),
                       os.path.join(outdir, "crop-java-states%s-2x.png" % suffix), 24, 34)
        ui = os.path.join(outdir, "ui-%s.png" % ("dark" if tag == "current" else "mineral"))
        if os.path.exists(ui):
            crop_box(ui, os.path.join(outdir, "crop-popup%s.png" % suffix),
                     os.path.join(outdir, "crop-popup%s-2x.png" % suffix), (540, 215, 960, 470))


if __name__ == "__main__":
    d = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "preview")
    make_crops(d)
