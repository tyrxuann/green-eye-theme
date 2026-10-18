#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""文档漂移的回归测试：手写的摘要表必须引用真实调色板值。

矿彩曾经把选中色写成石板蓝 `#3E5173`，而代码里实际是 `#365847`；
生成器管不到的紧凑摘要表最容易再次漂移，所以这里直接对行断言。
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "intellij" / "src"))

from palette import PALETTES  # noqa: E402

DOCS = [ROOT / "README.md", ROOT / "intellij" / "README.md"]


def row_starting(text, prefix):
    for line in text.splitlines():
        if line.startswith(prefix):
            return line
    raise AssertionError("找不到表格行: %s" % prefix)


class DocDriftTests(unittest.TestCase):
    def test_selection_row_uses_real_palette_values(self):
        for doc in DOCS:
            text = doc.read_text(encoding="utf-8")
            row = row_starting(text, "| 选中 / 查找 |")
            for theme in ("dark", "mineral"):
                palette = PALETTES[theme]
                self.assertIn(palette["bg_selection"], row,
                              "%s 的选中色与调色板不一致" % doc.name)
                self.assertIn(palette["bg_search"], row,
                              "%s 的查找色与调色板不一致" % doc.name)

    def test_mineral_summary_does_not_use_dead_colors(self):
        dead = {"#3E5173", "#D4AD6A", "#D7A3B6", "#D49E8D", "#83948E"}
        for doc in DOCS:
            text = doc.read_text(encoding="utf-8")
            for color in dead:
                self.assertNotIn(color, text,
                                 "%s 仍引用不存在的颜色 %s" % (doc.name, color))


if __name__ == "__main__":
    unittest.main()
