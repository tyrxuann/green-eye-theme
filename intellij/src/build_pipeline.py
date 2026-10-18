#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
构建编排（替代 intellij/scripts/build.sh）。

为什么用 Python：
  · Windows 原生没有 bash / make；
  · 旧的 build.sh 无条件要求 Pillow，即使只想生成主题文件；
  · 用 sys.executable 调子脚本，天然复用当前解释器（uv / venv / 系统 Python）。

原则不变：任何一步失败立即中止，避免生成半成品。
`--no-preview` 跳过预览图渲染与 preview/ 的新鲜度检查，因此不需要 Pillow。
"""
import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
INTELLIJ = HERE.parent
ROOT = INTELLIJ.parent
REF = INTELLIJ / "build" / "ref"
THEMES = INTELLIJ / "themes"
PLATFORM_DOC = INTELLIJ / "README.md"
TESTS = ROOT / "tests"

NAMES = [
    REF / "all_reference_attribute_names.txt",
    REF / "ide_language_attribute_names.txt",
    REF / "ide_official_attribute_names.txt",
]
CHROME = [
    REF / "ide_chrome_names.txt",
    REF / "ide_official_chrome_names.txt",
]


def run(script, *args):
    cmd = [sys.executable, str(script), *[str(a) for a in args]]
    subprocess.run(cmd, cwd=str(HERE), check=True)


def run_unittest(pattern):
    cmd = [sys.executable, "-m", "unittest", "discover",
           "-s", str(TESTS), "-p", pattern, "-v"]
    subprocess.run(cmd, cwd=str(ROOT), check=True)


def require_pillow():
    if importlib.util.find_spec("PIL") is None:
        print("预览图需要 Pillow。", file=sys.stderr)
        print("  · 推荐：uv run green_eye.py build", file=sys.stderr)
        print("  · 或无预览：python3 green_eye.py build --no-preview",
              file=sys.stderr)
        return False
    return True


def build(no_preview=False, skip_tests=False):
    if not no_preview and not require_pillow():
        return 1

    print("== style ==")
    run(HERE / "check_style.py")

    print("== editor schemes ==")
    run(HERE / "gen_icls.py", "--names", *NAMES, "--chrome-names", *CHROME,
        "--outdir", THEMES, "--check")

    print("== palette and parity checks ==")
    run(HERE / "check_collisions.py")
    run(HERE / "check_token_separation.py")
    run(HERE / "check_identity.py")
    run(HERE / "check_reverse_palette.py")
    run(HERE / "check_render_styles.py")
    run(HERE / "check_attribute_parity.py")

    print("== theme package ==")
    run(HERE / "gen_theme_json.py")

    if not skip_tests:
        print("== installer tests ==")
        run_unittest("test_install.py")

    print("== generated documentation ==")
    run(HERE / "gen_readme_table.py", PLATFORM_DOC)
    run(HERE / "gen_deviations.py", PLATFORM_DOC)
    run(HERE / "gen_mineral_doc.py", PLATFORM_DOC)
    run(HERE / "gen_status_metrics.py", PLATFORM_DOC)

    print("== shared palette ==")
    run(ROOT / "shared" / "export_palette.py")
    run(ROOT / "shared" / "export_palette.py", "--check")
    run(ROOT / "shared" / "tools" / "check_palette.py")

    if not no_preview:
        print("== previews ==")
        run(HERE / "render_java.py")
        run(HERE / "render_ui.py")
        run(HERE / "render_diff_debug.py")

    print("== artifact checks ==")
    run(HERE / "check_palette_usage.py")
    if no_preview:
        run(HERE / "check_freshness.py", "--no-preview")
    else:
        run(HERE / "check_freshness.py")
    run(HERE / "gen_verification_report.py")

    print("Build complete.")
    return 0


def preview():
    if not require_pillow():
        return 1
    print("== previews ==")
    run(HERE / "render_java.py")
    run(HERE / "render_ui.py")
    run(HERE / "render_diff_debug.py")
    print("Previews complete.")
    return 0


def palette():
    """只导出并验收跨平台契约，不生成主题；给 VS Code 等新平台用。"""
    print("== shared palette ==")
    run(ROOT / "shared" / "export_palette.py")
    run(ROOT / "shared" / "export_palette.py", "--check")
    run(ROOT / "shared" / "tools" / "check_palette.py")
    return 0


def check():
    palette = ROOT / "shared" / "palette.json"
    if not palette.is_file():
        print("缺少 %s；先运行 build。" % palette.relative_to(ROOT),
              file=sys.stderr)
        return 1
    run(ROOT / "shared" / "export_palette.py", "--check")
    run(ROOT / "shared" / "tools" / "check_palette.py")
    return 0


def test():
    run_unittest("test_*.py")
    return 0


def clean():
    import shutil
    removed = 0
    for base in (HERE, ROOT / "shared", ROOT / "tests"):
        for cache in base.rglob("__pycache__"):
            shutil.rmtree(str(cache), ignore_errors=True)
            removed += 1
    for base in (HERE, ROOT / "shared", ROOT / "tests"):
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            if path.name.endswith(".pyc") or ".tmp." in path.name:
                path.unlink(missing_ok=True)
                removed += 1
    print("清理完成：%d 项。" % removed)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Green Eye 构建编排")
    ap.add_argument("--no-preview", action="store_true",
                    help="不生成预览图（不需要 Pillow）")
    ap.add_argument("--skip-tests", action="store_true",
                    help="跳过安装器集成测试")
    args = ap.parse_args(argv)
    return build(no_preview=args.no_preview, skip_tests=args.skip_tests)


if __name__ == "__main__":
    sys.exit(main())
