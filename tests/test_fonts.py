#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""预览字体解析测试：缺字体时不能崩，环境变量要生效。"""
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "intellij" / "src"))

try:
    from PIL import Image, ImageDraw, ImageFont  # noqa: F401
    HAVE_PIL = True
except ImportError:
    HAVE_PIL = False


@unittest.skipUnless(HAVE_PIL, "需要 Pillow 才能测试预览字体")
class FontResolutionTests(unittest.TestCase):
    @staticmethod
    def load():
        import render_preview
        return render_preview

    def test_missing_fonts_fall_back_without_crashing(self):
        rp = self.load()
        with mock.patch.object(rp, "MONO_CANDIDATES",
                               ["/no/such/__green_eye_missing__.ttf"]), \
                mock.patch.object(rp, "CJK_CANDIDATES",
                                  ["/no/such/__green_eye_missing__.ttc"]), \
                mock.patch.dict(os.environ, {"GREEN_EYE_MONO_FONT": "",
                                             "GREEN_EYE_CJK_FONT": ""}):
            fonts = rp.Fonts()
            self.assertIsNotNone(fonts.get(14))
            self.assertIsNotNone(fonts.get(14, cjk=True))

    def test_mono_env_override_is_used(self):
        rp = self.load()
        if not rp.F.mono:
            self.skipTest("本机没有可用于测试的等宽字体")
        with mock.patch.dict(os.environ, {"GREEN_EYE_MONO_FONT": rp.F.mono}):
            fonts = rp.Fonts()
            self.assertEqual(fonts.mono, rp.F.mono)

    def test_cjk_env_override_is_used(self):
        rp = self.load()
        if not rp.F.cjk:
            self.skipTest("本机没有可用于测试的 CJK 字体")
        with mock.patch.dict(os.environ, {"GREEN_EYE_CJK_FONT": rp.F.cjk}):
            fonts = rp.Fonts()
            self.assertEqual(fonts.cjk, rp.F.cjk)

    def test_draw_run_with_missing_fonts_does_not_crash(self):
        rp = self.load()
        with mock.patch.object(rp, "MONO_CANDIDATES",
                               ["/no/such/__green_eye_missing__.ttf"]), \
                mock.patch.object(rp, "CJK_CANDIDATES",
                                  ["/no/such/__green_eye_missing__.ttc"]), \
                mock.patch.dict(os.environ, {"GREEN_EYE_MONO_FONT": "",
                                             "GREEN_EYE_CJK_FONT": ""}):
            old = rp.F
            rp.F = rp.Fonts()
            try:
                img = Image.new("RGB", (240, 40), "white")
                draw = ImageDraw.Draw(img)
                end = rp.draw_run(draw, 0, 0, "中文 abc", 14, "black")
                self.assertGreater(end, 0)
            finally:
                rp.F = old

    def test_split_cjk(self):
        rp = self.load()
        parts = [(text, is_cjk) for text, is_cjk in rp.split_cjk("abc中文def")]
        self.assertEqual(parts, [("abc", False), ("中文", True), ("def", False)])


if __name__ == "__main__":
    unittest.main()
