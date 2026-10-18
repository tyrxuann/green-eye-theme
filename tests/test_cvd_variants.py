#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A+ CVD Improved 变体测试：真实残余数、对比度、产物。"""
import itertools
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "intellij" / "src"))
sys.path.insert(0, str(ROOT / "shared" / "tools"))

import cvd_variants  # noqa: E402
from colorlib import contrast, de2000  # noqa: E402
from gen_cvd_report import TOKENS, collapse_pairs  # noqa: E402
from project_config import VERSION  # noqa: E402


class CVDVariantTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (ROOT / "shared" / "palette.json").is_file():
            raise unittest.SkipTest("先运行 build / palette")

    def test_real_residual_counts(self):
        data = json.loads(cvd_variants.PALETTE.read_text(encoding="utf-8"))
        expected = {"dark": 13, "mineral": 14}
        for theme in data["themes"]:
            colors = cvd_variants.variant_colors(
                theme["colors"], cvd_variants.OVERRIDES[theme["id"]])
            self.assertEqual(len(collapse_pairs(colors)),
                             expected[theme["id"]], theme["id"])
            normal_min = min(de2000(colors[a], colors[b])
                             for a, b in itertools.combinations(TOKENS, 2))
            self.assertGreaterEqual(normal_min, 12.0)
            for key, value in cvd_variants.OVERRIDES[theme["id"]].items():
                self.assertGreaterEqual(contrast(value, colors["bg_editor"]),
                                        cvd_variants.FLOORS[key])

    def test_build_artifacts(self):
        with tempfile.TemporaryDirectory(prefix="green eye cvd ") as tmp:
            self.assertEqual(cvd_variants.build(package=True, outdir=tmp), 0)
            target = Path(tmp) / ("green-eye-%s-cvd.zip" % VERSION)
            self.assertTrue(target.is_file())
            with zipfile.ZipFile(target) as zf:
                names = zf.namelist()
                self.assertIn("intellij/Green-Eye-Dark-CVD.icls", names)
                self.assertIn("intellij/Green-Eye-Mineral-CVD.icls", names)
                self.assertIn("vscode/green-eye-cvd-variants-%s.vsix"
                              % VERSION, names)
                self.assertIn("cvd-variants-report.md", names)
                self.assertIn("LICENSE", names)
                self.assertIn("SHA256SUMS", names)
                self.assertIn("6BC087",
                              zf.read("intellij/Green-Eye-Dark-CVD.icls")
                              .decode("utf-8"))

            vsix = (ROOT / "vscode" / "dist"
                    / ("green-eye-cvd-variants-%s.vsix" % VERSION))
            with zipfile.ZipFile(vsix) as zf:
                names = zf.namelist()
                self.assertIn("extension/themes/green-eye-dark-cvd.json",
                              names)
                self.assertIn("extension/themes/green-eye-mineral-cvd.json",
                              names)
                self.assertIn("extension/LICENSE", names)
                dark = json.loads(
                    zf.read("extension/themes/green-eye-dark-cvd.json"))
                self.assertIn("CVD Improved", dark["name"])


if __name__ == "__main__":
    unittest.main()
