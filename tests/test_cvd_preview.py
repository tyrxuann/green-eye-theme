#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CVD 对比色板生成测试（需要 Pillow）。"""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "intellij" / "src"))

try:
    from PIL import Image  # noqa: F401
    HAVE_PIL = True
except ImportError:
    HAVE_PIL = False


@unittest.skipUnless(HAVE_PIL, "需要 Pillow")
class CVDPreviewTests(unittest.TestCase):
    def test_generate_swatch_image(self):
        import gen_cvd_preview
        with tempfile.TemporaryDirectory(prefix="green eye cvd ") as tmp:
            self.assertEqual(gen_cvd_preview.generate(outdir=tmp), 0)
            path = Path(tmp) / "cvd-compare.png"
            self.assertTrue(path.is_file())
            with Image.open(path) as img:
                self.assertGreater(img.width, 800)
                self.assertGreater(img.height, 400)


if __name__ == "__main__":
    unittest.main()
