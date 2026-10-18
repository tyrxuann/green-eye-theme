#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""色彩数学的单元测试：已知值 + shared/intellij 两份实现的一致性。"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "shared" / "tools"))
sys.path.insert(0, str(ROOT / "intellij" / "src"))

import colorlib  # noqa: E402
from palette import PALETTES, contrast as palette_contrast  # noqa: E402
from check_collisions import de2000 as intellij_de2000  # noqa: E402


def hex_colors(palette):
    return [v for v in palette.values()
            if isinstance(v, str) and v.startswith("#") and len(v) == 7]


class ColorMathTests(unittest.TestCase):
    def test_known_contrast_values(self):
        self.assertAlmostEqual(colorlib.contrast("#000000", "#FFFFFF"), 21.0, places=6)
        self.assertAlmostEqual(colorlib.contrast("#777777", "#777777"), 1.0, places=6)

    def test_known_ciede2000_values(self):
        self.assertAlmostEqual(colorlib.de2000("#000000", "#000000"), 0.0, places=9)
        self.assertAlmostEqual(colorlib.de2000("#000000", "#FFFFFF"), 100.0, places=3)
        self.assertAlmostEqual(
            colorlib.de2000("#D7BA76", "#365847"),
            colorlib.de2000("#365847", "#D7BA76"), places=9)

    def test_shared_and_intellij_implementations_agree(self):
        for palette in PALETTES.values():
            bg = palette["bg_editor"]
            colors = hex_colors(palette)
            for color in colors:
                self.assertAlmostEqual(
                    colorlib.contrast(color, bg),
                    palette_contrast(color, bg), places=12)
            for i, first in enumerate(colors):
                for second in colors[i + 1:]:
                    self.assertAlmostEqual(
                        colorlib.de2000(first, second),
                        intellij_de2000(first, second), places=9)

    def test_cvd_simulation_returns_hex(self):
        for kind in ("protanopia", "deuteranopia"):
            out = colorlib.simulate_cvd("#D7BA76", kind)
            self.assertRegex(out, r"^#[0-9A-F]{6}$")


if __name__ == "__main__":
    unittest.main()
