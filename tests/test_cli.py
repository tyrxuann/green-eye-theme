#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CLI 入口的轻量测试：帮助、版本、子命令参数。"""
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "green_eye.py"
sys.path.insert(0, str(ROOT / "intellij" / "src"))

from project_config import VERSION  # noqa: E402


def run(*args):
    return subprocess.run([sys.executable, str(CLI), *args],
                          cwd=str(ROOT), text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)


class CliTests(unittest.TestCase):
    def test_help_lists_commands(self):
        result = run("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        for command in ("build", "check", "palette", "test", "preview",
                        "install", "package", "vscode", "cvd", "clean", "version"):
            self.assertIn(command, result.stdout)

    def test_version(self):
        result = run("version")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), VERSION)

    def test_build_has_no_preview_flag(self):
        result = run("build", "--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--no-preview", result.stdout)

    def test_install_has_dry_run(self):
        result = run("install", "--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--dry-run", result.stdout)


if __name__ == "__main__":
    unittest.main()
