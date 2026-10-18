"""Exercise interpreter selection through the build entrypoint in isolation."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class BuildInterpreterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="green eye build ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        scripts = self.root / "intellij" / "scripts"
        scripts.mkdir(parents=True)
        (self.root / "intellij" / "src").mkdir()
        self.build = scripts / "build.sh"
        shutil.copyfile(ROOT / "intellij/scripts/build.sh", self.build)
        (scripts / "test_install.sh").write_text("exit 0\n")
        self.log = self.root / "calls.log"
        executable = self.root / ".venv/bin/python3"
        executable.parent.mkdir(parents=True)
        executable.write_text(
            '#!/bin/sh\nprintf "%s\\n" "$0|$PWD|$*" >> "$BUILD_TEST_LOG"\n'
        )
        executable.chmod(0o755)
        self.python = executable.with_name("python")
        self.python.symlink_to("python3")

    def run_build(self, python, **env):
        return subprocess.run(
            ["bash", str(self.build)], cwd=self.root, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env={**os.environ, "PYTHON": python,
                 "BUILD_TEST_LOG": str(self.log), **env},
        )

    def assert_build(self, python, **env):
        result = self.run_build(python, **env)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        calls = self.log.read_text().splitlines()
        self.assertGreater(len(calls), 10)
        # Resolving the executable target would bypass the virtual environment.
        self.assertTrue(all(line.startswith(str(self.python) + "|") for line in calls))
        self.assertIn(
            f"{self.python}|{self.root / 'intellij/src'}|check_style.py", calls
        )
        self.assertIn("Build complete.", result.stdout)

    def test_relative_virtualenv(self):
        self.assert_build(".venv/bin/python")

    def test_absolute_path_with_spaces(self):
        self.assert_build(str(self.python))

    def test_relative_path_entry(self):
        self.assert_build("python", PATH=".venv/bin" + os.pathsep + os.environ["PATH"])

    def test_missing_interpreter_fails_before_build(self):
        result = self.run_build("./missing/python")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.log.exists())
        self.assertNotIn("== style ==", result.stdout)


if __name__ == "__main__":
    unittest.main()
