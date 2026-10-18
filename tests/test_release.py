#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""发布流程 dry-run 测试（不修改仓库）。"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "intellij" / "src"))

import release  # noqa: E402
import versioning  # noqa: E402


class ReleaseTests(unittest.TestCase):
    def test_dry_run_does_not_change_version(self):
        before = versioning.current_version()
        major, minor, patch = (int(x) for x in before.split("."))
        target = "%d.%d.%d" % (major, minor, patch + 1)
        self.assertEqual(release.run(target, dry_run=True), 0)
        self.assertEqual(versioning.current_version(), before)

    def test_invalid_version(self):
        self.assertEqual(release.run("1.2", dry_run=True), 1)

    def test_same_version_rejected(self):
        current = versioning.current_version()
        self.assertEqual(release.run(current, dry_run=True), 1)


if __name__ == "__main__":
    unittest.main()
