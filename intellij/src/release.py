#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
发布前全流程：bump → build → VS Code → CVD 变体 → package → test。

不会自动 git commit / tag / push；成功后会打印下一步命令，便于人工审查。
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
INTELLIJ = HERE.parent
ROOT = INTELLIJ.parent
sys.path.insert(0, str(HERE))

import build_pipeline  # noqa: E402
import cvd_variants  # noqa: E402
import gen_summary_report  # noqa: E402
import package_release  # noqa: E402
import versioning  # noqa: E402
import vscode_build  # noqa: E402


def _git_clean():
    result = subprocess.run(["git", "status", "--porcelain"],
                            cwd=str(ROOT), text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    return result.returncode == 0 and not result.stdout.strip()


def run(version, dry_run=False, skip_tests=False, allow_dirty=False):
    try:
        if versioning.current_version() == version:
            print("版本号已经是 %s，无需发布。" % version, file=sys.stderr)
            return 1
        versioning.bump(version, dry_run=True)
    except ValueError as exc:
        print("错误: %s" % exc, file=sys.stderr)
        return 1
    if not dry_run and not allow_dirty and not _git_clean():
        print("工作区不干净；先提交/清理，或加 --allow-dirty。", file=sys.stderr)
        return 1

    steps = [
        "bump 版本到 %s" % version,
        "build IntelliJ（含 29 项验收）",
        "build VS Code 主题 + VSIX",
        "build CVD 变体（A+）",
        "package IntelliJ zip",
        "package 合并 zip",
    ]
    if not skip_tests:
        steps.append("运行全部测试")
    if dry_run:
        print("发布演练：")
        for index, step in enumerate(steps, 1):
            print("  %d. %s" % (index, step))
        print("\n演练结束，未修改任何文件。")
        return 0

    rc = versioning.bump(version)
    if rc:
        return rc
    for label, func in [
        ("build", build_pipeline.build),
        ("vscode", vscode_build.build),
        ("cvd-variants", cvd_variants.build),
        ("package", package_release.package),
        ("package-all", package_release.package_all),
    ]:
        print("\n== release: %s ==" % label)
        rc = func()
        if rc:
            return rc
    if not skip_tests:
        print("\n== release: test ==")
        rc = build_pipeline.test()
        if rc:
            return rc

    print("\n== release: report ==")
    gen_summary_report.main([])
    print("\n发布产物已生成：")
    for label, path in [
        ("IntelliJ", ROOT / "release" / ("green-eye-%s.zip" % version)),
        ("合并包", ROOT / "release" / ("green-eye-%s-all.zip" % version)),
        ("CVD 变体", ROOT / "release" / ("green-eye-%s-cvd.zip" % version)),
        ("VS Code", ROOT / "vscode" / "dist"
         / ("green-eye-theme-%s.vsix" % version)),
        ("CVD VSIX", ROOT / "vscode" / "dist"
         / ("green-eye-cvd-variants-%s.vsix" % version)),
    ]:
        state = "%d 字节" % path.stat().st_size if path.is_file() else "缺失"
        print("  %-12s %s（%s）" % (label, path.name, state))
    print("\n下一步（人工确认后执行）：")
    print("  git add -A")
    print('  git commit -m "release: v%s"' % version)
    print("  git tag v%s" % version)
    print("  git push origin main --tags")
    return 0


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="发布前全流程")
    ap.add_argument("version")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--skip-tests", action="store_true")
    ap.add_argument("--allow-dirty", action="store_true")
    args = ap.parse_args()
    sys.exit(run(args.version, dry_run=args.dry_run,
                 skip_tests=args.skip_tests, allow_dirty=args.allow_dirty))
