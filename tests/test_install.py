#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""跨平台安装器集成测试（替代 intellij/scripts/test_install.sh）。

不依赖 bash / unzip / shasum / grep：路径用 pathlib，hash 用 hashlib，
读 jar 用 zipfile。测试在临时目录里跑，不会碰真实 IDE 配置。
"""
import hashlib
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "green_eye.py"
DIST = ROOT / "intellij" / "dist"
THEMES = ROOT / "intellij" / "themes"
sys.path.insert(0, str(ROOT / "intellij" / "src"))


def find_artifact():
    jars = sorted(DIST.glob("GreenEye-Theme-*.jar"))
    return jars[-1] if jars else None


class InstallerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.artifact = find_artifact()
        if cls.artifact is None:
            raise unittest.SkipTest("先运行 green_eye.py build（缺少插件 jar）")

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="green eye install ")
        self.addCleanup(self.temp.cleanup)
        self.config = Path(self.temp.name) / "IntelliJIdea2026.2"
        (self.config / "plugins").mkdir(parents=True)
        (self.config / "colors").mkdir()

    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, str(CLI), "install",
             "--config-dir", str(self.config), *args],
            cwd=str(ROOT), text=True, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def snapshot(self):
        out = []
        for path in sorted(self.config.rglob("*")):
            if path.is_file():
                out.append((str(path.relative_to(self.config)),
                            hashlib.sha256(path.read_bytes()).hexdigest()[:16],
                            path.stat().st_mtime_ns))
        return out

    def assert_ok(self, result):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_fresh_install(self):
        result = self.run_cli("--yes")
        self.assert_ok(result)
        self.assertTrue((self.config / "plugins" / self.artifact.name).is_file())
        self.assertIn("安装插件", result.stdout)

    def test_repeat_install_is_idempotent(self):
        self.assert_ok(self.run_cli("--yes"))
        before = self.snapshot()
        result = self.run_cli("--yes")
        self.assert_ok(result)
        self.assertIn("无需改动", result.stdout)
        self.assertEqual(before, self.snapshot())

    def test_dirty_state_is_cleaned(self):
        old_jar = self.config / "plugins" / "GreenEye-Theme-0.0.1.jar"
        shutil.copy2(str(self.artifact), str(old_jar))
        plugin_dir = self.config / "plugins" / "GreenEye-Theme"
        (plugin_dir / "META-INF").mkdir(parents=True)
        with zipfile.ZipFile(self.artifact) as zf:
            manifest = zf.read("META-INF/plugin.xml")
        (plugin_dir / "META-INF" / "plugin.xml").write_bytes(manifest)
        icls = sorted(THEMES.glob("Green-Eye-*.icls"))[0]
        shutil.copy2(str(icls), str(self.config / "colors" / icls.name))
        disabled = self.config / "disabled_plugins.txt"
        disabled.write_text("com.greeneye.intellij.theme\nsome.other.plugin\n",
                            encoding="utf-8")

        self.assert_ok(self.run_cli("--yes"))
        self.assertFalse(old_jar.exists())
        self.assertFalse(plugin_dir.exists())
        self.assertFalse((self.config / "colors" / icls.name).exists())
        self.assertEqual(disabled.read_text(encoding="utf-8"),
                         "some.other.plugin\n")

    def test_bom_disabled_plugins_is_preserved(self):
        disabled = self.config / "disabled_plugins.txt"
        disabled.write_bytes(
            b"\xef\xbb\xbfcom.greeneye.intellij.theme\nsome.other.plugin\n")
        self.assert_ok(self.run_cli("--yes"))
        data = disabled.read_bytes()
        self.assertTrue(data.startswith(b"\xef\xbb\xbf"))
        text = data.decode("utf-8-sig")
        self.assertNotIn("com.greeneye.intellij.theme", text)
        self.assertIn("some.other.plugin", text)

    def test_locked_target_has_friendly_error(self):
        target = self.config / "plugins" / self.artifact.name
        target.mkdir()
        result = self.run_cli("--yes")
        self.assertEqual(result.returncode, 1)
        self.assertIn("请完全退出", result.stderr)

    def test_latest_config_is_numeric(self):
        import install
        root = Path(self.temp.name) / "JetBrains"
        (root / "IntelliJIdea2026.2").mkdir(parents=True)
        (root / "IntelliJIdea2026.10").mkdir()
        dirs = install.discover_targets(root, None, False)
        self.assertEqual([p.name for p in dirs], ["IntelliJIdea2026.10"])

    def test_dry_run_does_not_touch_files(self):
        before = self.snapshot()
        result = self.run_cli("--dry-run", "--yes")
        self.assert_ok(result)
        self.assertIn("dry-run", result.stdout)
        self.assertEqual(before, self.snapshot())

    def test_icls_only_and_plugin_mode_are_mutually_exclusive(self):
        self.assert_ok(self.run_cli("--icls-only", "--yes"))
        self.assertEqual(list((self.config / "plugins").glob("*")), [])
        self.assertEqual(len(list((self.config / "colors").glob("*.icls"))), 2)

        self.assert_ok(self.run_cli("--yes"))
        self.assertTrue((self.config / "plugins" / self.artifact.name).is_file())
        self.assertEqual(list((self.config / "colors").glob("*.icls")), [])

    def test_uninstall_removes_everything_it_installed(self):
        disabled = self.config / "disabled_plugins.txt"
        disabled.write_text("com.greeneye.intellij.theme\nsome.other.plugin\n",
                            encoding="utf-8")
        self.assert_ok(self.run_cli("--yes"))
        self.assert_ok(self.run_cli("--uninstall", "--yes"))
        self.assertEqual(list((self.config / "plugins").glob("*")), [])
        self.assertEqual(list((self.config / "colors").glob("*.icls")), [])
        self.assertEqual(disabled.read_text(encoding="utf-8"),
                         "some.other.plugin\n")

    def test_uninstall_rejects_icls_only(self):
        result = self.run_cli("--uninstall", "--icls-only", "--yes")
        self.assertEqual(result.returncode, 1)
        self.assertIn("不能与", result.stderr)


if __name__ == "__main__":
    unittest.main()
