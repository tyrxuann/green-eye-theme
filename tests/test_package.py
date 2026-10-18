#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""发布包测试：内容齐全、SHA256SUMS 覆盖除自身外的全部文件。"""
import hashlib
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "green_eye.py"
DIST = ROOT / "intellij" / "dist"
sys.path.insert(0, str(ROOT / "intellij" / "src"))

from project_config import VERSION  # noqa: E402


class PackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not list(DIST.glob("GreenEye-Theme-*.jar")):
            raise unittest.SkipTest("先运行 green_eye.py build（缺少 jar）")

    def test_package_manifest_and_sums(self):
        with tempfile.TemporaryDirectory(prefix="green eye package ") as tmp:
            result = subprocess.run(
                [sys.executable, str(CLI), "package", "--outdir", tmp],
                cwd=str(ROOT), text=True, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            zips = list(Path(tmp).glob("*.zip"))
            self.assertEqual(len(zips), 1)
            prefix = "green-eye-%s/" % VERSION
            with zipfile.ZipFile(zips[0]) as zf:
                names = zf.namelist()
                self.assertIn(prefix + "INSTALL.txt", names)
                self.assertIn(prefix + "THIRD_PARTY_NOTICES.md", names)
                self.assertIn(prefix + "SHA256SUMS", names)
                self.assertTrue(any(n.startswith(prefix + "GreenEye-Theme-")
                                    and n.endswith(".jar") for n in names))
                self.assertEqual(
                    len([n for n in names if n.endswith(".icls")]), 2)
                if (ROOT / "LICENSE").is_file():
                    self.assertIn(prefix + "LICENSE", names)

                sums = zf.read(prefix + "SHA256SUMS").decode("utf-8")
                expected = {}
                for line in sums.splitlines():
                    digest, filename = line.split("  ", 1)
                    expected[filename] = digest
                self.assertEqual(len(expected), len(names) - 1)
                for name in names:
                    if name.endswith("SHA256SUMS"):
                        continue
                    filename = name.rsplit("/", 1)[-1]
                    actual = hashlib.sha256(zf.read(name)).hexdigest()
                    self.assertEqual(expected.get(filename), actual, name)

    def test_combined_package_contains_vscode(self):
        with tempfile.TemporaryDirectory(prefix="green eye package all ") as tmp:
            result = subprocess.run(
                [sys.executable, str(CLI), "package", "--all",
                 "--outdir", tmp],
                cwd=str(ROOT), text=True, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            zips = list(Path(tmp).glob("*-all.zip"))
            self.assertEqual(len(zips), 1)
            prefix = "green-eye-%s/" % VERSION
            with zipfile.ZipFile(zips[0]) as zf:
                names = zf.namelist()
                self.assertTrue(any(n.startswith(prefix + "intellij/")
                                    and n.endswith(".jar") for n in names))
                self.assertEqual(
                    len([n for n in names if n.startswith(prefix + "intellij/")
                         and n.endswith(".icls")]), 2)
                self.assertIn(prefix + "vscode/green-eye-theme-%s.vsix"
                              % VERSION, names)
                self.assertIn(prefix + "INSTALL.txt", names)
                self.assertIn(prefix + "THIRD_PARTY_NOTICES.md", names)
                self.assertIn(prefix + "SHA256SUMS", names)


if __name__ == "__main__":
    unittest.main()
