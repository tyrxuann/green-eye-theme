#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""doctor 预检的单元测试：缺失/正常两种路径。"""
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "intellij" / "src"))

import doctor  # noqa: E402
from project_config import PLUGIN_ID, VERSION  # noqa: E402


class DoctorTests(unittest.TestCase):
    def test_missing_palette_is_failure(self):
        status, label, _ = doctor.check_palette(Path("/no/such/palette.json"))
        self.assertEqual(status, doctor.FAIL)
        self.assertIn("palette", label)

    def test_valid_palette(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "palette.json"
            path.write_text(json.dumps({
                "schema": "green-eye-palette/1",
                "themes": [{}, {}],
            }), encoding="utf-8")
            self.assertEqual(doctor.check_palette(path)[0], doctor.OK)

    def test_jar_detection(self):
        with tempfile.TemporaryDirectory() as tmp:
            jar = Path(tmp) / ("GreenEye-Theme-%s.jar" % VERSION)
            with zipfile.ZipFile(jar, "w") as zf:
                zf.writestr("META-INF/plugin.xml",
                            "<idea-plugin><id>%s</id></idea-plugin>" % PLUGIN_ID)
            self.assertEqual(doctor.check_jar(jar)[0], doctor.OK)
            self.assertEqual(doctor.check_jar(Path(tmp) / "missing.jar")[0],
                             doctor.FAIL)

    def test_license_and_manual_report_checks(self):
        self.assertEqual(doctor.check_license(Path("/no/such/LICENSE"))[0],
                         doctor.WARN)
        self.assertEqual(doctor.check_manual_report(Path("/no/such/report.md"))[0],
                         doctor.WARN)

    def test_manual_report_parsed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "report.md"
            path.write_text("通过 **3** · 失败 **1** · 跳过 **0** · 共 4 项\n",
                            encoding="utf-8")
            status, _, detail = doctor.check_manual_report(path)
            self.assertEqual(status, doctor.WARN)
            self.assertIn("失败 1", detail)

    def test_icls_detection(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "Green-Eye-Dark.icls"
            path.write_text('<scheme name="Green Eye Dark"></scheme>',
                            encoding="utf-8")
            self.assertEqual(doctor.check_icls(path)[0], doctor.OK)

    def test_json_output(self):
        cli = ROOT / "green_eye.py"
        result = subprocess.run([sys.executable, str(cli), "doctor", "--json"],
                                cwd=str(ROOT), text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        payload = json.loads(result.stdout)
        self.assertIn("checks", payload)
        self.assertIn("summary", payload)
        self.assertEqual(len(payload["checks"]) >= 5, True)

    def test_checks_shape(self):
        if not (ROOT / "shared" / "palette.json").is_file():
            self.skipTest("先运行 build / palette")
        rows = doctor.checks()
        self.assertTrue(rows)
        for row in rows:
            self.assertEqual(len(row), 3)
            self.assertIn(row[0], (doctor.OK, doctor.WARN, doctor.FAIL))


if __name__ == "__main__":
    unittest.main()
