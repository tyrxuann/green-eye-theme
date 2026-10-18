#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""发布前汇总页测试。"""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "intellij" / "src"))

import gen_summary_report  # noqa: E402
from project_config import VERSION  # noqa: E402


class SummaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (ROOT / "shared" / "palette.json").is_file():
            raise unittest.SkipTest("先运行 build / palette")

    def test_report_contains_sections(self):
        text = gen_summary_report.build_report()
        self.assertIn("Green Eye 发布前汇总", text)
        self.assertIn(VERSION, text)
        for section in ("Doctor", "验收", "CVD", "真机走查", "产物", "仍需处理"):
            self.assertIn("## %s" % section, text)

    def test_write_report(self):
        with tempfile.TemporaryDirectory(prefix="green eye report ") as tmp:
            path = Path(tmp) / "report.md"
            self.assertEqual(gen_summary_report.main(["--out", str(path)]), 0)
            self.assertTrue(path.is_file())
            self.assertIn("Green Eye 发布前汇总",
                          path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
