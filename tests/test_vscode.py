#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VS Code 主题与 VSIX 的结构 / 色值测试。"""
import json
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "intellij" / "src"))
sys.path.insert(0, str(ROOT / "vscode" / "src"))

import generate  # noqa: E402
import package_vsix  # noqa: E402
import vscode_build  # noqa: E402
from palette import PALETTES  # noqa: E402
from project_config import VERSION  # noqa: E402

PALETTE = ROOT / "shared" / "palette.json"
THEME_FILES = {
    "dark": "green-eye-dark.json",
    "mineral": "green-eye-mineral.json",
}


class VSCodeThemeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not PALETTE.is_file():
            raise unittest.SkipTest("先运行 green_eye.py palette / build")

    def generate(self, tmp):
        self.assertEqual(generate.generate(outdir=tmp), 0)
        return {key: json.loads((Path(tmp) / name).read_text(encoding="utf-8"))
                for key, name in THEME_FILES.items()}

    def test_theme_structure_and_palette_values(self):
        with tempfile.TemporaryDirectory(prefix="green eye vscode ") as tmp:
            themes = self.generate(tmp)
            for key, doc in themes.items():
                palette = PALETTES[key]
                self.assertEqual(doc["type"], "dark")
                self.assertTrue(doc["name"].endswith(palette["label"]))
                self.assertEqual(doc["colors"]["editor.background"],
                                 palette["bg_editor"])
                self.assertEqual(doc["colors"]["editor.foreground"],
                                 palette["fg"])
                self.assertEqual(doc["colors"]["editorLineNumber.foreground"],
                                 palette["line_numbers"])
                self.assertEqual(doc["colors"]["editor.selectionBackground"],
                                 palette["bg_selection"])
                self.assertEqual(doc["colors"]["editor.findMatchBackground"],
                                 palette["bg_search"])
                known = {v for v in palette.values()
                         if isinstance(v, str) and v.startswith("#")}
                used = set(doc["colors"].values())
                for rule in doc["tokenColors"]:
                    used.add(rule["settings"]["foreground"])
                self.assertEqual(sorted(used - known), [],
                                 "%s 使用了调色板外的颜色" % key)

    def test_no_punctuation_or_operator_coloring(self):
        with tempfile.TemporaryDirectory(prefix="green eye vscode ") as tmp:
            themes = self.generate(tmp)
            forbidden = ("punctuation.definition.string", "punctuation.separator",
                         "punctuation.terminator", "keyword.operator",
                         "meta.brace", "punctuation.section")
            for key, doc in themes.items():
                for rule in doc["tokenColors"]:
                    for scope in rule["scope"]:
                        for bad in forbidden:
                            self.assertNotIn(bad, scope,
                                             "%s 不应单独给 %s 上色" % (key, scope))

    def test_two_themes_are_visibly_different(self):
        with tempfile.TemporaryDirectory(prefix="green eye vscode ") as tmp:
            themes = self.generate(tmp)
            diffs = 0
            for rule_a, rule_b in zip(themes["dark"]["tokenColors"],
                                      themes["mineral"]["tokenColors"]):
                if rule_a["settings"]["foreground"] != rule_b["settings"]["foreground"]:
                    diffs += 1
            self.assertGreaterEqual(diffs, 5)
            self.assertNotEqual(
                themes["dark"]["colors"]["editor.selectionBackground"],
                themes["mineral"]["colors"]["editor.selectionBackground"])

    def test_build_and_freshness(self):
        with tempfile.TemporaryDirectory(prefix="green eye vsix ") as tmp:
            self.assertEqual(vscode_build.build(package=True, outdir=tmp), 0)

    def test_vsix_manifest(self):
        with tempfile.TemporaryDirectory(prefix="green eye vsix ") as tmp:
            self.assertEqual(package_vsix.package(outdir=tmp), 0)
            vsix = Path(tmp) / ("green-eye-theme-%s.vsix" % VERSION)
            self.assertTrue(vsix.is_file())
            with zipfile.ZipFile(vsix) as zf:
                names = set(zf.namelist())
                self.assertIn("[Content_Types].xml", names)
                self.assertIn("extension.vsixmanifest", names)
                self.assertIn("extension/package.json", names)
                self.assertIn("extension/README.md", names)
                for name in THEME_FILES.values():
                    self.assertIn("extension/themes/%s" % name, names)
                if (ROOT / "LICENSE").is_file():
                    self.assertIn("extension/LICENSE", names)
                pkg = json.loads(zf.read("extension/package.json"))
                self.assertEqual(pkg["version"], VERSION)
                root = ET.fromstring(zf.read("extension.vsixmanifest"))
                ns = "{http://schemas.microsoft.com/developer/vsx-schema/2011}"
                identity = root.find(".//%sIdentity" % ns)
                self.assertIsNotNone(identity)
                self.assertEqual(identity.get("Version"), VERSION)
                self.assertEqual(identity.get("Publisher"), pkg["publisher"])


if __name__ == "__main__":
    unittest.main()
