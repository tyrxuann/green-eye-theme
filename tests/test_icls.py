#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""已生成 .icls 的关键属性回归测试（需先 build）。"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT / "shared" / "tools"))
from colorlib import contrast  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
THEMES = ROOT / "intellij" / "themes"


class IclsTests(unittest.TestCase):
    @staticmethod
    def _colors(text):
        return {m.group(1): m.group(2) for m in re.finditer(
            r'<option name="([A-Z_]+)" value="([0-9A-Fa-f]{6})"', text)}

    def test_change_bars_have_contrast(self):
        for name in ("Green-Eye-Dark.icls", "Green-Eye-Mineral.icls"):
            path = THEMES / name
            if not path.is_file():
                self.skipTest("先运行 build")
            colors = self._colors(path.read_text(encoding="utf-8"))
            line_bg = "#" + colors.get("REVIEW_CHANGED_LINES_COLOR", "2E4A2A")
            for key in ("ADDED_LINES_COLOR", "MODIFIED_LINES_COLOR",
                        "DELETED_LINES_COLOR"):
                self.assertIn(key, colors, name)
                ratio = contrast("#" + colors[key], line_bg)
                self.assertGreaterEqual(ratio, 2.5,
                                        "%s/%s %.2f" % (name, key, ratio))

    def test_diff_attributes_have_no_foreground(self):
        for name in ("Green-Eye-Dark.icls", "Green-Eye-Mineral.icls"):
            path = THEMES / name
            if not path.is_file():
                self.skipTest("先运行 build")
            text = path.read_text(encoding="utf-8")
            for key in ("DIFF_INSERTED", "DIFF_DELETED", "DIFF_MODIFIED",
                        "DIFF_CONFLICT"):
                block = re.search(
                    r'<option name="%s">.*?</option>' % key, text, re.S)
                self.assertIsNotNone(block, key)
                self.assertNotIn('name="FOREGROUND"', block.group(0))
                self.assertIn('name="BACKGROUND"', block.group(0))

    def test_diff_background_contrast(self):
        import json
        data = json.loads((ROOT / "shared" / "palette.json").read_text(
            encoding="utf-8"))
        fg_by_id = {t["id"]: t["colors"]["fg"] for t in data["themes"]}
        bg_by_id = {t["id"]: t["colors"]["bg_editor"] for t in data["themes"]}
        for theme_id, name in (("dark", "Green-Eye-Dark.icls"),
                               ("mineral", "Green-Eye-Mineral.icls")):
            path = THEMES / name
            if not path.is_file():
                self.skipTest("先运行 build")
            text = path.read_text(encoding="utf-8")
            editor = bg_by_id[theme_id]
            for key in ("DIFF_INSERTED", "DIFF_DELETED", "DIFF_MODIFIED"):
                block = re.search(
                    r'<option name="%s">.*?</option>' % key, text, re.S)
                bg = re.search(r'name="BACKGROUND" value="([0-9A-Fa-f]{6})"',
                               block.group(0))
                self.assertIsNotNone(bg, key)
                self.assertGreaterEqual(contrast("#" + bg.group(1), editor),
                                        1.6, "%s/%s" % (name, key))
                self.assertGreaterEqual(
                    contrast("#" + bg.group(1), fg_by_id[theme_id]), 4.5,
                    "%s/%s" % (name, key))

    def test_xml_syntax_roles(self):
        import json
        data = json.loads((ROOT / "shared" / "palette.json").read_text(
            encoding="utf-8"))
        for theme in data["themes"]:
            name = {"dark": "Green-Eye-Dark.icls",
                    "mineral": "Green-Eye-Mineral.icls"}[theme["id"]]
            path = THEMES / name
            if not path.is_file():
                self.skipTest("先运行 build")
            text = path.read_text(encoding="utf-8")
            expected = {
                "XML_TAG_NAME": theme["colors"]["keyword"],
                "XML_ATTRIBUTE_NAME": theme["colors"]["annotation"],
                "XML_ATTRIBUTE_VALUE": theme["colors"]["string"],
                "XML_NS_PREFIX": theme["colors"]["constant"],
            }
            for key, color in expected.items():
                block = re.search(
                    r'<option name="%s">.*?</option>' % key, text, re.S)
                self.assertIsNotNone(block, key)
                match = re.search(r'name="FOREGROUND" value="([0-9A-Fa-f]{6})"',
                                  block.group(0))
                self.assertEqual(match.group(1).upper(), color.lstrip("#").upper())

    def test_doc_tag_has_effect_color(self):
        for name in ("Green-Eye-Dark.icls", "Green-Eye-Mineral.icls"):
            path = THEMES / name
            if not path.is_file():
                self.skipTest("先运行 build")
            text = path.read_text(encoding="utf-8")
            block = re.search(
                r'<option name="DEFAULT_DOC_COMMENT_TAG">.*?</option>',
                text, re.S)
            self.assertIsNotNone(block, name)
            self.assertIn('name="EFFECT_TYPE" value="1"', block.group(0))
            self.assertIn('name="EFFECT_COLOR"', block.group(0))


if __name__ == "__main__":
    unittest.main()
