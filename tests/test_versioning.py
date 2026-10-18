#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""版本号统一更新测试。"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "intellij" / "src"))

import versioning  # noqa: E402


class VersioningTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="green eye version ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "intellij" / "src").mkdir(parents=True)
        (self.root / "vscode").mkdir()
        (self.root / "intellij" / "src" / "project_config.py").write_text(
            '#!/usr/bin/env python3\nVERSION = "1.1.0"\n', encoding="utf-8")
        (self.root / "vscode" / "package.json").write_text(
            '{\n  "name": "green-eye-theme",\n  "version": "1.1.0"\n}\n',
            encoding="utf-8")

    def test_current_version(self):
        self.assertEqual(versioning.current_version(self.root), "1.1.0")

    def test_dry_run_does_not_write(self):
        before = (self.root / "intellij" / "src" / "project_config.py").read_text(
            encoding="utf-8")
        self.assertEqual(versioning.bump("1.2.0", root=self.root, dry_run=True), 0)
        after = (self.root / "intellij" / "src" / "project_config.py").read_text(
            encoding="utf-8")
        self.assertEqual(before, after)

    def test_bump_updates_both_files(self):
        cache = self.root / "intellij" / "src" / "__pycache__"
        cache.mkdir()
        (cache / "project_config.cpython-313.pyc").write_bytes(b"stale")
        self.assertEqual(versioning.bump("1.2.0", root=self.root), 0)
        self.assertFalse((cache / "project_config.cpython-313.pyc").exists())
        config = (self.root / "intellij" / "src" / "project_config.py").read_text(
            encoding="utf-8")
        self.assertIn('VERSION = "1.2.0"', config)
        pkg = json.loads((self.root / "vscode" / "package.json").read_text(
            encoding="utf-8"))
        self.assertEqual(pkg["version"], "1.2.0")
        self.assertEqual(versioning.current_version(self.root), "1.2.0")

    def test_invalid_version_rejected(self):
        with self.assertRaises(ValueError):
            versioning.bump("1.2", root=self.root)


if __name__ == "__main__":
    unittest.main()
