#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""色觉缺陷报告测试：配对识别与报告结构。"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "intellij" / "src"))

from palette import PALETTES  # noqa: E402
from gen_cvd_report import build_report, collapse_pairs  # noqa: E402


class CVDDTests(unittest.TestCase):
    def test_known_collapse_pair_is_reported(self):
        pairs = collapse_pairs(PALETTES["dark"])
        keys = {(a, b) for a, b, *_ in pairs}
        self.assertIn(("string", "error"), keys)
        self.assertGreater(len(pairs), 0)

    def test_report_contains_both_themes(self):
        text, counts = build_report()
        self.assertIn("Green Eye Dark", text)
        self.assertIn("Green Eye Mineral", text)
        self.assertEqual(counts["dark"], len(collapse_pairs(PALETTES["dark"])))
        self.assertEqual(counts["mineral"],
                         len(collapse_pairs(PALETTES["mineral"])))
        self.assertIn("报告项，不判失败", text)


if __name__ == "__main__":
    unittest.main()
