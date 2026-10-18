#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""真机走查 runner 测试：解析、批量答案、报告。"""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "intellij" / "src"))

import manual_verify  # noqa: E402


class ManualVerifyTests(unittest.TestCase):
    def test_parse_checklist(self):
        items = manual_verify.parse()
        self.assertGreaterEqual(len(items), 30)
        self.assertTrue(any("Green Eye Dark" in text for _, text in items))
        self.assertTrue(any(section.startswith("1.") for section, _ in items))

    def test_all_pass_report(self):
        items = manual_verify.parse()
        with tempfile.TemporaryDirectory(prefix="green eye manual ") as tmp:
            path = Path(tmp) / "report.md"
            result = manual_verify.run(
                answers=["y"] * len(items), report=str(path))
            self.assertEqual(result, 0)
            text = path.read_text(encoding="utf-8")
            self.assertIn("通过 **%d**" % len(items), text)
            self.assertIn("失败 **0**", text)

    def test_failed_item_is_listed(self):
        items = manual_verify.parse()
        with tempfile.TemporaryDirectory(prefix="green eye manual ") as tmp:
            path = Path(tmp) / "report.md"
            answers = ["n"] + ["y"] * (len(items) - 1)
            self.assertEqual(manual_verify.run(answers=answers,
                                               report=str(path)), 1)
            self.assertTrue(path.is_file())
            text = path.read_text(encoding="utf-8")
            self.assertIn("失败 **1**", text)
            self.assertIn("## 失败项", text)

    def test_list_mode(self):
        self.assertEqual(manual_verify.run(list_only=True), 0)


if __name__ == "__main__":
    unittest.main()
